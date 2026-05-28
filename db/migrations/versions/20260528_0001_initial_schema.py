"""initial_schema

Revision ID: 20260528_0001
Revises:
Create Date: 2026-05-28 12:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260528_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sources_name"), "sources", ["name"], unique=True)

    op.create_table(
        "raw_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("author_hash", sa.String(length=255), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("product_category", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("platform_meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_raw_documents_source_external"),
    )

    op.create_table(
        "external_contexts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("context_type", sa.String(length=50), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "processed_vocs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("raw_document_id", sa.String(length=36), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("product_category", sa.String(length=100), nullable=False),
        sa.Column("brand_mentions", sa.JSON(), nullable=False),
        sa.Column("competitor_mentions", sa.JSON(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("raw_document_id"),
    )

    op.create_table(
        "nlp_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("voc_id", sa.String(length=36), nullable=False),
        sa.Column("sentiment_label", sa.String(length=30), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("intent_label", sa.String(length=30), nullable=False),
        sa.Column("purchase_intent_score", sa.Float(), nullable=False),
        sa.Column("urgency_label", sa.String(length=30), nullable=False),
        sa.Column("urgency_score", sa.Float(), nullable=False),
        sa.Column("complaint_type", sa.String(length=100), nullable=True),
        sa.Column("topic_id", sa.String(length=100), nullable=False),
        sa.Column("topic_label", sa.String(length=150), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["voc_id"], ["processed_vocs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voc_id"),
    )

    op.create_table(
        "lead_scores",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("voc_id", sa.String(length=36), nullable=False),
        sa.Column("lead_score", sa.Integer(), nullable=False),
        sa.Column("priority", sa.String(length=30), nullable=False),
        sa.Column("score_reason", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["voc_id"], ["processed_vocs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voc_id"),
    )

    op.create_table(
        "context_matches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("voc_id", sa.String(length=36), nullable=False),
        sa.Column("external_context_id", sa.String(length=36), nullable=False),
        sa.Column("match_reason", sa.String(length=255), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["external_context_id"], ["external_contexts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voc_id"], ["processed_vocs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "strategy_insights",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("voc_id", sa.String(length=36), nullable=False),
        sa.Column("lead_score_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=30), nullable=False),
        sa.Column("target_segment", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("llm_model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["lead_score_id"], ["lead_scores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voc_id"], ["processed_vocs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("strategy_insights")
    op.drop_table("context_matches")
    op.drop_table("lead_scores")
    op.drop_table("nlp_analyses")
    op.drop_table("processed_vocs")
    op.drop_table("external_contexts")
    op.drop_table("raw_documents")
    op.drop_index(op.f("ix_sources_name"), table_name="sources")
    op.drop_table("sources")
