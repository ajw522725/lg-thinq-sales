"""
룰 기반 Lead Score 공식 구현
TRD 9.3 기준 — yuna0822

최종 구현에서는 XGBoost로 보정 예정 (Phase 4)
"""
from __future__ import annotations

from .models import ScoringFeatures, ScoreBreakdown, LeadScoreResult
from ..nlp.models import NLPAnalysisResult


def rule_based_score(features: ScoringFeatures) -> LeadScoreResult:
    """
    TRD 9.3 점수 공식 기반 Lead Score 산출

    Lead Score =
        purchase_intent_score * 35
      + urgency_score          * 15
      + competitor_comparison  * 10
      + product_category_weight* 10
      + external_context_score * 10
      + sentiment_adjustment   * 10
      + engagement_score       * 10
    """
    # ── 각 항목 기여도 계산 ──────────────────────
    intent_pts    = features.purchase_intent_score * 35
    urgency_pts   = features.urgency_score * 15
    competitor_pts = (10 if features.competitor_comparison_flag else
                      min(features.competitor_mention_count * 3, 10))
    product_pts   = features.product_category_weight * 10
    context_pts   = features.external_context_score * 10
    sentiment_pts = _sentiment_adjustment(features) * 10
    engagement_pts = features.engagement_score * 10

    raw_score = (
        intent_pts
        + urgency_pts
        + competitor_pts
        + product_pts
        + context_pts
        + sentiment_pts
        + engagement_pts
    )
    score = round(min(max(raw_score, 0.0), 100.0), 2)

    # ── 우선순위 분류 (TRD 9.4) ──────────────────
    priority = _classify_priority(score)

    # ── 점수 근거 생성 ────────────────────────────
    breakdown = _build_breakdown(
        features, intent_pts, urgency_pts, competitor_pts,
        product_pts, context_pts, sentiment_pts, engagement_pts, score,
    )

    return LeadScoreResult(
        voc_id=features.voc_id,
        lead_score=score,
        priority=priority,
        score_reason=breakdown,
    )


def _sentiment_adjustment(features: ScoringFeatures) -> float:
    """
    감성 점수 보정값 (0~1)
    - negative + high complaint: 보정 낮춤 (불만이 많으면 구매보다 이탈 리스크)
    - positive: 보정 높임
    """
    if features.complaint_intensity > 0.6:
        return max(0.0, features.sentiment_score - 0.3)
    return features.sentiment_score


def _classify_priority(score: float) -> str:
    """TRD 9.4 우선순위 분류"""
    if score >= 80:
        return "high"
    elif score >= 50:
        return "medium"
    return "low"


def _build_breakdown(
    features: ScoringFeatures,
    intent_pts: float,
    urgency_pts: float,
    competitor_pts: float,
    product_pts: float,
    context_pts: float,
    sentiment_pts: float,
    engagement_pts: float,
    score: float,
) -> ScoreBreakdown:
    """점수 산출 근거 생성"""
    # 기여도 순으로 top factor 정렬
    factor_map = {
        "구매의도": intent_pts,
        "긴급도": urgency_pts,
        "경쟁사 비교": competitor_pts,
        "제품군 중요도": product_pts,
        "외부 환경 연관": context_pts,
        "감성 보정": sentiment_pts,
        "참여도": engagement_pts,
    }
    top_factors = sorted(factor_map, key=lambda k: factor_map[k], reverse=True)[:3]

    explanation = (
        f"Lead Score {score}점: "
        + ", ".join(f"{f}({factor_map[f]:.1f}pt)" for f in top_factors)
    )

    return ScoreBreakdown(
        purchase_intent_contribution=round(intent_pts, 2),
        urgency_contribution=round(urgency_pts, 2),
        competitor_contribution=round(competitor_pts, 2),
        product_weight_contribution=round(product_pts, 2),
        external_context_contribution=round(context_pts, 2),
        sentiment_adjustment=round(sentiment_pts, 2),
        engagement_contribution=round(engagement_pts, 2),
        top_factors=top_factors,
        explanation=explanation,
    )
