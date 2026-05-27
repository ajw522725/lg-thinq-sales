"""
외부 데이터 Context 결합 전용 Pydantic 모델
TRD 7.1 ExternalContext / ContextMatch 기준 — yuna0822
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExternalContextData(BaseModel):
    """공공·외부 데이터 한 건 (ExternalContext 테이블)"""
    id: UUID = Field(default_factory=uuid4)
    context_type: Literal["weather", "air_quality", "energy", "housing"]
    region: str
    observed_at: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    source_name: str


class ContextMatchResult(BaseModel):
    """VOC ↔ 외부 데이터 매핑 결과 (ContextMatch 테이블)"""
    id: UUID = Field(default_factory=uuid4)
    voc_id: UUID
    external_context_id: UUID
    match_reason: str
    match_score: float = Field(ge=0.0, le=1.0)
    context_type: str
    context_summary: str = ""


class ContextEnrichmentResult(BaseModel):
    """단일 VOC에 대한 Context 결합 최종 결과"""
    voc_id: UUID
    matches: list[ContextMatchResult] = Field(default_factory=list)
    aggregated_context_score: float = Field(0.0, ge=0.0, le=1.0)
    context_description: str = ""
