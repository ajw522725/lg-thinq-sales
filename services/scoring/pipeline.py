"""
Lead Scoring 파이프라인 오케스트레이터
NLPAnalysisResult + VOC 메타 → LeadScoreResult
TRD 9장 기준 — yuna0822
"""
from __future__ import annotations

import logging

from ..nlp.models import NLPAnalysisResult, ProcessedVOCInput
from .features import build_feature_vector
from .rule_based import rule_based_score
from .models import LeadScoreResult

logger = logging.getLogger(__name__)


def run_lead_scoring(
    nlp: NLPAnalysisResult,
    voc: ProcessedVOCInput,
    external_context_score: float = 0.0,
) -> LeadScoreResult:
    """
    단일 VOC에 대한 Lead Score 산출

    Args:
        nlp: NLP 분석 결과 (run_nlp_pipeline 반환값)
        voc: 원본 VOC 입력
        external_context_score: 외부 데이터 연관 점수 (Phase 5 완성 후 사용)

    Returns:
        LeadScoreResult
    """
    logger.info(f"Lead Scoring 시작: voc_id={nlp.voc_id}")

    # 1. Feature Vector 생성
    features = build_feature_vector(nlp, voc, external_context_score)

    # 2. 룰 기반 점수 산출 (Phase 4에서 XGBoost로 보정)
    result = rule_based_score(features)

    logger.info(
        f"Lead Score 완료: voc_id={nlp.voc_id} | "
        f"score={result.lead_score} | priority={result.priority}"
    )
    return result


def run_scoring_on_nlp_results(
    nlp_results: list[NLPAnalysisResult],
    voc_map: dict,
) -> list[LeadScoreResult]:
    """
    NLP 결과 목록 전체에 대해 Lead Scoring 일괄 실행
    (Demo 모드 배치 실행용)

    Args:
        nlp_results: run_pipeline_on_demo_data() 반환값
        voc_map: voc_id → ProcessedVOCInput 딕셔너리

    Returns:
        LeadScoreResult 목록
    """
    results: list[LeadScoreResult] = []
    for nlp in nlp_results:
        voc = voc_map.get(nlp.voc_id)
        if voc is None:
            logger.warning(f"VOC 메타 없음: voc_id={nlp.voc_id}, 스킵")
            continue
        try:
            score = run_lead_scoring(nlp, voc)
            results.append(score)
        except Exception as e:
            logger.error(f"Lead Scoring 실패: voc_id={nlp.voc_id}, error={e}")
            # 개별 실패는 전체를 중단하지 않음 (TRD 16.2)

    return results
