"""
Phase 5: 외부 공공 데이터 API 클라이언트
- 기상청 단기예보 API (data.go.kr)
- 한국환경공단 에어코리아 API (data.go.kr)

API 키 발급: https://www.data.go.kr 회원가입 후 신청
환경변수: WEATHER_API_KEY, AIR_QUALITY_API_KEY
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from .models import ExternalContextData

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 지역 코드 (기상청 격자 좌표 — 주요 도시)
# ──────────────────────────────────────────────
REGION_GRID: dict[str, tuple[int, int]] = {
    "서울": (60, 127), "부산": (98, 76),  "대구": (89, 90),
    "인천": (55, 124), "광주": (58, 74),  "대전": (67, 100),
    "울산": (102, 84), "세종": (66, 103), "경기": (60, 120),
    "강원": (73, 134), "충북": (69, 107), "충남": (68, 100),
    "전북": (63, 89),  "전남": (51, 67),  "경북": (89, 91),
    "경남": (91, 77),  "제주": (52, 38),
}

DEFAULT_REGION = os.getenv("WEATHER_REGION", "서울")


def fetch_weather(region: str | None = None, date: datetime | None = None) -> ExternalContextData | None:
    """
    기상청 단기예보 API 호출
    WEATHER_API_KEY 없으면 None 반환 (Demo fallback)

    Args:
        region: 지역명 (없으면 WEATHER_REGION 환경변수 사용)
        date: 조회 날짜 (없으면 오늘)
    """
    api_key = os.getenv("WEATHER_API_KEY", "")
    if not api_key or api_key == "...":
        logger.debug("WEATHER_API_KEY 없음 — Demo fallback")
        return _demo_weather(region or DEFAULT_REGION, date)

    try:
        target_date = date or datetime.now()
        region_name = region or DEFAULT_REGION
        nx, ny = REGION_GRID.get(region_name, REGION_GRID["서울"])

        base_date = target_date.strftime("%Y%m%d")
        base_time = _get_nearest_forecast_time(target_date)

        params = {
            "serviceKey": api_key,
            "numOfRows": 10,
            "pageNo": 1,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }
        url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?" + urlencode(params)
        with urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = data["response"]["body"]["items"]["item"]
        weather_data = {item["category"]: item["fcstValue"] for item in items}

        return ExternalContextData(
            context_type="weather",
            region=region_name,
            observed_at=target_date,
            data={
                "temperature": weather_data.get("TMP", "N/A"),
                "humidity": weather_data.get("REH", "N/A"),
                "precipitation": weather_data.get("PCP", "N/A"),
                "sky": weather_data.get("SKY", "N/A"),
            },
            source_name="기상청 단기예보",
        )
    except Exception as e:
        logger.error(f"기상청 API 실패: {e} — Demo fallback")
        return _demo_weather(region or DEFAULT_REGION, date)


def fetch_air_quality(region: str | None = None) -> ExternalContextData | None:
    """
    에어코리아 미세먼지 API 호출
    AIR_QUALITY_API_KEY 없으면 Demo fallback
    """
    api_key = os.getenv("AIR_QUALITY_API_KEY", "")
    if not api_key or api_key == "...":
        logger.debug("AIR_QUALITY_API_KEY 없음 — Demo fallback")
        return _demo_air_quality(region or DEFAULT_REGION)

    try:
        region_name = region or DEFAULT_REGION
        params = {
            "serviceKey": api_key,
            "returnType": "json",
            "numOfRows": 1,
            "pageNo": 1,
            "sidoName": region_name,
            "ver": "1.0",
        }
        url = "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty?" + urlencode(params)
        with urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        item = data["response"]["body"]["items"][0]
        return ExternalContextData(
            context_type="air_quality",
            region=region_name,
            observed_at=datetime.now(),
            data={
                "pm10": item.get("pm10Value", "N/A"),
                "pm25": item.get("pm25Value", "N/A"),
                "grade": item.get("pm10Grade1h", "N/A"),
                "o3": item.get("o3Value", "N/A"),
            },
            source_name="에어코리아",
        )
    except Exception as e:
        logger.error(f"에어코리아 API 실패: {e} — Demo fallback")
        return _demo_air_quality(region or DEFAULT_REGION)


# ──────────────────────────────────────────────
# Demo 모드 (API 키 없이 동작)
# ──────────────────────────────────────────────

def _demo_weather(region: str, date: datetime | None) -> ExternalContextData:
    """계절 기반 가상 날씨 데이터"""
    month = (date or datetime.now()).month
    if month in (6, 7, 8):
        desc = {"temperature": "33", "humidity": "82", "precipitation": "없음", "season": "여름"}
    elif month in (12, 1, 2):
        desc = {"temperature": "-2", "humidity": "45", "precipitation": "없음", "season": "겨울"}
    elif month in (3, 4, 5):
        desc = {"temperature": "18", "humidity": "55", "precipitation": "없음", "season": "봄"}
    else:
        desc = {"temperature": "15", "humidity": "68", "precipitation": "있음", "season": "가을"}
    return ExternalContextData(
        context_type="weather",
        region=region,
        observed_at=date or datetime.now(),
        data=desc,
        source_name="[Demo] 기상 시뮬레이션",
    )


def _demo_air_quality(region: str) -> ExternalContextData:
    """가상 공기질 데이터"""
    return ExternalContextData(
        context_type="air_quality",
        region=region,
        observed_at=datetime.now(),
        data={"pm10": "45", "pm25": "22", "grade": "보통", "o3": "0.04"},
        source_name="[Demo] 공기질 시뮬레이션",
    )


def _get_nearest_forecast_time(dt: datetime) -> str:
    """기상청 단기예보 발표 시각 계산 (0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300)"""
    forecast_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    hour = dt.hour
    for h in reversed(forecast_hours):
        if hour >= h:
            return f"{h:02d}00"
    return "2300"
