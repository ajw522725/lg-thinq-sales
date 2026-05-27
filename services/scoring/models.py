"""
Lead Scoring 전용 Pydantic 모델
TRD 9장 기준 — yuna0822
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ScoringFeatures(BaseModel):
    """NLP 결과 → Lead Score Feature Vector (TRD 9.2)"""
    voc_id: UUID

    # NLP 기반 Feature
    sentiment_score: float = Field(0.0, ge=0.0, le=1.0)
    purchase_intent_score: float = Field(0.0, ge=0.0, le=1.0)
    urgency_score: float = Field(0.0, ge=0.0, le=1.0)
    competitor_mention_count: int = Field(0, ge=0)
    competitor_comparison_flag: bool = False
    complaint_intensity: float = Field(0.0, ge=0.0, le=1.0)

    # 메타 기반 Feature
    product_category_weight: float = Field(0.5, ge=0.0, le=1.0)
    platform_weight: float = Field(0.5, ge=0.0, le=1.0)
    engagement_score: float = Field(0.0, ge=0.0, le=1.0)

    # 외부 데이터 Feature (Phase 5에서 채워짐)
    external_context_score: float = Field(0.0, ge=0.0, le=1.0)


class ScoreBreakdown(BaseModel):
    """점수 산출 근거 (score_reason jsonb)"""
    purchase_intent_contribution: float = 0.0
    urgency_contribution: float = 0.0
    competitor_contribution: float = 0.0
    product_weight_contribution: float = 0.0
    external_context_contribution: float = 0.0
    sentiment_adjustment: float = 0.0
    engagement_contribution: float = 0.0
    top_factors: list[str] = Field(default_factory=list)
    explanation: str = ""


class LeadScoreResult(BaseModel):
    """Lead Score 결과 — DB LeadScore 테이블과 매핑 (TRD 7.1)"""
    id: UUID = Field(default_factory=uuid4)
    voc_id: UUID

    lead_score: float = Field(ge=0.0, le=100.0)
    priority: Literal["high", "medium", "low"]
    score_reason: ScoreBreakdown
    model_version: str = "rule_based_v1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
