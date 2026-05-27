import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    UUID, DateTime, Enum, Float, ForeignKey,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


# ── 1. Source ────────────────────────────────────────────────────────────────
# 데이터 원천 정보 (다나와, Reddit, 기상청 등 10개 소스)

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(
        Enum("review", "sns", "blog", "public", name="source_type"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", "error", name="source_status"),
        nullable=False,
        default="active",
    )
    last_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_documents: Mapped[list["RawDocument"]] = relationship(back_populates="source")

    def __repr__(self) -> str:
        return f"<Source name={self.name} type={self.type} status={self.status}>"


# ── 2. RawDocument ───────────────────────────────────────────────────────────
# 각 플랫폼에서 수집한 원문 데이터

class RawDocument(Base):
    __tablename__ = "raw_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # 플랫폼 고유 ID
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    author_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)    # SHA-256 익명화
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)       # "ko" | "en"
    product_keyword: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    platform_meta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)      # 플랫폼별 추가 필드

    source: Mapped["Source"] = relationship(back_populates="raw_documents")
    processed_voc: Mapped[Optional["ProcessedVOC"]] = relationship(back_populates="raw_document", uselist=False)

    def __repr__(self) -> str:
        return f"<RawDocument source_id={self.source_id} language={self.language}>"


# ── 3. ProcessedVOC ──────────────────────────────────────────────────────────
# 정제된 VOC 분석 단위

class ProcessedVOC(Base):
    __tablename__ = "processed_vocs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_documents.id"), nullable=False, unique=True)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    product_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    brand_mentions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    competitor_mentions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    keywords: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_document: Mapped["RawDocument"] = relationship(back_populates="processed_voc")
    nlp_analysis: Mapped[Optional["NLPAnalysis"]] = relationship(back_populates="voc", uselist=False)
    lead_score: Mapped[Optional["LeadScore"]] = relationship(back_populates="voc", uselist=False)
    strategy_insights: Mapped[list["StrategyInsight"]] = relationship(back_populates="voc")
    context_matches: Mapped[list["ContextMatch"]] = relationship(back_populates="voc")


# ── 4. NLPAnalysis ───────────────────────────────────────────────────────────
# VOC NLP 분석 결과 (감성, 구매의도, 긴급도, 토픽, 불만유형, 경쟁사)

class NLPAnalysis(Base):
    __tablename__ = "nlp_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processed_vocs.id"), nullable=False, unique=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(
        Enum("positive", "neutral", "negative", name="sentiment_label"),
        nullable=True,
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    purchase_intent_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0~1
    urgency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)           # 0~1
    complaint_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    topic_label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    voc: Mapped["ProcessedVOC"] = relationship(back_populates="nlp_analysis")


# ── 5. ExternalContext ───────────────────────────────────────────────────────
# 공공·외부 데이터 (기상청, AirKorea, 전기요금, 입주물량)

class ExternalContext(Base):
    __tablename__ = "external_contexts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    context_type: Mapped[str] = mapped_column(
        Enum("weather", "air_quality", "energy", "housing", name="context_type"),
        nullable=False,
    )
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)                         # 실제 측정값
    source_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # "KMA" | "AirKorea" 등
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    context_matches: Mapped[list["ContextMatch"]] = relationship(back_populates="external_context")


# ── 6. ContextMatch ──────────────────────────────────────────────────────────
# VOC ↔ 외부 데이터 매핑 결과

class ContextMatch(Base):
    __tablename__ = "context_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processed_vocs.id"), nullable=False)
    external_context_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("external_contexts.id"), nullable=False)
    match_reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    voc: Mapped["ProcessedVOC"] = relationship(back_populates="context_matches")
    external_context: Mapped["ExternalContext"] = relationship(back_populates="context_matches")


# ── 7. LeadScore ─────────────────────────────────────────────────────────────
# 리드 스코어 결과 (0~100, High/Medium/Low)

class LeadScore(Base):
    __tablename__ = "lead_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processed_vocs.id"), nullable=False, unique=True)
    lead_score: Mapped[float] = mapped_column(Float, nullable=False)                  # 0~100
    priority: Mapped[str] = mapped_column(
        Enum("high", "medium", "low", name="lead_priority"),
        nullable=False,
    )
    score_reason: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)        # feature별 기여도
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    voc: Mapped["ProcessedVOC"] = relationship(back_populates="lead_score")
    strategy_insights: Mapped[list["StrategyInsight"]] = relationship(back_populates="lead_score_rel")


# ── 8. StrategyInsight ───────────────────────────────────────────────────────
# LLM이 생성한 영업 전략 인사이트

class StrategyInsight(Base):
    __tablename__ = "strategy_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voc_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("processed_vocs.id"), nullable=False)
    lead_score_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("lead_scores.id"), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)        # "High" | "Medium" | "Low"
    target_segment: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")  # "completed" | "failed"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    voc: Mapped["ProcessedVOC"] = relationship(back_populates="strategy_insights")
    lead_score_rel: Mapped[Optional["LeadScore"]] = relationship(back_populates="strategy_insights")
