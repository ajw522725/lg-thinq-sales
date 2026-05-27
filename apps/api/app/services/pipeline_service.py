from __future__ import annotations

from datetime import datetime
from typing import Any

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
    context_payload = match_context(processed.product_category, processed.normalized_text, processed.region)
    context = ContextMatch(voc_id=processed.id, **context_payload)
    return raw_document, VocRecord(voc=processed, analysis=analysis, lead_score=lead_score, insight=insight, context=context)


def source_type_for_name(name: str) -> str:
    if name == "Naver Blog":
        return "blog"
    if name in {"Reddit", "YouTube", "X/Twitter"}:
        return "sns"
    return "review"


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _contains_korean(text: str) -> bool:
    return any("가" <= char <= "힣" for char in text)
