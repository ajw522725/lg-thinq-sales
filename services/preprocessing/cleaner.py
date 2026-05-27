"""
VOC 텍스트 전처리 — 정규화, 중복 제거, 품질 필터링.

주요 기능:
  - HTML 태그 제거
  - 연속 공백/개행 정규화
  - 제로폭 문자 제거
  - 최소 길이 필터 (기본 30자)
  - 중복 제거 (정확 일치 + 유사도 기반)
  - 경쟁사 언급 탐지 (platform_meta 보완)
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional

# 제거 대상 패턴
_HTML_TAG = re.compile(r"<[^>]+>")
_ZERO_WIDTH = re.compile(r"[​‌‍﻿­]+")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_URL_PATTERN = re.compile(r"https?://\S+")

# 스팸/저품질 패턴 (VOC 가치 없는 텍스트)
_SPAM_PATTERNS = [
    re.compile(r"(광고|협찬|제공받아|소정의 수수료|파트너스 활동)", re.IGNORECASE),
    re.compile(r"(구독|좋아요|알림설정|눌러주세요){2,}", re.IGNORECASE),
    re.compile(r"^(ㅋ+|ㅎ+|ㄷ+|ㅠ+|ㅜ+|👍+|❤+)$"),
]

# 경쟁사 키워드
_COMPETITOR_KEYWORDS = {
    "삼성": "Samsung", "samsung": "Samsung",
    "다이슨": "Dyson", "dyson": "Dyson",
    "위니아": "Winix", "winix": "Winix",
    "샤오미": "Xiaomi", "xiaomi": "Xiaomi",
    "캐리어": "Carrier", "carrier": "Carrier",
    "whirlpool": "Whirlpool",
    "블루에어": "Blueair", "blueair": "Blueair",
}

SPACE_PATTERN = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """텍스트를 정규화한다."""
    text = _HTML_TAG.sub(" ", text)
    text = _ZERO_WIDTH.sub("", text)
    text = _URL_PATTERN.sub("", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def clean_text(text: str) -> str:
    """Backward-compatibility alias for normalize_text."""
    cleaned = _HTML_TAG.sub(" ", text)
    cleaned = _URL_PATTERN.sub(" ", cleaned)
    cleaned = cleaned.replace("​", " ")
    cleaned = SPACE_PATTERN.sub(" ", cleaned)
    return cleaned.strip()


def is_quality(text: str, min_len: int = 30) -> bool:
    """VOC로 사용할 만한 품질인지 판단한다."""
    if len(text) < min_len:
        return False
    for pattern in _SPAM_PATTERNS:
        if pattern.search(text):
            return False
    # 한글/영어 실질 문자가 최소 10자 이상
    meaningful = re.sub(r"[^가-힣a-zA-Z]", "", text)
    return len(meaningful) >= 10


def content_hash(text: str) -> str:
    """본문 텍스트의 SHA-256 앞 16자리 해시를 반환한다 (중복 탐지용)."""
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def detect_competitors(text: str) -> list[str]:
    """텍스트에서 경쟁사 언급을 탐지한다."""
    lower = text.lower()
    found = set()
    for kw, brand in _COMPETITOR_KEYWORDS.items():
        if kw.lower() in lower:
            found.add(brand)
    return sorted(found)


def preprocess_document(doc: dict, min_len: int = 30) -> Optional[dict]:
    """
    단일 RawDocument dict를 전처리한다.
    품질 미달이면 None 반환.

    반환 dict는 ProcessedVOC 스키마와 대응:
      - normalized_text
      - content_hash (중복 탐지용)
      - competitor_mentions
      - quality_pass
    """
    raw_text = doc.get("content", "")
    normalized = normalize_text(raw_text)

    if not is_quality(normalized, min_len):
        return None

    competitors = detect_competitors(normalized)

    # platform_meta의 competitor_mentions 보완 (Reddit/YouTube는 이미 있을 수 있음)
    existing = doc.get("platform_meta", {}).get("competitor_mentions", [])
    merged_competitors = sorted(set(existing) | {c.lower() for c in competitors})

    processed = dict(doc)
    processed["content"] = normalized
    processed["normalized_text"] = normalized
    processed["content_hash"] = content_hash(normalized)
    processed["platform_meta"] = {
        **doc.get("platform_meta", {}),
        "competitor_mentions": merged_competitors,
    }
    return processed


def deduplicate(docs: list[dict]) -> list[dict]:
    """content_hash 기준으로 중복 문서를 제거한다."""
    seen: set[str] = set()
    result = []
    for doc in docs:
        h = doc.get("content_hash") or content_hash(doc.get("content", ""))
        if h not in seen:
            seen.add(h)
            result.append(doc)
    return result


def preprocess_batch(docs: list[dict], min_len: int = 30) -> dict:
    """
    RawDocument 목록을 전처리한다.

    반환:
      {
        "processed": list[dict],   전처리 통과 문서
        "stats": {
          "total": int,
          "passed": int,
          "filtered_quality": int,
          "filtered_duplicate": int,
        }
      }
    """
    total = len(docs)
    cleaned = []
    filtered_quality = 0

    for doc in docs:
        result = preprocess_document(doc, min_len)
        if result is None:
            filtered_quality += 1
        else:
            cleaned.append(result)

    deduped = deduplicate(cleaned)
    filtered_duplicate = len(cleaned) - len(deduped)

    return {
        "processed": deduped,
        "stats": {
            "total": total,
            "passed": len(deduped),
            "filtered_quality": filtered_quality,
            "filtered_duplicate": filtered_duplicate,
        },
    }
