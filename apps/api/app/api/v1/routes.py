from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.dashboard_repository import build_dashboard_summary, build_voc_stats
from app.repositories.voc_repository import ingest_vocs, list_lead_score_records, list_strategy_insights, list_voc_records, seed_demo_data
from app.schemas.domain import DashboardSummary, IngestionVOC, SeedResponse, StrategyInsight, VocRecord

router = APIRouter(prefix=settings.api_prefix)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "demo" if settings.demo_mode else "production"}


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    return build_dashboard_summary(db)


@router.get("/vocs", response_model=list[VocRecord])
def list_vocs(db: Session = Depends(get_db)) -> list[VocRecord]:
    return list_voc_records(db)


@router.get("/vocs/stats")
def voc_stats(db: Session = Depends(get_db)) -> dict[str, object]:
    return build_voc_stats(db)


@router.get("/lead-scores", response_model=list[VocRecord])
def lead_scores(db: Session = Depends(get_db)) -> list[VocRecord]:
    return list_lead_score_records(db)


@router.get("/insights", response_model=list[StrategyInsight])
def insights(db: Session = Depends(get_db)) -> list[StrategyInsight]:
    return list_strategy_insights(db)


@router.post("/demo/seed", response_model=SeedResponse)
def seed_demo(reset: bool = False, db: Session = Depends(get_db)) -> SeedResponse:
    return seed_demo_data(db, reset=reset)


@router.post("/ingestion/vocs", response_model=SeedResponse)
def ingest_collector_vocs(vocs: list[IngestionVOC], reset: bool = False, db: Session = Depends(get_db)) -> SeedResponse:
    return ingest_vocs(db, vocs, reset=reset)
