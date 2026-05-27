"""
긴급도 분석 모듈
긴급 표현, 느낌표 빈도, 부정 강도를 조합하여 긴급도 산출
"""
import re

from .models import UrgencyResult, SentimentResult


URGENT_EXPRESSIONS = {
    "ko": ["지금 당장", "빨리", "즉시", "긴급", "오늘 안에", "당장", "못 쓰겠다",
           "고장", "작동 안", "연락 안", "3일째", "일주일째", "AS 요청", "수리 요청"],
    "en": ["urgent", "immediately", "asap", "broken", "can't use", "not working",
           "days waiting", "emergency", "fix now", "critical"],
}


def analyze_urgency(text: str, lang: str, sentiment: SentimentResult | None = None) -> UrgencyResult:
    """
    긴급도 분석

    Args:
        text: 전처리된 텍스트
        lang: "ko" | "en"
        sentiment: 감성분석 결과 (있으면 보정에 활용)

    Returns:
        UrgencyResult
    """
    _lang = lang if lang in ("ko", "en") else "ko"
    text_lower = text.lower()

    urgent_kws = URGENT_EXPRESSIONS.get(_lang, URGENT_EXPRESSIONS["ko"])
    matched = [kw for kw in urgent_kws if kw in text_lower]

    # 느낌표 빈도 신호
    exclaim_count = len(re.findall(r"!", text))

    # 기본 점수
    score = min(len(matched) * 0.2, 0.8)

    # 느낌표 보정
    if exclaim_count >= 3:
        score = min(score + 0.15, 1.0)
    elif exclaim_count >= 1:
        score = min(score + 0.05, 1.0)

    # 부정 감성 보정
    if sentiment and sentiment.label == "negative":
        score = min(score + sentiment.score * 0.1, 1.0)

    # 레이블 결정
    if score >= 0.6:
        level = "high"
    elif score >= 0.3:
        level = "medium"
    else:
        level = "low"

    return UrgencyResult(
        urgency_score=round(score, 4),
        urgency_level=level,
        urgency_signals=matched,
    )
