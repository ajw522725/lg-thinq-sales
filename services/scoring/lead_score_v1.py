from __future__ import annotations

from typing import Any


PLATFORM_WEIGHT = {
    "Danawa": 6,
    "Reddit": 7,
    "Naver Blog": 8,
    "YouTube": 6,
    "X/Twitter": 8,
}


def calculate_lead_score(source: str, engagement: int, analysis: Any) -> tuple[int, str, dict[str, float | int]]:
    intent_points = analysis.purchase_intent_score * 46
    urgency_points = analysis.urgency_score * 26
    competitor_points = min(len(analysis.competitor_mentions) * 10, 14)
    sentiment_points = _sentiment_adjustment(analysis.sentiment, analysis.sentiment_score)
    platform_points = PLATFORM_WEIGHT.get(source, 5)
    engagement_points = min(engagement / 7, 14)
    context_points = _context_points(analysis.topic)
    intent_bonus = 12 if analysis.intent == "high" else 4 if analysis.intent == "medium" else 0
    urgency_bonus = 10 if analysis.urgency == "critical" else 6 if analysis.urgency == "medium" else 0

    score = round(
        intent_points
        + urgency_points
        + competitor_points
        + sentiment_points
        + platform_points
        + engagement_points
        + context_points
        + intent_bonus
        + urgency_bonus
    )
    score = max(0, min(100, score))

    if score >= 80:
        priority = "high"
    elif score >= 50:
        priority = "medium"
    else:
        priority = "low"

    reasons: dict[str, float | int] = {
        "intent_points": round(intent_points, 1),
        "urgency_points": round(urgency_points, 1),
        "competitor_points": competitor_points,
        "sentiment_points": round(sentiment_points, 1),
        "platform_points": platform_points,
        "engagement_points": round(engagement_points, 1),
        "context_points": context_points,
        "intent_bonus": intent_bonus,
        "urgency_bonus": urgency_bonus,
    }
    return score, priority, reasons


def _sentiment_adjustment(sentiment: str, sentiment_score: float) -> float:
    if sentiment == "positive":
        return sentiment_score * 12
    if sentiment == "negative":
        return 16
    return 7


def _context_points(topic: str) -> int:
    if topic in {"Air Quality Demand", "Energy Efficiency", "Subscription Pricing"}:
        return 14
    if topic in {"ThinQ Connectivity", "Maintenance Service", "Installation Issues"}:
        return 11
    return 6
