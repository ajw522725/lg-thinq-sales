"""
전략 인사이트 전용 Pydantic 모델
TRD 7.1 StrategyInsight 테이블 기준 — yuna0822
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StrategyInsight(BaseModel):
    """LLM이 생성한 단일 전략 인사이트 (StrategyInsight 테이블)"""
    id: UUID = Field(default_factory=uuid4)
    voc_id: UUID
    lead_score_id: UUID

    title: str
    summary: str
    recommended_action: str
    reasoning: str

    confidence: float = Field(ge=0.0, le=1.0)
    llm_model: str = "demo"
    prompt_version: str = "v1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InsightGenerationResult(BaseModel):
    """단일 VOC에 대한 인사이트 생성 최종 결과"""
    voc_id: UUID
    lead_score_id: UUID
    insight: StrategyInsight
    is_demo: bool = True
