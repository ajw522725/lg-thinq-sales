"""
API 응답 스키마
서비스 내부 모델을 API 레이어에서 노출할 형태로 변환
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class NLPResponse(BaseModel):
    voc_id: str
    sentiment_label: str
    sentiment_score: float
    intent_label: str
    purchase_intent_score: float
    urgency_score: float
    complaint_type: str | None
    topic_id: str | None
    topic_label: str | None
    keywords: list[str]
    competitor_mentions: dict[str, int]
    competitor_comparison_flag: bool
    model_version: str


class ScoreResponse(BaseModel):
    lead_score: float
    priority: str
    score_reason: dict[str, Any]


class InsightResponse(BaseModel):
    title: str
    summary: str
    recommended_action: str
    reasoning: str
    confidence: float
    llm_model: str


class PipelineResponse(BaseModel):
    """POST /pipeline/run 응답 — NLP + Score + Insight 통합"""
    voc_id: str
    source: str
    product_category: str
    nlp: NLPResponse
    score: ScoreResponse
    insight: InsightResponse
    processing_time_ms: float
    demo_mode: bool


class DemoRunResponse(BaseModel):
    """GET /demo/run 응답"""
    total: int
    results: list[PipelineResponse]
