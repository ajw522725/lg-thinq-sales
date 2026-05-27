"""
NLP 분석 전용 엔드포인트
POST /nlp/analyze
"""
from __future__ import annotations

from uuid import uuid4
from fastapi import APIRouter, HTTPException

from app.schemas.requests import VOCRequest
from app.schemas.responses import NLPResponse

router = APIRouter()


@router.post("/nlp/analyze", response_model=NLPResponse, tags=["nlp"])
def analyze_nlp(req: VOCRequest):
    """
    NLP 분석만 단독 실행 (감성, 구매의도, 긴급도, 키워드, 경쟁사, 토픽)
    """
    try:
        from services.nlp.models import ProcessedVOCInput
        from services.nlp.pipeline import run_nlp_pipeline

        voc = ProcessedVOCInput(
            id=uuid4(),
            raw_document_id=uuid4(),
            normalized_text=req.text,
            product_category=req.product_category,
            product_keyword=req.product_keyword,
            source=req.source,
            platform="api",
            language=req.language,
            rating=req.rating,
            platform_meta=req.platform_meta,
        )
        nlp = run_nlp_pipeline(voc)

        return NLPResponse(
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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
