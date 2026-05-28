"""스케줄러 상태 조회 및 수동 트리거 API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

scheduler_router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])

_JOB_REGISTRY: dict[str, Any] = {}


def _get_registry() -> dict[str, Any]:
    from services.scheduler.jobs import (
        job_collect_voc,
        job_ingest_to_db,
        job_run_nlp,
        job_run_lead_scoring,
        job_generate_insights,
        job_full_pipeline,
    )
    return {
        "collect_voc":       job_collect_voc,
        "ingest_to_db":      job_ingest_to_db,
        "run_nlp":           job_run_nlp,
        "lead_scoring":      job_run_lead_scoring,
        "generate_insights": job_generate_insights,
        "full_pipeline":     job_full_pipeline,
    }


@scheduler_router.get("/status")
def scheduler_status() -> dict:
    """스케줄러 상태 및 등록된 잡 목록을 반환한다."""
    from services.scheduler import get_scheduler

    sched = get_scheduler()
    if sched is None or not sched.running:
        return {"running": False, "mode": "demo", "jobs": []}

    jobs = []
    for job in sched.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return {"running": True, "mode": "live", "jobs": jobs}


@scheduler_router.post("/trigger/{job_id}")
def trigger_job(job_id: str, background_tasks: BackgroundTasks) -> dict:
    """지정한 잡을 즉시 실행한다 (백그라운드)."""
    registry = _get_registry()
    if job_id not in registry:
        raise HTTPException(
            status_code=404,
            detail=f"job_id '{job_id}' 없음. 가능한 잡: {list(registry.keys())}",
        )
    background_tasks.add_task(registry[job_id])
    return {
        "status": "triggered",
        "job_id": job_id,
        "triggered_at": datetime.utcnow().isoformat(),
    }
