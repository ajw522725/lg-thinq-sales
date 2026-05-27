"""
Feature Engineering — NLP 결과를 Lead Score Feature Vector로 변환
TRD 9.2 기준 — yuna0822
"""
from __future__ import annotations

from ..nlp.models import NLPAnalysisResult, ProcessedVOCInput
from .models import ScoringFeatures


# ──────────────────────────────────────────────
# 플랫폼 신뢰도 가중치 (TRD 기준)
# ──────────────────────────────────────────────
PLATFORM_WEIGHTS: dict[str, float] = {
    "danawa":     0.85,
    "enuri":      0.80,
    "naver_blog": 0.75,
    "reddit":     0.70,
    "youtube":    0.65,
    "twitter":    0.55,
}

# ──────────────────────────────────────────────
# 제품군 가중치 (전략적 중요도 반영)
# ──────────────────────────────────────────────
PRODUCT_CATEGORY_WEIGHTS: dict[str, float] = {
    "air_conditioner": 0.90,
    "air_purifier":    0.85,
    "refrigerator":    0.80,
    "washing_machine": 0.75,
    "dehumidifier":    0.70,
}


def build_feature_vector(
    nlp: NLPAnalysisResult,
    voc: ProcessedVOCInput,
    external_context_score: float = 0.0,
) -> ScoringFeatures:
    """
    NLP 분석 결과 + VOC 메타데이터 → Feature Vector 변환

    Args:
        nlp: NLP 분석 결과
        voc: 원본 VOC 입력 (플랫폼, 제품군 등 메타 포함)
        external_context_score: 외부 데이터 연관 점수 (Phase 5에서 채워짐, 기본 0.0)

    Returns:
        ScoringFeatures
    """
    # 플랫폼 가중치
    platform_w = PLATFORM_WEIGHTS.get(voc.source, 0.60)

    # 제품군 가중치
    product_w = PRODUCT_CATEGORY_WEIGHTS.get(voc.product_category, 0.70)

    # 불만 강도: 불만 유형이 있고 감성이 부정적일수록 높음
    complaint_intensity = 0.0
    if nlp.complaint_type and nlp.sentiment_label == "negative":
        complaint_intensity = nlp.sentiment_score * 0.8

    # 참여도(engagement) 점수: platform_meta에서 추출
    engagement = _calc_engagement_score(voc)

    return ScoringFeatures(
        voc_id=nlp.voc_id,
        sentiment_score=nlp.sentiment_score,
        purchase_intent_score=nlp.purchase_intent_score,
        urgency_score=nlp.urgency_score,
        competitor_mention_count=sum(nlp.competitor_mentions.values()),
        competitor_comparison_flag=nlp.competitor_comparison_flag,
        complaint_intensity=complaint_intensity,
        product_category_weight=product_w,
        platform_weight=platform_w,
        engagement_score=engagement,
        external_context_score=external_context_score,
    )


def _calc_engagement_score(voc: ProcessedVOCInput) -> float:
    """
    플랫폼별 참여 지표(helpful, upvotes, likes 등)를 0~1 점수로 정규화
    """
    meta = voc.platform_meta
    if not meta:
        return 0.0

    # 플랫폼별 주요 참여 지표 추출
    value = (
        meta.get("helpful_count", 0)
        or meta.get("upvotes", 0)
        or meta.get("likes", 0)
        or meta.get("view_count", 0) // 100  # view는 100으로 나눠서 normalize
    )
    # 로그 스케일로 0~1 정규화 (최대 참조값: 100)
    import math
    return round(min(math.log1p(value) / math.log1p(100), 1.0), 4)
