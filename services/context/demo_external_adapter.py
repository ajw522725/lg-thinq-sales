from __future__ import annotations

from datetime import datetime
from typing import Any


REGION_ALIASES = {
    "Seoul": "서울",
    "Busan": "부산",
    "Daegu": "대구",
    "Incheon": "인천",
    "Gwangju": "광주",
    "Daejeon": "대전",
    "Ulsan": "울산",
    "Jeju": "제주",
    "National": "전국",
}


def normalize_region(region: str | None) -> str:
    if not region:
        return "전국"
    return REGION_ALIASES.get(region, region)


def normalize_product_category(product_category: str) -> str:
    normalized = product_category.strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "air_conditioner": "air_conditioner",
        "air_purifier": "air_purifier",
        "refrigerator": "refrigerator",
        "washer": "washing_machine",
        "washing_machine": "washing_machine",
        "dryer": "washing_machine",
        "dehumidifier": "dehumidifier",
        "subscription_care": "subscription_care",
        "lg_styler": "styler",
        "에어컨": "air_conditioner",
        "공기청정기": "air_purifier",
        "냉장고": "refrigerator",
        "세탁기": "washing_machine",
        "건조기": "washing_machine",
        "제습기": "dehumidifier",
        "구독": "subscription_care",
    }
    return mapping.get(normalized, normalized)


def infer_context_type(product_category: str, text: str) -> str:
    product = normalize_product_category(product_category)
    lower_text = text.lower()

    if product == "air_purifier" or any(keyword in lower_text for keyword in ("fine dust", "pm2.5", "미세먼지", "공기질", "air quality")):
        return "air_quality"
    if product in {"air_conditioner", "dehumidifier"} or any(keyword in lower_text for keyword in ("cooling", "humidity", "습도", "냉방", "더위", "제습")):
        return "weather"
    if any(keyword in lower_text for keyword in ("energy", "electric", "전기", "전기세", "에너지", "절전")):
        return "energy"
    if any(keyword in lower_text for keyword in ("moving", "newlywed", "이사", "신혼", "입주")):
        return "housing"
    if product == "subscription_care" or any(keyword in lower_text for keyword in ("subscription", "care plan", "구독", "케어", "렌탈")):
        return "subscription"
    return "none"


def build_demo_external_context(
    context_type: str,
    region: str | None,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    region_name = normalize_region(region)
    observed = observed_at or datetime.utcnow()

    if context_type == "air_quality":
        return {
            "context_type": "air_quality",
            "region": region_name,
            "observed_at": observed,
            "source_name": "demo-airkorea",
            "data": {
                "pm10": 45,
                "pm25": 22,
                "grade": "보통",
                "signal": "seasonal fine dust concern",
            },
            "summary": "PM2.5 22μg, 미세먼지 보통 수준",
        }
    if context_type == "weather":
        return {
            "context_type": "weather",
            "region": region_name,
            "observed_at": observed,
            "source_name": "demo-kma",
            "data": {
                "temperature": 29,
                "humidity": 72,
                "precipitation": "없음",
                "signal": "warm and humid demand context",
            },
            "summary": "기온 29도, 습도 72%",
        }
    if context_type == "energy":
        return {
            "context_type": "energy",
            "region": region_name,
            "observed_at": observed,
            "source_name": "demo-energy-context",
            "data": {
                "electricity_price_pressure": "medium",
                "seasonal_usage": "cooling demand rising",
                "signal": "energy saving value proposition",
            },
            "summary": "냉방 수요 증가와 전기요금 민감도 중간",
        }
    if context_type == "housing":
        return {
            "context_type": "housing",
            "region": region_name,
            "observed_at": observed,
            "source_name": "demo-housing-context",
            "data": {
                "moving_season": "active",
                "new_household_demand": "medium",
                "signal": "new household appliance purchase context",
            },
            "summary": "이사/신혼 가전 구매 맥락",
        }
    if context_type == "subscription":
        return {
            "context_type": "subscription",
            "region": region_name,
            "observed_at": observed,
            "source_name": "demo-subscription-context",
            "data": {
                "care_plan_interest": "high",
                "price_sensitivity": "medium",
                "signal": "subscription care comparison context",
            },
            "summary": "구독 케어 관심과 가격 민감도 동시 감지",
        }
    return {
        "context_type": "none",
        "region": region_name,
        "observed_at": observed,
        "source_name": "demo-context",
        "data": {"signal": "no strong external context"},
        "summary": "강한 외부 맥락 없음",
    }


def score_context_match(context_type: str, product_category: str, text: str) -> tuple[float, str]:
    product = normalize_product_category(product_category)
    lower_text = text.lower()

    if context_type == "air_quality":
        score = 0.65
        if product == "air_purifier":
            score += 0.15
        if any(keyword in lower_text for keyword in ("미세먼지", "pm2.5", "fine dust", "air quality")):
            score += 0.1
        return min(score, 0.95), "AirKorea demo context matched air purifier/fine dust demand"
    if context_type == "weather":
        score = 0.62
        if product in {"air_conditioner", "dehumidifier"}:
            score += 0.15
        if any(keyword in lower_text for keyword in ("냉방", "습도", "더위", "cooling", "humidity")):
            score += 0.1
        return min(score, 0.92), "KMA demo weather context matched cooling/humidity demand"
    if context_type == "energy":
        return 0.76, "Energy cost context matched efficiency/electricity keyword"
    if context_type == "housing":
        return 0.74, "Housing/moving context matched new appliance purchase keyword"
    if context_type == "subscription":
        return 0.78, "Subscription care context matched care plan/price sensitivity keyword"
    return 0.2, "No strong external context"
