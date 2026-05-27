"""
외부 데이터 ↔ VOC 매핑 로직
TRD 10장 기준 — yuna0822

Phase 5에서 실제 공공 API 연동으로 고도화 예정
현재: 제품군-context_type 매핑 룰 기반 스켈레톤
"""
from __future__ import annotations

import logging
from uuid import uuid4

from ..nlp.models import ProcessedVOCInput
from .models import ContextMatchResult, ContextEnrichmentResult, ExternalContextData

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 제품군별 주요 외부 데이터 매핑 (TRD 10.2)
# ──────────────────────────────────────────────
PRODUCT_CONTEXT_MAP: dict[str, list[str]] = {
    "air_conditioner":  ["weather"],
    "dehumidifier":     ["weather"],
    "air_purifier":     ["air_quality"],
    "refrigerator":     ["weather", "energy"],
    "washing_machine":  ["weather"],
    "default":          ["energy", "housing"],
}

# VOC 키워드 → context_type 매핑 (TRD 10.2)
KEYWORD_CONTEXT_MAP: dict[str, str] = {
    "습하다": "weather", "곰팡이": "weather", "덥다": "weather",
    "냉방": "weather",   "제습": "weather",
    "미세먼지": "air_quality", "공기청정": "air_quality", "먼지": "air_quality",
    "전기세": "energy",  "에너지": "energy", "전력": "energy",
    "이사": "housing",   "신혼가전": "housing", "입주": "housing",
}


def match_external_context(
    voc: ProcessedVOCInput,
    available_contexts: list[ExternalContextData] | None = None,
) -> ContextEnrichmentResult:
    """
    VOC와 외부 데이터를 매핑하여 Context 점수 산출

    Args:
        voc: 분석 대상 VOC
        available_contexts: 외부 데이터 목록 (None이면 Demo 모드 — 매핑 점수만 반환)

    Returns:
        ContextEnrichmentResult
    """
    # Phase 5 이전: 제품군 기반 매핑 점수만 산출 (Demo 모드)
    if available_contexts is None:
        return _demo_context_match(voc)

    # Phase 5: 실제 외부 데이터와 매핑 (TODO)
    return _real_context_match(voc, available_contexts)


def _demo_context_match(voc: ProcessedVOCInput) -> ContextEnrichmentResult:
    """
    Demo 모드: 실제 API 호출 없이 제품군 + 키워드 기반으로 context 점수 추정
    """
    text_lower = voc.normalized_text.lower()

    # 제품군 기반 기본 점수
    relevant_types = PRODUCT_CONTEXT_MAP.get(
        voc.product_category, PRODUCT_CONTEXT_MAP["default"]
    )
    base_score = 0.3 if relevant_types else 0.0

    # VOC 키워드 기반 추가 점수
    matched_types: list[str] = []
    for keyword, ctx_type in KEYWORD_CONTEXT_MAP.items():
        if keyword in text_lower and ctx_type in relevant_types:
            matched_types.append(ctx_type)

    keyword_bonus = min(len(set(matched_types)) * 0.15, 0.5)
    aggregated_score = round(min(base_score + keyword_bonus, 1.0), 4)

    description = (
        f"[Demo] 제품군={voc.product_category}, "
        f"연관 context={relevant_types}, "
        f"키워드 매칭={list(set(matched_types))}"
    ) if matched_types else f"[Demo] 제품군={voc.product_category} 기본 점수"

    # Demo context 매치 객체 생성 (실제 DB ID 없음)
    demo_matches = [
        ContextMatchResult(
            voc_id=voc.id,
            external_context_id=uuid4(),
            match_reason=f"제품군({voc.product_category}) → {ctx_type}",
            match_score=round(aggregated_score, 4),
            context_type=ctx_type,
            context_summary=f"[Demo] {ctx_type} 데이터 연관",
        )
        for ctx_type in set(relevant_types + matched_types)
    ]

    return ContextEnrichmentResult(
        voc_id=voc.id,
        matches=demo_matches,
        aggregated_context_score=aggregated_score,
        context_description=description,
    )


def _real_context_match(
    voc: ProcessedVOCInput,
    contexts: list[ExternalContextData],
) -> ContextEnrichmentResult:
    """
    Phase 5 구현 예정 — 실제 외부 데이터 기반 매핑

    매핑 기준 (TRD 10.2):
    - 시간: VOC 작성일 ±7일
    - 지역: 명시 지역 → 없으면 수도권 평균
    - 제품군: PRODUCT_CONTEXT_MAP 기준
    """
    # TODO Phase 5
    raise NotImplementedError("Phase 5에서 구현 예정 — 실제 공공 API 데이터 필요")
