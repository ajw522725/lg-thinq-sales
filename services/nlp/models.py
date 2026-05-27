"""
NLP 파이프라인 전용 Pydantic 모델 정의
입력/출력 타입을 명확히 정의하여 모듈 간 인터페이스 고정
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# 입력 모델
# ──────────────────────────────────────────────

class ProcessedVOCInput(BaseModel):
    """NLP 파이프라인의 입력 단위 (ProcessedVOC 테이블과 매핑)"""
    id: UUID = Field(default_factory=uuid4)
    raw_document_id: UUID
    normalized_text: str
    product_category: str
    product_keyword: str | None = None
    source: str                            # danawa, reddit, naver_blog, youtube, twitter
    platform: str                          # review, sns, blog
    language: str | None = None            # ko / en / other (없으면 자동 감지)
    published_at: datetime | None = None
    rating: float | None = None            # 1~5 평점 (있는 경우)
    platform_meta: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────
# 전처리 결과
# ──────────────────────────────────────────────

class PreprocessResult(BaseModel):
    original_text: str
    cleaned_text: str
    language: Literal["ko", "en", "other"]
    sentences: list[str] = Field(default_factory=list)
    tokens: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# 개별 분석 결과 모델
# ──────────────────────────────────────────────

class SentimentResult(BaseModel):
    label: Literal["positive", "neutral", "negative"]
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    model_used: str = "rule_based"


class IntentResult(BaseModel):
    purchase_intent_score: float = Field(ge=0.0, le=1.0)
    intent_label: Literal["high", "medium", "low"]
    matched_keywords: list[str] = Field(default_factory=list)


class ComplaintResult(BaseModel):
    complaint_type: str | None = None
    complaint_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_complaint: bool = False


class UrgencyResult(BaseModel):
    urgency_score: float = Field(ge=0.0, le=1.0)
    urgency_level: Literal["high", "medium", "low"]
    urgency_signals: list[str] = Field(default_factory=list)


class KeywordResult(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    product_keywords: list[str] = Field(default_factory=list)


class CompetitorResult(BaseModel):
    competitor_mentions: dict[str, int] = Field(default_factory=dict)
    competitor_comparison_flag: bool = False
    comparison_context: str | None = None
    total_mention_count: int = 0


class TopicResult(BaseModel):
    topic_id: str | None = None
    topic_label: str | None = None
    topic_keywords: list[str] = Field(default_factory=list)
    representative: bool = False


# ──────────────────────────────────────────────
# NLP 파이프라인 통합 결과 (NLPAnalysis 테이블과 매핑)
# ──────────────────────────────────────────────

class NLPAnalysisResult(BaseModel):
    """NLP 분석 전체 결과 — DB NLPAnalysis 테이블에 저장"""
    id: UUID = Field(default_factory=uuid4)
    voc_id: UUID

    # 감성
    sentiment_label: Literal["positive", "neutral", "negative"]
    sentiment_score: float
    confidence: float

    # 구매의도
    purchase_intent_score: float
    intent_label: Literal["high", "medium", "low"]

    # 긴급도
    urgency_score: float

    # 불만
    complaint_type: str | None = None

    # 토픽
    topic_id: str | None = None
    topic_label: str | None = None

    # 기타
    keywords: list[str] = Field(default_factory=list)
    competitor_mentions: dict[str, int] = Field(default_factory=dict)
    competitor_comparison_flag: bool = False

    model_version: str = "v1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ──────────────────────────────────────────────
# Demo 모드용 VOC 입력 (JSON 파일 기반)
# ──────────────────────────────────────────────

class DemoVOCItem(BaseModel):
    """data/demo/sample_voc.json 한 항목"""
    id: str
    source: str
    platform: str
    language: str | None = None
    product_category: str
    product_keyword: str | None = None
    title: str | None = None
    content: str
    rating: float | None = None
    published_at: str | None = None
    platform_meta: dict[str, Any] = Field(default_factory=dict)

    def to_processed_voc(self) -> ProcessedVOCInput:
        from uuid import uuid4
        return ProcessedVOCInput(
            id=uuid4(),
            raw_document_id=uuid4(),
            normalized_text=f"{self.title or ''} {self.content}".strip(),
            product_category=self.product_category,
            product_keyword=self.product_keyword,
            source=self.source,
            platform=self.platform,
            language=self.language,
            published_at=datetime.fromisoformat(self.published_at) if self.published_at else None,
            rating=self.rating,
            platform_meta=self.platform_meta,
        )
