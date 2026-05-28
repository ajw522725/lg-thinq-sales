"""
VOC 수집·분석 배치 잡 정의.

각 잡은 독립적으로 실행되며, 실패해도 다른 잡에 영향을 주지 않는다.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("scheduler.jobs")


# ── 1. VOC 수집 ───────────────────────────────────────────────────────────────

def job_collect_voc(keywords: list[str] | None = None) -> dict:
    """4개 플랫폼에서 VOC를 수집하고 DB에 적재한다."""
    from services.collectors.runner import DEFAULT_KEYWORDS, run_collection

    kws = keywords or DEFAULT_KEYWORDS
    logger.info(f"[job_collect_voc] 시작 keywords={kws}")

    try:
        result = run_collection(kws, max_per_source=50, save=True)
        stats = result["stats"]
        logger.info(
            f"[job_collect_voc] 완료 — "
            f"수집 {stats['total']}건 / 통과 {stats['passed']}건 / "
            f"품질 필터 {stats['filtered_quality']}건 / 중복 {stats['filtered_duplicate']}건"
        )
        return {"status": "ok", "stats": stats}
    except Exception as exc:
        logger.error(f"[job_collect_voc] 실패: {exc}", exc_info=True)
        return {"status": "error", "error": str(exc)}


# ── 2. VOC → DB 적재 ──────────────────────────────────────────────────────────

def job_ingest_to_db(processed_docs: list[dict] | None = None) -> dict:
    """수집된 VOC를 PostgreSQL에 적재한다."""
    try:
        from apps.api.app.db.session import SessionLocal
        from apps.api.app.repositories.voc_repository import ingest_vocs
        from apps.api.app.schemas.domain import IngestionVOC

        if not processed_docs:
            # 최신 JSONL에서 로드
            from services.collectors.runner import _PROCESSED_LATEST
            import json
            if not _PROCESSED_LATEST.exists():
                logger.warning("[job_ingest_to_db] processed latest 파일 없음 — 스킵")
                return {"status": "skipped"}
            with open(_PROCESSED_LATEST, encoding="utf-8") as f:
                processed_docs = [json.loads(line) for line in f if line.strip()]

        payload = [IngestionVOC(**d) for d in processed_docs]
        db = SessionLocal()
        try:
            result = ingest_vocs(db, payload, reset=False)
        finally:
            db.close()

        logger.info(f"[job_ingest_to_db] 적재 완료 — {result.processed_documents}건")
        return {"status": "ok", "inserted": result.processed_documents}
    except Exception as exc:
        logger.error(f"[job_ingest_to_db] 실패: {exc}", exc_info=True)
        return {"status": "error", "error": str(exc)}


# ── 3. NLP 분석 ───────────────────────────────────────────────────────────────

def job_run_nlp() -> dict:
    """분석되지 않은 VOC에 NLP 파이프라인을 실행한다."""
    try:
        from apps.api.app.db.session import SessionLocal
        from apps.api.app.services.pipeline_service import run_pending_nlp

        db = SessionLocal()
        try:
            count = run_pending_nlp(db)
        finally:
            db.close()

        logger.info(f"[job_run_nlp] 완료 — {count}건 처리")
        return {"status": "ok", "processed": count}
    except Exception as exc:
        logger.error(f"[job_run_nlp] 실패: {exc}", exc_info=True)
        return {"status": "error", "error": str(exc)}


# ── 4. Lead Scoring ───────────────────────────────────────────────────────────

def job_run_lead_scoring() -> dict:
    """NLP 완료된 VOC에 리드 스코어링을 실행한다."""
    try:
        from apps.api.app.db.session import SessionLocal
        from apps.api.app.services.pipeline_service import run_pending_scoring

        db = SessionLocal()
        try:
            count = run_pending_scoring(db)
        finally:
            db.close()

        logger.info(f"[job_run_lead_scoring] 완료 — {count}건")
        return {"status": "ok", "scored": count}
    except Exception as exc:
        logger.error(f"[job_run_lead_scoring] 실패: {exc}", exc_info=True)
        return {"status": "error", "error": str(exc)}


# ── 5. Strategy Insight 생성 ──────────────────────────────────────────────────

def job_generate_insights() -> dict:
    """High 우선순위 리드에 대해 LLM 전략 인사이트를 생성한다."""
    try:
        from apps.api.app.db.session import SessionLocal
        from apps.api.app.services.pipeline_service import run_pending_insights

        db = SessionLocal()
        try:
            count = run_pending_insights(db)
        finally:
            db.close()

        logger.info(f"[job_generate_insights] 완료 — {count}건")
        return {"status": "ok", "generated": count}
    except Exception as exc:
        logger.error(f"[job_generate_insights] 실패: {exc}", exc_info=True)
        return {"status": "error", "error": str(exc)}


# ── 6. 풀 파이프라인 (수집 → NLP → 스코어 → 인사이트) ────────────────────────

def job_full_pipeline(keywords: list[str] | None = None) -> dict:
    """수집부터 인사이트 생성까지 전체 파이프라인을 순서대로 실행한다."""
    logger.info("[job_full_pipeline] 전체 파이프라인 시작")
    results = {}

    results["collect"] = job_collect_voc(keywords)
    if results["collect"]["status"] == "ok":
        results["ingest"] = job_ingest_to_db()
    results["nlp"]      = job_run_nlp()
    results["scoring"]  = job_run_lead_scoring()
    results["insights"] = job_generate_insights()

    failed = [k for k, v in results.items() if v.get("status") == "error"]
    status = "partial_error" if failed else "ok"
    logger.info(f"[job_full_pipeline] 완료 status={status} failed={failed}")
    return {"status": status, "results": results, "failed_steps": failed}
