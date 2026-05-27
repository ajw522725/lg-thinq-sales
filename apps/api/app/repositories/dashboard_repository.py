from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.domain import DashboardSummary
from app.repositories.voc_repository import list_voc_records


def build_dashboard_summary(db: Session) -> DashboardSummary:
    records = list_voc_records(db)
    total = len(records)
    sentiment_counter = Counter(record.analysis.sentiment_label for record in records)
    urgency_counter = Counter(record.analysis.urgency_label for record in records)
    platform_counter = Counter(record.voc.source for record in records)
    keyword_counter = Counter(keyword for record in records for keyword in record.voc.keywords)
    topic_counter = Counter(record.analysis.topic_label for record in records)
    high_priority = [record for record in records if record.lead_score.priority == "high"]
    purchase_intent = [record for record in records if record.analysis.intent_label in {"high", "medium"}]
    average_score = sum(record.lead_score.lead_score for record in records) / total if total else 0
    sorted_high_priority = sorted(high_priority, key=lambda record: record.lead_score.lead_score, reverse=True)
    featured_insight = _pick_featured_insight(records)

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
        high_priority_preview=sorted_high_priority[:5],
        featured_insight=featured_insight,
    )


def build_voc_stats(db: Session) -> dict[str, Any]:
    summary = build_dashboard_summary(db)
    return {
        "sentiment_breakdown": summary.sentiment_breakdown,
        "urgency_breakdown": summary.urgency_breakdown,
        "topic_clusters": summary.topic_clusters,
        "top_keywords": summary.top_keywords,
        "platform_distribution": summary.platform_distribution,
    }


def _pick_featured_insight(records):
    if not records:
        return None
    return max(records, key=lambda record: record.lead_score.lead_score).insight


def _topic_status(topic: str, count: int) -> str:
    if topic in {"ThinQ Connectivity", "Installation Issues", "Maintenance Service"}:
        return "critical"
    if topic in {"Air Quality Demand", "Energy Efficiency"}:
        return "opportunity"
    if count >= 4:
        return "watch"
    return "normal"
