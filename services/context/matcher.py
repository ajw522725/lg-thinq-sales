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


def fetch_and_match(voc: ProcessedVOCInput) -> ContextEnrichmentResult:
    """
    Phase 5: 실제 공공 API를 호출해서 VOC와 매핑.
    API 키 없거나 호출 실패 시 _demo_context_match() fallback.
    """
    from .api_client import fetch_weather, fetch_air_quality

    relevant_types = PRODUCT_CONTEXT_MAP.get(
        voc.product_category, PRODUCT_CONTEXT_MAP["default"]
    )
    region = _extract_region(voc.normalized_text)
    date = voc.published_at

    fetched: list[ExternalContextData] = []
    if "weather" in relevant_types:
        w = fetch_weather(region, date)
        if w:
            fetched.append(w)
    if "air_quality" in relevant_types:
        a = fetch_air_quality(region)
        if a:
            fetched.append(a)

    if not fetched:
        return _demo_context_match(voc)

    return _real_context_match(voc, fetched)


def _real_context_match(
    voc: ProcessedVOCInput,
    contexts: list[ExternalContextData],
) -> ContextEnrichmentResult:
    """실제 외부 데이터 기반 매핑 (TRD 10.2)"""
    matches: list[ContextMatchResult] = []
    total_score = 0.0

    for ctx in contexts:
        score = _score_context_relevance(voc, ctx)
        if score > 0:
            matches.append(ContextMatchResult(
                voc_id=voc.id,
                external_context_id=ctx.id,
                match_reason=f"제품군({voc.product_category}) + {ctx.context_type}",
                match_score=score,
                context_type=ctx.context_type,
                context_summary=_summarize_context(ctx),
            ))
            total_score += score

    aggregated = round(min(total_score / max(len(matches), 1), 1.0), 4)
    description = ", ".join(f"{m.context_type}(score={m.match_score:.2f})" for m in matches)

    return ContextEnrichmentResult(
        voc_id=voc.id,
        matches=matches,
        aggregated_context_score=aggregated,
        context_description=description or "연관 외부 데이터 없음",
    )


def _score_context_relevance(voc: ProcessedVOCInput, ctx: ExternalContextData) -> float:
    """VOC-Context 연관도 점수 (0~1)"""
    relevant_types = PRODUCT_CONTEXT_MAP.get(voc.product_category, [])
    if ctx.context_type not in relevant_types:
        return 0.0

    base = 0.4
    text_lower = voc.normalized_text.lower()
    bonus = sum(
        0.15 for kw, t in KEYWORD_CONTEXT_MAP.items()
        if kw in text_lower and t == ctx.context_type
    )

    # 날씨: 여름/겨울 에어컨/제습기 → 높은 연관도
    if ctx.context_type == "weather":
        temp = ctx.data.get("temperature") or ctx.data.get("season", "")
        season = ctx.data.get("season", "")
        if season in ("여름", "겨울") and voc.product_category in ("air_conditioner", "dehumidifier"):
            bonus += 0.2

    # 공기질: 나쁨 등급 + 공기청정기
    if ctx.context_type == "air_quality":
        grade = str(ctx.data.get("grade", ""))
        if grade in ("나쁨", "매우나쁨", "4", "3") and voc.product_category == "air_purifier":
            bonus += 0.25

    return round(min(base + bonus, 1.0), 4)


def _extract_region(text: str) -> str | None:
    """텍스트에서 지역명 추출"""
    regions = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
               "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    for r in regions:
        if r in text:
            return r
    return None


def _summarize_context(ctx: ExternalContextData) -> str:
    if ctx.context_type == "weather":
        temp = ctx.data.get("temperature", "?")
        season = ctx.data.get("season", "")
        return f"기온 {temp}도, {season}" if season else f"기온 {temp}도"
    if ctx.context_type == "air_quality":
        pm25 = ctx.data.get("pm25", "?")
        grade = ctx.data.get("grade", "?")
        return f"PM2.5 {pm25}μg, 등급 {grade}"
    return str(ctx.data)
