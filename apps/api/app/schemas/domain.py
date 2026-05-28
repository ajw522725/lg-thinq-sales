from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


SourceType = Literal["review", "sns", "blog", "public"]
SentimentLabel = Literal["positive", "neutral", "negative"]
IntentLabel = Literal["high", "medium", "low"]
UrgencyLabel = Literal["critical", "medium", "low"]
PriorityLabel = Literal["high", "medium", "low"]


class Source(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: SourceType
    status: Literal["active", "inactive", "error"] = "active"
    last_collected_at: Optional[datetime] = None


class RawDocument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    external_id: str
    title: str
    content: str
    url: str
    author_hash: str
    published_at: datetime
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    language: str = "unknown"
    product_category: str
    region: Optional[str] = None
    platform_meta: dict[str, Any] = Field(default_factory=dict)


class ProcessedDocument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    raw_document_id: UUID
    source: str
    title: str
    normalized_text: str
    product_category: str
    brand_mentions: list[str] = Field(default_factory=list)
    competitor_mentions: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    region: Optional[str] = None
    published_at: datetime
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NLPResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: UUID = Field(default_factory=uuid4)
    voc_id: UUID
    sentiment_label: SentimentLabel
    sentiment_score: float
    intent_label: IntentLabel
    purchase_intent_score: float
    urgency_label: UrgencyLabel
    urgency_score: float
    complaint_type: Optional[str] = None
    topic_id: str
    topic_label: str
    confidence: float
    model_version: str = "rule-based-v1"


class LeadScore(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: UUID = Field(default_factory=uuid4)
    voc_id: UUID
    lead_score: int
    priority: PriorityLabel
    score_reason: dict[str, Any]
    model_version: str = "lead-score-v1"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StrategyInsight(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    voc_id: UUID
    lead_score_id: UUID
    title: str
    summary: str
    recommended_action: str
    reasoning: str
    priority: PriorityLabel
    target_segment: str
    confidence: float
    llm_model: str = "demo-rule-generator"
    prompt_version: str = "demo-v1"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContextMatch(BaseModel):
    voc_id: UUID
    context_type: str
    region: str
    match_reason: str
    match_score: float
    context_summary: Optional[str] = None
    context_data: dict[str, Any] = Field(default_factory=dict)
    source_name: str = "demo-context"
    observed_at: Optional[datetime] = None


class VocRecord(BaseModel):
    voc: ProcessedDocument
    analysis: NLPResult
    lead_score: LeadScore
    insight: StrategyInsight
    context: ContextMatch


class DashboardSummary(BaseModel):
    total_voc_collected: int
    high_priority_leads: int
    negative_voc_rate: float
    purchase_intent_detected: int
    average_lead_score: float
    sentiment_breakdown: dict[str, int]
    urgency_breakdown: dict[str, int]
    platform_distribution: dict[str, int]
    top_keywords: list[str]
    topic_clusters: list[dict[str, Any]]
    high_priority_preview: list[VocRecord]
    featured_insight: Optional[StrategyInsight] = None


class SeedResponse(BaseModel):
    seeded: bool
    raw_documents: int
    processed_documents: int
    insights: int


class CollectionRunRequest(BaseModel):
    keywords: list[str] = Field(default_factory=lambda: ["LG air purifier"])
    sources: list[str] = Field(default_factory=lambda: ["Reddit"])
    max_per_source: int = 10
    live: bool = True
    reset: bool = False
    save: bool = False


class CollectionRunResponse(SeedResponse):
    mode: Literal["demo", "live"]
    keywords: list[str]
    sources: list[str]
    collector_raw: int
    ingestion_payload: int
    source_stats: dict[str, int]


class IngestionVOC(BaseModel):
    source: str
    external_id: str
    title: str
    content: str
    url: str
    published_at: datetime
    product_category: str
    region: Optional[str] = None
    engagement: int = 0
    author_hash: str = "collector_demo_author"
    rating: Optional[int] = None
