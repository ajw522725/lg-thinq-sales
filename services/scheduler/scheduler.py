"""
APScheduler 기반 배치 스케줄러.

수집 주기 (PRD 기준):
  - 전체 파이프라인: 6시간마다 (기본)
  - 데모 모드: 스케줄러 비활성화, 수동 트리거만 허용

환경변수:
  SCHEDULER_ENABLED=true|false   (기본 true, DEMO_MODE=true면 자동 false)
  SCHEDULER_COLLECT_INTERVAL_H   VOC 수집 주기 (기본 6시간)
  SCHEDULER_NLP_INTERVAL_H       NLP 분석 주기 (기본 1시간)
  SCHEDULER_INSIGHT_INTERVAL_H   인사이트 생성 주기 (기본 2시간)
"""
from __future__ import annotations

import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

logger = logging.getLogger("scheduler")

_scheduler: BackgroundScheduler | None = None


def _job_listener(event) -> None:
    if event.exception:
        logger.error(f"잡 실패: job_id={event.job_id} error={event.exception}")
    else:
        logger.info(f"잡 완료: job_id={event.job_id} retval={event.retval}")


def _is_enabled() -> bool:
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    use_demo  = os.getenv("USE_DEMO_DATA", "false").lower() == "true"
    if demo_mode or use_demo:
        return False
    return os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler


def start_scheduler() -> None:
    global _scheduler

    if not _is_enabled():
        logger.info("스케줄러 비활성 (DEMO_MODE=true 또는 SCHEDULER_ENABLED=false)")
        return

    collect_h = int(os.getenv("SCHEDULER_COLLECT_INTERVAL_H", "6"))
    nlp_h     = int(os.getenv("SCHEDULER_NLP_INTERVAL_H", "1"))
    insight_h = int(os.getenv("SCHEDULER_INSIGHT_INTERVAL_H", "2"))

    _scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    _scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # VOC 수집 → DB 적재 (6시간)
    from services.scheduler.jobs import job_collect_voc, job_ingest_to_db
    _scheduler.add_job(
        func=job_collect_voc,
        trigger=IntervalTrigger(hours=collect_h),
        id="collect_voc",
        name="VOC 수집 (4 플랫폼)",
        replace_existing=True,
        misfire_grace_time=300,
    )
    _scheduler.add_job(
        func=job_ingest_to_db,
        trigger=IntervalTrigger(hours=collect_h, minutes=10),
        id="ingest_to_db",
        name="VOC DB 적재",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # NLP 분석 (1시간)
    from services.scheduler.jobs import job_run_nlp
    _scheduler.add_job(
        func=job_run_nlp,
        trigger=IntervalTrigger(hours=nlp_h),
        id="run_nlp",
        name="NLP 분석 파이프라인",
        replace_existing=True,
        misfire_grace_time=180,
    )

    # Lead Scoring (1시간 + 30분 오프셋)
    from services.scheduler.jobs import job_run_lead_scoring
    _scheduler.add_job(
        func=job_run_lead_scoring,
        trigger=IntervalTrigger(hours=nlp_h, minutes=30),
        id="lead_scoring",
        name="Lead Scoring",
        replace_existing=True,
        misfire_grace_time=180,
    )

    # 인사이트 생성 (2시간)
    from services.scheduler.jobs import job_generate_insights
    _scheduler.add_job(
        func=job_generate_insights,
        trigger=IntervalTrigger(hours=insight_h),
        id="generate_insights",
        name="LLM 전략 인사이트 생성",
        replace_existing=True,
        misfire_grace_time=180,
    )

    _scheduler.start()
    jobs = _scheduler.get_jobs()
    logger.info(
        f"스케줄러 시작 — 등록 잡 {len(jobs)}개 "
        f"(수집 {collect_h}h / NLP {nlp_h}h / 인사이트 {insight_h}h)"
    )
    for job in jobs:
        logger.info(f"  [{job.id}] {job.name} | next_run={job.next_run_time}")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료")
    _scheduler = None
