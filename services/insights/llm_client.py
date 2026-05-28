"""
LLM API 클라이언트 (OpenAI / Gemini / Demo)
TRD 11장 기준 -yuna0822

Demo 모드: API 키 없이 규칙 기반 인사이트 생성
Phase 6에서 실제 API 연동으로 고도화 예정
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_RESPONSE_KEYS = ("title", "summary", "recommended_action", "reasoning", "confidence")


# ──────────────────────────────────────────────
# Demo 모드 인사이트 템플릿 (우선순위별)
# ──────────────────────────────────────────────
_DEMO_TEMPLATES: dict[str, dict] = {
    "high": {
        "title": "즉시 영업 접촉 권장",
        "summary": (
            "해당 고객은 높은 구매 의도와 긴급도를 보이고 있습니다. "
            "경쟁사 제품과 적극적으로 비교 중이며 빠른 결정을 내릴 가능성이 높습니다."
        ),
        "recommended_action": (
            "24시간 이내 담당 영업 사원이 직접 연락하여 맞춤 견적과 "
            "프로모션 정보를 제공하세요."
        ),
        "reasoning": (
            "Lead Score 80점 이상으로 구매 의도 신호가 강합니다. "
            "긴급 표현과 경쟁사 비교 언급이 동시에 감지되어 전환 시점이 임박했습니다."
        ),
        "confidence": 0.85,
    },
    "medium": {
        "title": "관심 고객 - 정보 제공 우선",
        "summary": (
            "구매를 고려 중이나 아직 결정을 내리지 못한 고객입니다. "
            "제품 기능 및 가격 정보에 관심이 있습니다."
        ),
        "recommended_action": (
            "제품 스펙 비교 자료와 할부/렌탈 옵션 안내 콘텐츠를 이메일 또는 "
            "앱 푸시로 발송하세요."
        ),
        "reasoning": (
            "Lead Score 50~79점 구간으로 중간 구매 의도를 나타냅니다. "
            "추가 정보 제공을 통해 구매 결정을 촉진할 수 있습니다."
        ),
        "confidence": 0.70,
    },
    "low": {
        "title": "장기 육성 고객 -브랜드 인지 강화",
        "summary": (
            "현재 즉각적인 구매 의도는 낮지만 브랜드에 관심을 보이는 고객입니다. "
            "장기 관계 형성이 중요합니다."
        ),
        "recommended_action": (
            "뉴스레터 구독 유도 및 ThinQ 앱 기능 소개 콘텐츠로 브랜드 친밀도를 높이세요."
        ),
        "reasoning": (
            "Lead Score 50점 미만으로 구매 전환까지 시간이 필요합니다. "
            "지속적인 브랜드 노출로 잠재 리드를 육성하는 전략이 적합합니다."
        ),
        "confidence": 0.55,
    },
}


def call_llm(
    system_prompt: str,
    user_prompt: str,
    priority: str = "medium",
    nlp_context: dict | None = None,
) -> dict:
    """
    LLM 호출 -환경변수에 따라 OpenAI / Gemini / Demo 모드 선택

    Args:
        system_prompt: 시스템 프롬프트
        user_prompt: 유저 프롬프트
        priority: Lead Score 우선순위
        nlp_context: Demo 모드에서 인사이트를 맥락화하기 위한 NLP 데이터
                     (topic_id, sentiment_label, keywords, competitor_mentions, product_category)
    """
    provider = _provider()

    if _is_demo_mode() or provider == "demo":
        return _with_gateway_meta(
            _demo_response(priority, nlp_context),
            provider="demo",
            model="demo-rule-generator",
            is_demo=True,
        )

    try:
        if provider == "openai":
            raw = _call_openai(system_prompt, user_prompt)
            return _with_gateway_meta(
                _normalize_response(raw),
                provider="openai",
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                is_demo=False,
            )

        if provider == "gemini":
            raw = _call_gemini(system_prompt, user_prompt)
            return _with_gateway_meta(
                _normalize_response(raw),
                provider="gemini",
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
                is_demo=False,
            )

        raise RuntimeError(f"지원하지 않는 LLM_PROVIDER={provider}")
    except Exception as exc:
        if not _fallback_to_demo():
            raise
        logger.warning(f"LLM provider={provider} 호출 실패, demo fallback 사용: {exc}")
        fallback = _demo_response(priority, nlp_context)
        fallback["_fallback_reason"] = str(exc)
        return _with_gateway_meta(
            fallback,
            provider=provider,
            model="demo-rule-generator",
            is_demo=True,
        )


def current_llm_model() -> str:
    provider = _provider()
    if _is_demo_mode() or provider == "demo":
        return "demo-rule-generator"
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o")
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    return "demo-rule-generator"


def is_demo_response(raw: dict[str, Any] | None = None) -> bool:
    if raw and "_llm_is_demo" in raw:
        return bool(raw["_llm_is_demo"])
    return _is_demo_mode() or _provider() == "demo"


def _demo_response(priority: str, ctx: dict | None = None) -> dict:
    """
    Demo 모드: topic + sentiment + competitor 기반 맥락화된 인사이트 반환
    ctx keys: topic_id, topic_label, sentiment_label, keywords,
              competitor_mentions, product_category, urgency_score
    """
    base = dict(_DEMO_TEMPLATES.get(priority, _DEMO_TEMPLATES["medium"]))
    if not ctx:
        logger.info("[Demo] 컨텍스트 없음 -기본 템플릿 반환")
        return base

    topic_id = ctx.get("topic_id") or ""
    sentiment = ctx.get("sentiment_label", "neutral")
    competitors = ctx.get("competitor_mentions") or {}
    keywords = ctx.get("keywords") or []
    product = ctx.get("product_category", "가전")
    urgency = float(ctx.get("urgency_score", 0.0))

    # 토픽별 맞춤 title / action
    title, action = _topic_title_action(topic_id, priority, product, competitors)

    # summary: 감성 + 키워드 반영
    kw_str = ", ".join(keywords[:3]) if keywords else product
    comp_str = (
        f" 특히 {', '.join(list(competitors.keys())[:2])} 경쟁사와 비교 중입니다."
        if competitors else ""
    )
    urgency_str = " 긴급한 불만 표현이 감지되었습니다." if urgency >= 0.3 else ""
    summary = (
        f"고객은 {product} 관련 '{kw_str}' 키워드를 중심으로 "
        f"{'긍정적' if sentiment == 'positive' else '부정적' if sentiment == 'negative' else '중립적'} "
        f"반응을 보이고 있습니다.{comp_str}{urgency_str}"
    )

    # reasoning: lead score 기여 요소 반영
    reasoning = base["reasoning"]
    if competitors:
        reasoning += f" 경쟁사({', '.join(list(competitors.keys()))}) 언급이 전환 가능성을 높입니다."

    base.update({"title": title, "summary": summary, "recommended_action": action, "reasoning": reasoning})
    logger.info(f"[Demo] topic={topic_id} priority={priority} 맥락화 인사이트 반환")
    return base


def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "demo").lower().strip()


def _is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "true").lower() == "true"


def _fallback_to_demo() -> bool:
    return os.getenv("LLM_FALLBACK_TO_DEMO", "true").lower() == "true"


def _timeout() -> float:
    return float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))


def _with_gateway_meta(raw: dict[str, Any], provider: str, model: str, is_demo: bool) -> dict[str, Any]:
    normalized = _normalize_response(raw)
    for key, value in raw.items():
        if key.startswith("_"):
            normalized[key] = value
    normalized["_llm_provider"] = provider
    normalized["_llm_model"] = model
    normalized["_llm_is_demo"] = is_demo
    return normalized


def _normalize_response(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("LLM response must be a JSON object.")

    result = {
        "title": str(raw.get("title") or "전략 인사이트"),
        "summary": str(raw.get("summary") or "VOC 분석 결과를 바탕으로 영업 후속 조치가 필요합니다."),
        "recommended_action": str(raw.get("recommended_action") or "담당자가 VOC 맥락을 확인하고 맞춤 안내를 진행하세요."),
        "reasoning": str(raw.get("reasoning") or "감성, 구매의도, 리드 점수, 외부 context를 기반으로 생성된 demo 인사이트입니다."),
        "confidence": _clamp_confidence(raw.get("confidence", 0.5)),
    }

    missing = [key for key in REQUIRED_RESPONSE_KEYS if key not in raw]
    if missing:
        logger.info(f"LLM 응답 누락 필드 보정: {missing}")
    return result


def _clamp_confidence(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = 0.5
    return round(max(0.0, min(parsed, 1.0)), 4)


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response does not contain a JSON object.")
    return json.loads(stripped[start : end + 1])


# ──────────────────────────────────────────────
# 토픽별 title / action 매핑
# ──────────────────────────────────────────────
_TOPIC_TITLE: dict[str, str] = {
    "subscription_pricing":   "구독/렌탈 전환 의향 고객 감지",
    "installation_delivery":  "설치·배송 불만 고객 -즉각 대응 필요",
    "thinq_connectivity":     "ThinQ 앱 연결 불편 -UX 개선 요청",
    "energy_efficiency":      "에너지 절감 관심 고객 -기능 어필 필요",
    "air_quality":            "공기질 이슈 -공기청정기/필터 수요 감지",
    "maintenance_as":         "A/S·유지보수 불만 고객 -CS 에스컬레이션",
    "purchase_consideration": "비교 구매 단계 고객 -전환 촉진 타이밍",
}

_TOPIC_ACTION: dict[str, str] = {
    "subscription_pricing":   "렌탈/구독 월정액 비교표와 무료 체험 옵션을 제공하여 결정을 도우세요.",
    "installation_delivery":  "설치 일정을 확인하고 24시간 내 담당자가 직접 연락하세요.",
    "thinq_connectivity":     "ThinQ 앱 설정 가이드를 발송하고 연결 문제 원격 지원을 제안하세요.",
    "energy_efficiency":      "에너지 등급 비교 자료와 전기료 절감 계산기 링크를 제공하세요.",
    "air_quality":            "계절별 필터 구독 옵션과 공기질 센서 연동 기능을 소개하세요.",
    "maintenance_as":         "A/S 접수를 즉시 처리하고 서비스 보증 연장 프로모션을 안내하세요.",
    "purchase_consideration": "경쟁사 대비 비교표와 한정 프로모션 코드를 이메일로 발송하세요.",
}


def _topic_title_action(
    topic_id: str, priority: str, product: str, competitors: dict
) -> tuple[str, str]:
    title = _TOPIC_TITLE.get(topic_id, _DEMO_TEMPLATES.get(priority, {}).get("title", "VOC 인사이트"))
    action = _TOPIC_ACTION.get(topic_id, f"{product} 관련 맞춤 영업 자료를 준비하여 접촉하세요.")
    if competitors and topic_id in ("purchase_consideration", "subscription_pricing"):
        action += f" 경쟁사({', '.join(list(competitors.keys())[:2])}) 대비 차별점을 강조하세요."
    return title, action


def _call_openai(system_prompt: str, user_prompt: str) -> dict:
    """OpenAI API 호출 (Phase 6)"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key, timeout=_timeout())
    model = os.getenv("OPENAI_MODEL", "gpt-4o")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
    )
    content = response.choices[0].message.content or "{}"
    return _parse_json_object(content)


def _call_gemini(system_prompt: str, user_prompt: str) -> dict:
    """Gemini API 호출 (Phase 6)"""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

    import google.generativeai as genai  # type: ignore

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    model = genai.GenerativeModel(
        model_name,
        system_instruction=system_prompt,
    )
    response = model.generate_content(
        user_prompt,
        generation_config={"temperature": float(os.getenv("LLM_TEMPERATURE", "0.3"))},
    )
    return _parse_json_object(response.text)
