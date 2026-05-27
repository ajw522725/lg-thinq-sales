"""
수집기 공통 유틸리티 — rate limiter, 언어 감지, 제품군 매핑, 로거
"""
import hashlib
import logging
import time
from typing import Optional


# ── 로거 설정 ─────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"collector.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s — %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# ── Rate Limiter ──────────────────────────────────────────────────────────────

class RateLimiter:
    """요청 간격을 강제하여 차단 위험을 낮춘다."""

    def __init__(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self._last_call: float = 0.0

    def wait(self) -> None:
        import random
        elapsed = time.time() - self._last_call
        delay = random.uniform(self.min_seconds, self.max_seconds)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_call = time.time()


# ── 작성자 익명화 ──────────────────────────────────────────────────────────────

def hash_author(author: Optional[str]) -> Optional[str]:
    """작성자명을 SHA-256 앞 16자리로 익명화 (개인정보 비식별화)."""
    if not author:
        return None
    return hashlib.sha256(author.encode("utf-8")).hexdigest()[:16]


# ── 언어 감지 ─────────────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """텍스트 언어를 감지한다. 실패 시 'ko' 반환."""
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "ko"


# ── 제품군 매핑 ───────────────────────────────────────────────────────────────

PRODUCT_CATEGORY_MAP: dict[str, list[str]] = {
    "에어컨": ["에어컨", "냉방", "air conditioner", "스탠드형", "벽걸이", r"\bac\b", "에어콘"],
    "냉장고": ["냉장고", "냉동", "refrigerator", "fridge"],
    "세탁기": ["세탁기", "건조기", "드럼", "통돌이", "washer", "dryer", "washing machine"],
    "공기청정기": ["공기청정기", "air purifier", "공청기", "미세먼지"],
    "제습기": ["제습기", "제습", "dehumidifier"],
    "청소기": ["청소기", "로봇청소기", r"\bvacuum\b", "청소"],
    "식기세척기": ["식기세척기", "dishwasher"],
    "전자레인지": ["전자레인지", "microwave", "오븐"],
    "TV": [r"\btv\b", "텔레비전", "oled", "qned", "올레드"],
}

# 단어 경계 패턴이 필요한 키워드 (앞에 r"\b" 포함)
_REGEX_MARKER = r"\b"


def detect_product_category(text: str) -> Optional[str]:
    """텍스트에서 제품군을 추론한다. 단어 경계 패턴(\b)은 정규식으로 처리한다."""
    import re
    lower = text.lower()
    for category, keywords in PRODUCT_CATEGORY_MAP.items():
        for kw in keywords:
            if kw.startswith(_REGEX_MARKER):
                if re.search(kw, lower):
                    return category
            elif kw in lower:
                return category
    return None
