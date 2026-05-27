"""
전략 인사이트 생성 파이프라인 오케스트레이터
NLPAnalysisResult + LeadScoreResult + ContextEnrichmentResult → StrategyInsight
TRD 11장 기준 — yuna0822
"""
from __future__ import annotations

import logging

from ..nlp.models import NLPAnalysisResult, ProcessedVOCInput
from ..scoring.models import LeadScoreResult
from ..context.models import ContextEnrichmentResult
from .models import StrategyInsight, InsightGenerationResult
from .prompt_builder import build_insight_prompt
from .llm_client import call_llm

logger = logging.getLogger(__name__)


def generate_insight(
    nlp: NLPAnalysisResult,
    voc: ProcessedVOCInput,
    score: LeadScoreResult,
    context: ContextEnrichmentResult | None = None,
) -> InsightGenerationResult:
    """
    단일 VOC에 대한 전략 인사이트 생성

    Args:
        nlp: NLP 분석 결과
        voc: 원본 VOC 입력
        score: Lead Score 산출 결과
        context: 외부 데이터 Context 결합 결과 (없으면 생략)

    Returns:
        InsightGenerationResult
    """
    logger.info(f"인사이트 생성 시작: voc_id={nlp.voc_id}")

    system_prompt, user_prompt = build_insight_prompt(nlp, voc, score, context)
    nlp_context = {
        "topic_id": nlp.topic_id,
        "topic_label": nlp.topic_label,
        "sentiment_label": nlp.sentiment_label,
        "keywords": nlp.keywords[:5],
        "competitor_mentions": nlp.competitor_mentions,
        "product_category": voc.product_category,
        "urgency_score": nlp.urgency_score,
    }
    raw = call_llm(system_prompt, user_prompt, priority=score.priority, nlp_context=nlp_context)

    insight = StrategyInsight(
        voc_id=nlp.voc_id,
        lead_score_id=score.id,
        title=raw.get("title", "인사이트 제목 없음"),
        summary=raw.get("summary", ""),
        recommended_action=raw.get("recommended_action", ""),
        reasoning=raw.get("reasoning", ""),
        confidence=float(raw.get("confidence", 0.5)),
        llm_model=_current_llm_model(),
    )

    logger.info(
        f"인사이트 생성 완료: voc_id={nlp.voc_id} | "
        f"priority={score.priority} | confidence={insight.confidence}"
    )
    return InsightGenerationResult(
        voc_id=nlp.voc_id,
        lead_score_id=score.id,
        insight=insight,
        is_demo=_is_demo_mode(),
    )


def generate_insights_batch(
    nlp_results: list[NLPAnalysisResult],
    voc_map: dict,
    score_map: dict,
    context_map: dict | None = None,
) -> list[InsightGenerationResult]:
    """
    NLP 결과 목록 전체에 대해 인사이트 일괄 생성
    (Demo 모드 배치 실행용)

    Args:
        nlp_results: NLP 분석 결과 목록
        voc_map: voc_id → ProcessedVOCInput
        score_map: voc_id → LeadScoreResult
        context_map: voc_id → ContextEnrichmentResult (없으면 생략)

    Returns:
        InsightGenerationResult 목록
    """
    results: list[InsightGenerationResult] = []
    for nlp in nlp_results:
        voc = voc_map.get(nlp.voc_id)
        score = score_map.get(nlp.voc_id)
        if voc is None or score is None:
            logger.warning(f"VOC 또는 Score 없음: voc_id={nlp.voc_id}, 스킵")
            continue
        context = (context_map or {}).get(nlp.voc_id)
        try:
            result = generate_insight(nlp, voc, score, context)
            results.append(result)
        except Exception as e:
            logger.error(f"인사이트 생성 실패: voc_id={nlp.voc_id}, error={e}")

    return results


def _is_demo_mode() -> bool:
    import os
    return os.getenv("DEMO_MODE", "true").lower() == "true"


def _current_llm_model() -> str:
    import os
    provider = os.getenv("LLM_PROVIDER", "demo").lower()
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o")
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    return "demo"
