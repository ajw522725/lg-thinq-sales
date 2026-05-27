"""
풀 파이프라인 엔드포인트
POST /pipeline/run  — 단일 VOC 전체 분석
GET  /demo/run      — 데모 데이터 10개 일괄 분석
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.schemas.requests import VOCRequest
from app.schemas.responses import PipelineResponse, DemoRunResponse, NLPResponse, ScoreResponse, InsightResponse

router = APIRouter()

DEMO_DATA_PATH = Path(__file__).parents[6] / "data" / "demo" / "sample_voc.json"


def _build_processed_voc(req: VOCRequest):
    from services.nlp.models import ProcessedVOCInput
    return ProcessedVOCInput(
        id=uuid4(),
        raw_document_id=uuid4(),
        normalized_text=req.text,
        product_category=req.product_category,
        product_keyword=req.product_keyword,
        source=req.source,
        platform="api",
        language=req.language,
        rating=req.rating,
        platform_meta={**req.platform_meta, "engagement": req.engagement},
    )


def _run_pipeline(voc) -> tuple:
    """NLP → Score → Insight 실행, (nlp, score, insight) 반환"""
    from services.nlp.pipeline import run_nlp_pipeline
    from services.scoring.pipeline import run_lead_scoring
    from services.insights.pipeline import generate_insight

    nlp = run_nlp_pipeline(voc)
    score = run_lead_scoring(nlp, voc)
    result = generate_insight(nlp, voc, score)
    return nlp, score, result.insight


def _to_pipeline_response(voc, nlp, score, insight, elapsed_ms: float) -> PipelineResponse:
    import os
    return PipelineResponse(
        voc_id=str(nlp.voc_id),
        source=voc.source,
        product_category=voc.product_category,
        nlp=NLPResponse(
            voc_id=str(nlp.voc_id),
            sentiment_label=nlp.sentiment_label,
            sentiment_score=nlp.sentiment_score,
            intent_label=nlp.intent_label,
            purchase_intent_score=nlp.purchase_intent_score,
            urgency_score=nlp.urgency_score,
            complaint_type=nlp.complaint_type,
            topic_id=nlp.topic_id,
            topic_label=nlp.topic_label,
            keywords=nlp.keywords,
            competitor_mentions=nlp.competitor_mentions,
            competitor_comparison_flag=nlp.competitor_comparison_flag,
            model_version=nlp.model_version,
        ),
        score=ScoreResponse(
            lead_score=score.lead_score,
            priority=score.priority,
            score_reason=score.score_reason.model_dump(),
        ),
        insight=InsightResponse(
            title=insight.title,
            summary=insight.summary,
            recommended_action=insight.recommended_action,
            reasoning=insight.reasoning,
            confidence=insight.confidence,
            llm_model=insight.llm_model,
        ),
        processing_time_ms=round(elapsed_ms, 1),
        demo_mode=os.getenv("DEMO_MODE", "true").lower() == "true",
    )


@router.post("/pipeline/run", response_model=PipelineResponse, tags=["pipeline"])
def run_pipeline(req: VOCRequest):
    """
    단일 VOC에 대해 NLP 분석 → Lead Score → Strategy Insight 전체 파이프라인 실행
    """
    t0 = time.perf_counter()
    try:
        voc = _build_processed_voc(req)
        nlp, score, insight = _run_pipeline(voc)
        elapsed = (time.perf_counter() - t0) * 1000
        return _to_pipeline_response(voc, nlp, score, insight, elapsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo/run", response_model=DemoRunResponse, tags=["pipeline"])
def run_demo():
    """
    data/demo/sample_voc.json의 10개 데모 VOC에 대해 전체 파이프라인 실행
    API 키 없이 동작 확인 가능
    """
    if not DEMO_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Demo 데이터 없음: {DEMO_DATA_PATH}")

    from services.nlp.models import DemoVOCItem

    raw = json.loads(DEMO_DATA_PATH.read_text(encoding="utf-8"))
    items = [DemoVOCItem(**item) for item in raw]

    results = []
    for item in items:
        t0 = time.perf_counter()
        try:
            voc = item.to_processed_voc()
            nlp, score, insight = _run_pipeline(voc)
            elapsed = (time.perf_counter() - t0) * 1000
            results.append(_to_pipeline_response(voc, nlp, score, insight, elapsed))
        except Exception as e:
            continue

    return DemoRunResponse(total=len(results), results=results)
