from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import settings
from app.schemas.domain import (
    ContextMatch,
    LeadScore,
    NLPResult,
    ProcessedDocument,
    RawDocument,
    Source,
    StrategyInsight,
    VocRecord,
)
from services.context.demo_context_matcher import match_context
from services.insights.demo_insight_generator import generate_demo_insight
from services.nlp.rule_based_analyzer import analyze_text
from services.preprocessing.cleaner import clean_text
from services.scoring.lead_score_v1 import calculate_lead_score


def build_voc_record(item: dict[str, Any], source: Source) -> tuple[RawDocument, VocRecord]:
    published_at = _parse_datetime(item["published_at"])
    content = str(item["content"])
    engagement = int(item.get("engagement", 0) or 0)
    rating = item.get("rating")

    raw_document = RawDocument(
        source_id=source.id,
        external_id=str(item["external_id"]),
        title=str(item["title"]),
        content=content,
        url=str(item.get("url") or ""),
        author_hash=str(item.get("author_hash") or "collector_demo_author"),
        published_at=published_at,
        language="ko" if _contains_korean(content) else "en",
        product_category=str(item["product_category"]),
        region=item.get("region"),
        platform_meta={"rating": rating, "engagement": engagement},
    )

    normalized_text = clean_text(raw_document.content)
    if settings.db_pipeline_provider.lower() == "yuna":
        return raw_document, _build_yuna_voc_record(raw_document, source, normalized_text, engagement, rating)

    return raw_document, _build_legacy_voc_record(raw_document, source, normalized_text, engagement)


def _build_legacy_voc_record(
    raw_document: RawDocument,
    source: Source,
    normalized_text: str,
    engagement: int,
) -> VocRecord:
    analysis_result = analyze_text(normalized_text)
    processed = ProcessedDocument(
        raw_document_id=raw_document.id,
        source=source.name,
        title=raw_document.title,
        normalized_text=normalized_text,
        product_category=raw_document.product_category,
        brand_mentions=["LG"],
        competitor_mentions=analysis_result.competitor_mentions,
        keywords=analysis_result.keywords,
        region=raw_document.region,
        published_at=raw_document.published_at,
        url=raw_document.url,
    )
    analysis = NLPResult(
        voc_id=processed.id,
        sentiment_label=analysis_result.sentiment,
        sentiment_score=analysis_result.sentiment_score,
        intent_label=analysis_result.intent,
        purchase_intent_score=analysis_result.purchase_intent_score,
        urgency_label=analysis_result.urgency,
        urgency_score=analysis_result.urgency_score,
        complaint_type=analysis_result.complaint_type,
        topic_id=analysis_result.topic.lower().replace(" ", "_"),
        topic_label=analysis_result.topic,
        confidence=analysis_result.confidence,
    )
    score, priority, reasons = calculate_lead_score(
        source=source.name,
        engagement=engagement,
        analysis=analysis_result,
    )
    lead_score = LeadScore(
        voc_id=processed.id,
        lead_score=score,
        priority=priority,
        score_reason=reasons,
    )
    insight_payload = generate_demo_insight(processed, analysis_result, lead_score)
    insight = StrategyInsight(
        voc_id=processed.id,
        lead_score_id=lead_score.id,
        **insight_payload,
    )
    context_payload = match_context(
        processed.product_category,
        processed.normalized_text,
        processed.region,
        observed_at=raw_document.published_at,
    )
    context = ContextMatch(voc_id=processed.id, **context_payload)
    return VocRecord(voc=processed, analysis=analysis, lead_score=lead_score, insight=insight, context=context)


def _build_yuna_voc_record(
    raw_document: RawDocument,
    source: Source,
    normalized_text: str,
    engagement: int,
    rating: Any,
) -> VocRecord:
    from services.insights.pipeline import generate_insight
    from services.context.matcher import fetch_and_match
    from services.nlp.models import ProcessedVOCInput
    from services.nlp.pipeline import run_nlp_pipeline
    from services.scoring.pipeline import run_lead_scoring

    processed = ProcessedDocument(
        raw_document_id=raw_document.id,
        source=source.name,
        title=raw_document.title,
        normalized_text=normalized_text,
        product_category=raw_document.product_category,
        brand_mentions=["LG"],
        region=raw_document.region,
        published_at=raw_document.published_at,
        url=raw_document.url,
    )
    yuna_input = ProcessedVOCInput(
        id=processed.id,
        raw_document_id=raw_document.id,
        normalized_text=processed.normalized_text,
        product_category=processed.product_category,
        source=source.name,
        platform=source.type,
        language=raw_document.language,
        published_at=raw_document.published_at,
        rating=rating,
        platform_meta={**raw_document.platform_meta, "engagement": engagement},
    )
    yuna_nlp = run_nlp_pipeline(yuna_input)
    context_enrichment = fetch_and_match(yuna_input)
    yuna_score = run_lead_scoring(
        yuna_nlp,
        yuna_input,
        external_context_score=context_enrichment.aggregated_context_score,
    )
    yuna_insight = generate_insight(yuna_nlp, yuna_input, yuna_score, context=context_enrichment).insight

    competitor_mentions = [
        name for name, count in yuna_nlp.competitor_mentions.items() if int(count or 0) > 0
    ]
    processed.competitor_mentions = competitor_mentions
    processed.keywords = yuna_nlp.keywords

    analysis = NLPResult(
        id=yuna_nlp.id,
        voc_id=processed.id,
        sentiment_label=yuna_nlp.sentiment_label,
        sentiment_score=yuna_nlp.sentiment_score,
        intent_label=yuna_nlp.intent_label,
        purchase_intent_score=yuna_nlp.purchase_intent_score,
        urgency_label=_map_yuna_urgency(yuna_nlp.urgency_score),
        urgency_score=yuna_nlp.urgency_score,
        complaint_type=yuna_nlp.complaint_type,
        topic_id=yuna_nlp.topic_id or "general",
        topic_label=yuna_nlp.topic_label or "General",
        confidence=yuna_nlp.confidence,
        model_version=yuna_nlp.model_version,
    )
    lead_score = LeadScore(
        id=yuna_score.id,
        voc_id=processed.id,
        lead_score=int(round(yuna_score.lead_score)),
        priority=yuna_score.priority,
        score_reason=yuna_score.score_reason.model_dump(),
        model_version=yuna_score.model_version,
        created_at=yuna_score.created_at,
    )
    insight = StrategyInsight(
        id=yuna_insight.id,
        voc_id=processed.id,
        lead_score_id=lead_score.id,
        title=yuna_insight.title,
        summary=yuna_insight.summary,
        recommended_action=yuna_insight.recommended_action,
        reasoning=yuna_insight.reasoning,
        priority=lead_score.priority,
        target_segment=processed.product_category,
        confidence=yuna_insight.confidence,
        llm_model=yuna_insight.llm_model,
        prompt_version=yuna_insight.prompt_version,
        created_at=yuna_insight.created_at,
    )
    context_payload = match_context(
        processed.product_category,
        processed.normalized_text,
        processed.region,
        observed_at=raw_document.published_at,
    )
    context = ContextMatch(voc_id=processed.id, **context_payload)
    return VocRecord(voc=processed, analysis=analysis, lead_score=lead_score, insight=insight, context=context)


def _map_yuna_urgency(urgency_score: float) -> str:
    if urgency_score >= 0.7:
        return "critical"
    if urgency_score >= 0.35:
        return "medium"
    return "low"


def source_type_for_name(name: str) -> str:
    if name in {"Naver Blog", "NaverBlog"}:
        return "blog"
    if name in {"Reddit", "YouTube", "X/Twitter", "Twitter"}:
        return "sns"
    return "review"


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _contains_korean(text: str) -> bool:
    return any("가" <= char <= "힣" for char in text)
