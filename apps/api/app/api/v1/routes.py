from __future__ import annotations

from fastapi import APIRouter

from app.core.demo_store import demo_store
from app.schemas.domain import DashboardSummary, SeedResponse, StrategyInsight, VocRecord

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "demo"}


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary() -> DashboardSummary:
    return demo_store.dashboard_summary()


@router.get("/vocs", response_model=list[VocRecord])
def list_vocs() -> list[VocRecord]:
    demo_store.ensure_seeded()
    return demo_store.records


@router.get("/vocs/stats")
def voc_stats() -> dict[str, object]:
    return demo_store.voc_stats()


@router.get("/lead-scores", response_model=list[VocRecord])
def lead_scores() -> list[VocRecord]:
    demo_store.ensure_seeded()
    return sorted(demo_store.records, key=lambda record: record.lead_score.lead_score, reverse=True)


@router.get("/insights", response_model=list[StrategyInsight])
def insights() -> list[StrategyInsight]:
    demo_store.ensure_seeded()
    return [record.insight for record in sorted(demo_store.records, key=lambda item: item.lead_score.lead_score, reverse=True)]


@router.post("/demo/seed", response_model=SeedResponse)
def seed_demo() -> SeedResponse:
    return demo_store.seed()
