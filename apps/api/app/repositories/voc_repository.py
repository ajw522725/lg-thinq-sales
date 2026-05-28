from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.db import models
from app.schemas.domain import (
    ContextMatch,
    IngestionVOC,
    LeadScore,
    NLPResult,
    ProcessedDocument,
    SeedResponse,
    Source,
    StrategyInsight,
    VocRecord,
)
from app.services.pipeline_service import build_voc_record, source_type_for_name
from services.collectors.demo_collector import load_demo_raw_documents


REPO_ROOT = Path(__file__).resolve().parents[4]
DEMO_DATA_PATH = REPO_ROOT / "data" / "demo" / "voc_records.json"


def seed_demo_data(db: Session, reset: bool = False) -> SeedResponse:
    raw_records = load_demo_raw_documents(DEMO_DATA_PATH)
    return ingest_voc_items(db, raw_records, reset=reset)


def ingest_vocs(db: Session, vocs: list[IngestionVOC], reset: bool = False) -> SeedResponse:
    raw_items = [voc.model_dump() for voc in vocs]
    return ingest_voc_items(db, raw_items, reset=reset)


def ingest_voc_items(db: Session, raw_items: list[dict[str, Any]], reset: bool = False) -> SeedResponse:
    if reset:
        _clear_pipeline_tables(db)

    raw_count = 0
    processed_count = 0
    insight_count = 0

    for item in raw_items:
        source = _get_or_create_source(db, str(item["source"]))
        existing = db.scalar(
            select(models.RawDocument).where(
                models.RawDocument.source_id == source.id,
                models.RawDocument.external_id == str(item["external_id"]),
            )
        )
        if existing:
            continue

        source_schema = Source(
            id=source.id,
            name=source.name,
            type=source.type,
            status=source.status,
            last_collected_at=source.last_collected_at,
        )
        raw_schema, voc_record = build_voc_record(item, source_schema)
        raw_model = models.RawDocument(
            id=str(raw_schema.id),
            source_id=source.id,
            external_id=raw_schema.external_id,
            title=raw_schema.title,
            content=raw_schema.content,
            url=raw_schema.url,
            author_hash=raw_schema.author_hash,
            published_at=raw_schema.published_at,
            collected_at=raw_schema.collected_at,
            language=raw_schema.language,
            product_category=raw_schema.product_category,
            region=raw_schema.region,
            platform_meta=raw_schema.platform_meta,
        )
        processed_model = models.ProcessedVOC(
            id=str(voc_record.voc.id),
            raw_document_id=str(raw_schema.id),
            normalized_text=voc_record.voc.normalized_text,
            product_category=voc_record.voc.product_category,
            brand_mentions=voc_record.voc.brand_mentions,
            competitor_mentions=voc_record.voc.competitor_mentions,
            keywords=voc_record.voc.keywords,
        )
        analysis_model = models.NLPAnalysis(
            id=str(voc_record.analysis.id),
            voc_id=str(voc_record.voc.id),
            sentiment_label=voc_record.analysis.sentiment_label,
            sentiment_score=voc_record.analysis.sentiment_score,
            intent_label=voc_record.analysis.intent_label,
            purchase_intent_score=voc_record.analysis.purchase_intent_score,
            urgency_label=voc_record.analysis.urgency_label,
            urgency_score=voc_record.analysis.urgency_score,
            complaint_type=voc_record.analysis.complaint_type,
            topic_id=voc_record.analysis.topic_id,
            topic_label=voc_record.analysis.topic_label,
            confidence=voc_record.analysis.confidence,
            model_version=voc_record.analysis.model_version,
        )
        lead_score_model = models.LeadScore(
            id=str(voc_record.lead_score.id),
            voc_id=str(voc_record.voc.id),
            lead_score=voc_record.lead_score.lead_score,
            priority=voc_record.lead_score.priority,
            score_reason=voc_record.lead_score.score_reason,
            model_version=voc_record.lead_score.model_version,
        )
        external_context_model = models.ExternalContext(
            context_type=voc_record.context.context_type,
            region=voc_record.context.region,
            data={
                "source": voc_record.context.source_name,
                "match_reason": voc_record.context.match_reason,
                "context_summary": voc_record.context.context_summary,
                **voc_record.context.context_data,
                "product_category": voc_record.voc.product_category,
            },
            observed_at=voc_record.context.observed_at,
            source_name=voc_record.context.source_name,
        )
        insight_model = models.StrategyInsight(
            id=str(voc_record.insight.id),
            voc_id=str(voc_record.voc.id),
            lead_score_id=str(voc_record.lead_score.id),
            title=voc_record.insight.title,
            summary=voc_record.insight.summary,
            recommended_action=voc_record.insight.recommended_action,
            reasoning=voc_record.insight.reasoning,
            priority=voc_record.insight.priority,
            target_segment=voc_record.insight.target_segment,
            confidence=voc_record.insight.confidence,
            llm_model=voc_record.insight.llm_model,
            prompt_version=voc_record.insight.prompt_version,
        )

        db.add(raw_model)
        db.add(processed_model)
        db.add(analysis_model)
        db.add(lead_score_model)
        db.add(external_context_model)
        db.flush()
        context_match_model = models.ContextMatch(
            voc_id=str(voc_record.voc.id),
            external_context_id=external_context_model.id,
            match_reason=voc_record.context.match_reason,
            match_score=voc_record.context.match_score,
        )
        db.add(context_match_model)
        db.add(insight_model)
        raw_count += 1
        processed_count += 1
        insight_count += 1

    db.commit()
    return SeedResponse(seeded=True, raw_documents=raw_count, processed_documents=processed_count, insights=insight_count)


def list_voc_records(db: Session) -> list[VocRecord]:
    processed_vocs = _query_processed_vocs(db).all()
    return [to_voc_record(voc) for voc in processed_vocs]


def list_lead_score_records(db: Session) -> list[VocRecord]:
    processed_vocs = db.scalars(
        select(models.ProcessedVOC)
        .join(models.ProcessedVOC.raw_document)
        .join(models.ProcessedVOC.lead_score)
        .options(
            joinedload(models.ProcessedVOC.raw_document).joinedload(models.RawDocument.source),
            joinedload(models.ProcessedVOC.nlp_analysis),
            joinedload(models.ProcessedVOC.lead_score),
            joinedload(models.ProcessedVOC.strategy_insights),
            joinedload(models.ProcessedVOC.context_matches).joinedload(models.ContextMatch.external_context),
        )
        .order_by(models.LeadScore.lead_score.desc(), models.RawDocument.published_at.desc())
    ).unique().all()
    return [to_voc_record(voc) for voc in processed_vocs]


def list_strategy_insights(db: Session) -> list[StrategyInsight]:
    insights = (
        db.scalars(
            select(models.StrategyInsight)
            .order_by(
                models.StrategyInsight.priority.asc(),
                models.StrategyInsight.confidence.desc(),
                models.StrategyInsight.created_at.desc(),
            )
        )
        .all()
    )
    return [_to_strategy_insight(insight) for insight in sorted(insights, key=_insight_sort_key)]


def to_voc_record(voc: models.ProcessedVOC) -> VocRecord:
    raw = voc.raw_document
    source = raw.source
    analysis = voc.nlp_analysis
    lead_score = voc.lead_score
    insight = _pick_primary_insight(voc.strategy_insights)
    context_match = _pick_primary_context(voc.context_matches)

    if not analysis or not lead_score or not insight or not context_match:
        raise ValueError(f"Incomplete VOC pipeline record: {voc.id}")

    processed_schema = ProcessedDocument(
        id=voc.id,
        raw_document_id=raw.id,
        source=source.name,
        title=raw.title,
        normalized_text=voc.normalized_text,
        product_category=voc.product_category,
        brand_mentions=voc.brand_mentions,
        competitor_mentions=voc.competitor_mentions,
        keywords=voc.keywords,
        region=raw.region,
        published_at=raw.published_at,
        url=raw.url,
        created_at=voc.created_at,
    )
    analysis_schema = NLPResult(
        id=analysis.id,
        voc_id=voc.id,
        sentiment_label=analysis.sentiment_label,
        sentiment_score=analysis.sentiment_score,
        intent_label=analysis.intent_label,
        purchase_intent_score=analysis.purchase_intent_score,
        urgency_label=analysis.urgency_label,
        urgency_score=analysis.urgency_score,
        complaint_type=analysis.complaint_type,
        topic_id=analysis.topic_id,
        topic_label=analysis.topic_label,
        confidence=analysis.confidence,
        model_version=analysis.model_version,
    )
    lead_score_schema = LeadScore(
        id=lead_score.id,
        voc_id=voc.id,
        lead_score=lead_score.lead_score,
        priority=lead_score.priority,
        score_reason=lead_score.score_reason,
        model_version=lead_score.model_version,
        created_at=lead_score.created_at,
    )
    insight_schema = _to_strategy_insight(insight)
    context_schema = ContextMatch(
        voc_id=voc.id,
        context_type=context_match.external_context.context_type,
        region=context_match.external_context.region,
        match_reason=context_match.match_reason,
        match_score=context_match.match_score,
        context_summary=context_match.external_context.data.get("context_summary"),
        context_data=context_match.external_context.data,
        source_name=context_match.external_context.source_name,
        observed_at=context_match.external_context.observed_at,
    )
    return VocRecord(voc=processed_schema, analysis=analysis_schema, lead_score=lead_score_schema, insight=insight_schema, context=context_schema)


def _query_processed_vocs(db: Session):
    return db.scalars(
        select(models.ProcessedVOC)
        .join(models.ProcessedVOC.raw_document)
        .options(
            joinedload(models.ProcessedVOC.raw_document).joinedload(models.RawDocument.source),
            joinedload(models.ProcessedVOC.nlp_analysis),
            joinedload(models.ProcessedVOC.lead_score),
            joinedload(models.ProcessedVOC.strategy_insights),
            joinedload(models.ProcessedVOC.context_matches).joinedload(models.ContextMatch.external_context),
        )
        .order_by(models.RawDocument.published_at.desc())
    ).unique()


def _get_or_create_source(db: Session, source_name: str) -> models.Source:
    source = db.scalar(select(models.Source).where(models.Source.name == source_name))
    if source:
        return source
    source = models.Source(name=source_name, type=source_type_for_name(source_name), status="active")
    db.add(source)
    db.flush()
    return source


def _clear_pipeline_tables(db: Session) -> None:
    for model in (
        models.StrategyInsight,
        models.ContextMatch,
        models.ExternalContext,
        models.LeadScore,
        models.NLPAnalysis,
        models.ProcessedVOC,
        models.RawDocument,
        models.Source,
    ):
        db.execute(delete(model))
    db.commit()


def _to_strategy_insight(insight: models.StrategyInsight) -> StrategyInsight:
    return StrategyInsight(
        id=insight.id,
        voc_id=insight.voc_id,
        lead_score_id=insight.lead_score_id,
        title=insight.title,
        summary=insight.summary,
        recommended_action=insight.recommended_action,
        reasoning=insight.reasoning,
        priority=insight.priority,
        target_segment=insight.target_segment,
        confidence=insight.confidence,
        llm_model=insight.llm_model,
        prompt_version=insight.prompt_version,
        created_at=insight.created_at,
    )


def _pick_primary_insight(insights: list[models.StrategyInsight]) -> models.StrategyInsight | None:
    if not insights:
        return None
    return sorted(insights, key=_insight_sort_key)[0]


def _pick_primary_context(matches: list[models.ContextMatch]) -> models.ContextMatch | None:
    if not matches:
        return None
    return sorted(matches, key=lambda match: match.match_score, reverse=True)[0]


def _insight_sort_key(insight: models.StrategyInsight) -> tuple[int, float, float]:
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return (
        priority_order.get(insight.priority, 3),
        -insight.confidence,
        -insight.created_at.timestamp(),
    )
