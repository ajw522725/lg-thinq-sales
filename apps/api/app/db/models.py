from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    last_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_documents: Mapped[List["RawDocument"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class RawDocument(Base, TimestampMixin):
    __tablename__ = "raw_documents"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_raw_documents_source_external"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    author_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    product_category: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    platform_meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    source: Mapped[Source] = relationship(back_populates="raw_documents")
    processed_voc: Mapped[Optional["ProcessedVOC"]] = relationship(back_populates="raw_document", cascade="all, delete-orphan")


class ProcessedVOC(Base, TimestampMixin):
    __tablename__ = "processed_vocs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    raw_document_id: Mapped[str] = mapped_column(ForeignKey("raw_documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    product_category: Mapped[str] = mapped_column(String(100), nullable=False)
    brand_mentions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    competitor_mentions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    raw_document: Mapped[RawDocument] = relationship(back_populates="processed_voc")
    nlp_analysis: Mapped[Optional["NLPAnalysis"]] = relationship(back_populates="voc", cascade="all, delete-orphan")
    lead_score: Mapped[Optional["LeadScore"]] = relationship(back_populates="voc", cascade="all, delete-orphan")
    context_matches: Mapped[List["ContextMatch"]] = relationship(back_populates="voc", cascade="all, delete-orphan")
    strategy_insights: Mapped[List["StrategyInsight"]] = relationship(back_populates="voc", cascade="all, delete-orphan")


class NLPAnalysis(Base, TimestampMixin):
    __tablename__ = "nlp_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    voc_id: Mapped[str] = mapped_column(ForeignKey("processed_vocs.id", ondelete="CASCADE"), unique=True, nullable=False)
    sentiment_label: Mapped[str] = mapped_column(String(30), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    intent_label: Mapped[str] = mapped_column(String(30), nullable=False)
    purchase_intent_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency_label: Mapped[str] = mapped_column(String(30), nullable=False)
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False)
    complaint_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic_id: Mapped[str] = mapped_column(String(100), nullable=False)
    topic_label: Mapped[str] = mapped_column(String(150), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), default="rule-based-v1", nullable=False)

    voc: Mapped[ProcessedVOC] = relationship(back_populates="nlp_analysis")


class LeadScore(Base, TimestampMixin):
    __tablename__ = "lead_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    voc_id: Mapped[str] = mapped_column(ForeignKey("processed_vocs.id", ondelete="CASCADE"), unique=True, nullable=False)
    lead_score: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), nullable=False)
    score_reason: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), default="lead-score-v1", nullable=False)

    voc: Mapped[ProcessedVOC] = relationship(back_populates="lead_score")
    strategy_insights: Mapped[List["StrategyInsight"]] = relationship(back_populates="lead_score", cascade="all, delete-orphan")


class ExternalContext(Base, TimestampMixin):
    __tablename__ = "external_contexts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), default="demo-context", nullable=False)

    context_matches: Mapped[List["ContextMatch"]] = relationship(back_populates="external_context", cascade="all, delete-orphan")


class ContextMatch(Base, TimestampMixin):
    __tablename__ = "context_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    voc_id: Mapped[str] = mapped_column(ForeignKey("processed_vocs.id", ondelete="CASCADE"), nullable=False)
    external_context_id: Mapped[str] = mapped_column(ForeignKey("external_contexts.id", ondelete="CASCADE"), nullable=False)
    match_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)

    voc: Mapped[ProcessedVOC] = relationship(back_populates="context_matches")
    external_context: Mapped[ExternalContext] = relationship(back_populates="context_matches")


class StrategyInsight(Base, TimestampMixin):
    __tablename__ = "strategy_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    voc_id: Mapped[str] = mapped_column(ForeignKey("processed_vocs.id", ondelete="CASCADE"), nullable=False)
    lead_score_id: Mapped[str] = mapped_column(ForeignKey("lead_scores.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), nullable=False)
    target_segment: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), default="demo-rule-generator", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), default="demo-v1", nullable=False)

    voc: Mapped[ProcessedVOC] = relationship(back_populates="strategy_insights")
    lead_score: Mapped[LeadScore] = relationship(back_populates="strategy_insights")
