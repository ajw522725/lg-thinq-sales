from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.schemas.domain import (
    ContextMatch,
    DashboardSummary,
    LeadScore,
    NLPResult,
    ProcessedDocument,
    RawDocument,
    SeedResponse,
    Source,
    StrategyInsight,
    VocRecord,
)
from services.collectors.demo_collector import load_demo_raw_documents
from services.context.demo_context_matcher import match_context
from services.insights.demo_insight_generator import generate_demo_insight
from services.nlp.rule_based_analyzer import analyze_text
from services.preprocessing.cleaner import clean_text
from services.scoring.lead_score_v1 import calculate_lead_score


REPO_ROOT = Path(__file__).resolve().parents[4]
DEMO_DATA_PATH = REPO_ROOT / "data" / "demo" / "voc_records.json"


class DemoStore:
    def __init__(self) -> None:
        self.sources: list[Source] = []
        self.raw_documents: list[RawDocument] = []
        self.records: list[VocRecord] = []

    def seed(self) -> SeedResponse:
        raw_records = load_demo_raw_documents(DEMO_DATA_PATH)
        source_map = self._build_sources(raw_records)

        raw_documents: list[RawDocument] = []
        records: list[VocRecord] = []

        for item in raw_records:
            source = source_map[item["source"]]
            raw_document = RawDocument(
                source_id=source.id,
                external_id=item["external_id"],
                title=item["title"],
                content=item["content"],
                url=item["url"],
                author_hash=item["author_hash"],
                published_at=datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")),
                language="ko" if _contains_korean(item["content"]) else "en",
                product_category=item["product_category"],
                region=item.get("region"),
                platform_meta={"rating": item.get("rating"), "engagement": item.get("engagement", 0)},
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
                engagement=int(item.get("engagement", 0) or 0),
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

            raw_documents.append(raw_document)
            records.append(VocRecord(voc=processed, analysis=analysis, lead_score=lead_score, insight=insight, context=context))

        self.raw_documents = raw_documents
        self.records = sorted(records, key=lambda record: record.voc.published_at, reverse=True)
        return SeedResponse(seeded=True, raw_documents=len(self.raw_documents), processed_documents=len(self.records), insights=len(self.records))

    def ensure_seeded(self) -> None:
        if not self.records:
            self.seed()

    def dashboard_summary(self) -> DashboardSummary:
        self.ensure_seeded()
        total = len(self.records)
        sentiment_counter = Counter(record.analysis.sentiment_label for record in self.records)
        urgency_counter = Counter(record.analysis.urgency_label for record in self.records)
        platform_counter = Counter(record.voc.source for record in self.records)
        keyword_counter = Counter(keyword for record in self.records for keyword in record.voc.keywords)
        topic_counter = Counter(record.analysis.topic_label for record in self.records)
        high_priority = [record for record in self.records if record.lead_score.priority == "high"]
        purchase_intent = [record for record in self.records if record.analysis.intent_label in {"high", "medium"}]
        average_score = sum(record.lead_score.lead_score for record in self.records) / total if total else 0
        featured = max(self.records, key=lambda record: record.lead_score.lead_score).insight if self.records else None

        return DashboardSummary(
            total_voc_collected=total,
            high_priority_leads=len(high_priority),
            negative_voc_rate=round((sentiment_counter["negative"] / total) * 100, 1) if total else 0,
            purchase_intent_detected=len(purchase_intent),
            average_lead_score=round(average_score, 1),
            sentiment_breakdown=dict(sentiment_counter),
            urgency_breakdown=dict(urgency_counter),
            platform_distribution=dict(platform_counter),
            top_keywords=[keyword for keyword, _ in keyword_counter.most_common(8)],
            topic_clusters=[
                {"topic": topic, "count": count, "status": _topic_status(topic, count)}
                for topic, count in topic_counter.most_common()
            ],
            high_priority_preview=sorted(high_priority, key=lambda record: record.lead_score.lead_score, reverse=True)[:5],
            featured_insight=featured,
        )

    def voc_stats(self) -> dict[str, object]:
        summary = self.dashboard_summary()
        return {
            "sentiment_breakdown": summary.sentiment_breakdown,
            "urgency_breakdown": summary.urgency_breakdown,
            "topic_clusters": summary.topic_clusters,
            "top_keywords": summary.top_keywords,
            "platform_distribution": summary.platform_distribution,
        }

    def _build_sources(self, raw_records: list[dict[str, object]]) -> dict[str, Source]:
        source_map: dict[str, Source] = {}
        for item in raw_records:
            name = str(item["source"])
            if name in source_map:
                continue
            source_map[name] = Source(
                id=uuid4(),
                name=name,
                type=_source_type(name),
                last_collected_at=datetime.utcnow(),
            )
        self.sources = list(source_map.values())
        return source_map


def _source_type(name: str) -> str:
    if name == "Naver Blog":
        return "blog"
    if name in {"Reddit", "YouTube", "X/Twitter"}:
        return "sns"
    return "review"


def _contains_korean(text: str) -> bool:
    return any("가" <= char <= "힣" for char in text)


def _topic_status(topic: str, count: int) -> str:
    if topic in {"ThinQ Connectivity", "Installation Issues", "Maintenance Service"}:
        return "critical"
    if topic in {"Air Quality Demand", "Energy Efficiency"}:
        return "opportunity"
    if count >= 4:
        return "watch"
    return "normal"


demo_store = DemoStore()
