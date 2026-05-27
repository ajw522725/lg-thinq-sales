"""
감성분석 모듈
Phase 3에서 KoBERT / HuggingFace 모델로 교체 예정
현재: 키워드 기반 rule-based 구현 (골격 + 동작 가능)
"""
from __future__ import annotations

from .models import SentimentResult


# ──────────────────────────────────────────────
# 감성 키워드 사전
# ──────────────────────────────────────────────
POSITIVE_KW = {
    "ko": ["좋아", "좋다", "만족", "훌륭", "최고", "추천", "편리", "깔끔", "빠르다", "조용", "시원", "따뜻", "완벽", "대박"],
    "en": ["good", "great", "excellent", "love", "perfect", "amazing", "recommend", "satisfied", "quiet", "fast"],
}
NEGATIVE_KW = {
    "ko": ["불만", "실망", "최악", "별로", "고장", "냄새", "소음", "비싸", "느려", "답답", "불편", "짜증", "환불", "AS", "수리"],
    "en": ["bad", "terrible", "awful", "broken", "expensive", "slow", "noise", "disappointed", "issue", "problem", "worst"],
}


def analyze_sentiment(text: str, lang: str, rating: float | None = None) -> SentimentResult:
    """
    감성분석 수행

    Args:
        text: 전처리된 텍스트
        lang: "ko" | "en" | "other"
        rating: 플랫폼 평점 (1~5), 있으면 보정에 활용

    Returns:
        SentimentResult
    """
    pos_kw = POSITIVE_KW.get(lang, POSITIVE_KW["en"])
    neg_kw = NEGATIVE_KW.get(lang, NEGATIVE_KW["en"])

    text_lower = text.lower()
    pos_count = sum(1 for kw in pos_kw if kw in text_lower)
    neg_count = sum(1 for kw in neg_kw if kw in text_lower)

    # 기본 점수 계산
    total = pos_count + neg_count
    if total == 0:
        raw_score = 0.5
    else:
        raw_score = pos_count / total

    # 평점 보정 (있는 경우)
    if rating is not None:
        rating_score = (rating - 1) / 4       # 1~5 → 0~1
        raw_score = raw_score * 0.5 + rating_score * 0.5

    # 레이블 결정
    if raw_score >= 0.6:
        label = "positive"
        score = raw_score
    elif raw_score <= 0.4:
        label = "negative"
        score = 1.0 - raw_score
    else:
        label = "neutral"
        score = 0.5

    # 신뢰도: 키워드 매칭 수에 비례
    confidence = min(0.65 + total * 0.05, 0.95)

    return SentimentResult(
        label=label,
        score=round(score, 4),
        confidence=round(confidence, 4),
        model_used="rule_based_v1",
    )
