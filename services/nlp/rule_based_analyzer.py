from __future__ import annotations

from dataclasses import dataclass


POSITIVE_KEYWORDS = {
    "good",
    "excellent",
    "useful",
    "convenient",
    "love",
    "recommend",
    "satisfied",
    "편해",
    "만족",
    "추천",
    "좋",
}
NEGATIVE_KEYWORDS = {
    "expensive",
    "delayed",
    "frustrating",
    "annoying",
    "failed",
    "disappointing",
    "problem",
    "complaint",
    "too long",
    "높",
    "걱정",
    "불만",
}
BUYING_KEYWORDS = {
    "buy",
    "considering",
    "want",
    "quote",
    "discount",
    "bundle",
    "switch",
    "looking",
    "구매",
    "고민",
    "상담",
    "알아보고",
    "필요",
}
URGENCY_KEYWORDS = {
    "urgent",
    "critical",
    "before summer",
    "before the weekend",
    "next week",
    "three times",
    "심한",
    "바로",
}
COMPETITOR_KEYWORDS = {"samsung", "carrier", "dyson", "삼성", "캐리어", "다이슨"}
TOPIC_KEYWORDS = {
    "Subscription Pricing": {"subscription", "renewal", "monthly", "price", "discount", "구독", "가격", "할인"},
    "Installation Issues": {"installation", "delivery", "setup", "설치", "배송"},
    "ThinQ Connectivity": {"thinq", "app", "disconnect", "connectivity", "diagnosis", "연결"},
    "Energy Efficiency": {"energy", "electricity", "efficiency", "전기", "절감"},
    "Air Quality Demand": {"fine dust", "filter", "air purifier", "미세먼지", "필터", "공기청정기"},
    "Maintenance Service": {"maintenance", "repair", "support", "cleaning", "service", "케어", "관리"},
    "Competitor Comparison": COMPETITOR_KEYWORDS,
}


@dataclass(frozen=True)
class RuleBasedAnalysis:
    sentiment: str
    sentiment_score: float
    intent: str
    purchase_intent_score: float
    urgency: str
    urgency_score: float
    topic: str
    keywords: list[str]
    competitor_mentions: list[str]
    complaint_type: str | None
    confidence: float


def analyze_text(text: str) -> RuleBasedAnalysis:
    lower_text = text.lower()

    positive_hits = _count_hits(lower_text, POSITIVE_KEYWORDS)
    negative_hits = _count_hits(lower_text, NEGATIVE_KEYWORDS)
    buying_hits = _count_hits(lower_text, BUYING_KEYWORDS)
    urgency_hits = _count_hits(lower_text, URGENCY_KEYWORDS)
    competitors = sorted({keyword for keyword in COMPETITOR_KEYWORDS if keyword in lower_text})
    keywords = _extract_keywords(lower_text)
    topic = _detect_topic(lower_text)

    if negative_hits > positive_hits:
        sentiment = "negative"
        sentiment_score = max(0.1, 0.45 - negative_hits * 0.08)
    elif positive_hits > negative_hits:
        sentiment = "positive"
        sentiment_score = min(0.95, 0.62 + positive_hits * 0.08)
    else:
        sentiment = "neutral"
        sentiment_score = 0.5

    purchase_intent_score = min(1.0, (buying_hits * 0.22) + (0.12 if competitors else 0) + (0.08 if "subscription" in lower_text or "구독" in lower_text else 0))
    if purchase_intent_score >= 0.55:
        intent = "high"
    elif purchase_intent_score >= 0.25:
        intent = "medium"
    else:
        intent = "low"

    urgency_score = min(1.0, urgency_hits * 0.3 + (0.25 if sentiment == "negative" and negative_hits >= 2 else 0))
    if urgency_score >= 0.55:
        urgency = "critical"
    elif urgency_score >= 0.25:
        urgency = "medium"
    else:
        urgency = "low"

    complaint_type = _detect_complaint_type(lower_text, sentiment)
    confidence = min(0.95, 0.65 + (positive_hits + negative_hits + buying_hits + urgency_hits) * 0.03)

    return RuleBasedAnalysis(
        sentiment=sentiment,
        sentiment_score=round(sentiment_score, 2),
        intent=intent,
        purchase_intent_score=round(purchase_intent_score, 2),
        urgency=urgency,
        urgency_score=round(urgency_score, 2),
        topic=topic,
        keywords=keywords,
        competitor_mentions=competitors,
        complaint_type=complaint_type,
        confidence=round(confidence, 2),
    )


def _count_hits(text: str, keywords: set[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _extract_keywords(text: str) -> list[str]:
    candidates = [
        "ThinQ",
        "subscription care",
        "energy saving",
        "fine dust",
        "filter",
        "installation",
        "maintenance",
        "discount",
        "competitor",
        "구독",
        "미세먼지",
        "설치",
        "케어",
    ]
    return [keyword for keyword in candidates if keyword.lower() in text][:6]


def _detect_topic(text: str) -> str:
    best_topic = "General VOC"
    best_count = 0
    for topic, keywords in TOPIC_KEYWORDS.items():
        count = _count_hits(text, keywords)
        if count > best_count:
            best_topic = topic
            best_count = count
    return best_topic


def _detect_complaint_type(text: str, sentiment: str) -> str | None:
    if sentiment != "negative":
        return None
    if "price" in text or "expensive" in text or "가격" in text:
        return "pricing"
    if "installation" in text or "delivery" in text or "설치" in text:
        return "installation"
    if "app" in text or "disconnect" in text or "thinq" in text:
        return "connectivity"
    if "maintenance" in text or "repair" in text or "support" in text:
        return "maintenance"
    return "general"
