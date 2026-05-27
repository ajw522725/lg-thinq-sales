"""
핵심 키워드 추출 모듈
Phase 2: Kiwi 명사 추출 기반, Phase 3에서 KeyBERT로 고도화 예정
"""
from __future__ import annotations

import re
from collections import Counter

from .models import KeywordResult


# 제품군별 핵심 키워드 사전 (리드 스코어링 가중치에 사용)
PRODUCT_KEYWORDS: dict[str, list[str]] = {
    "air_conditioner":  ["에어컨", "냉방", "냉각", "제습", "냄새", "소음", "전기세", "휘센", "air conditioner", "cooling"],
    "air_purifier":     ["공기청정기", "미세먼지", "필터", "환기", "퓨리케어", "air purifier", "filter", "dust"],
    "refrigerator":     ["냉장고", "냉동", "온도", "전기세", "디오스", "refrigerator", "fridge", "freezer"],
    "washing_machine":  ["세탁기", "세탁", "건조", "소음", "트롬", "washer", "laundry", "drum"],
    "dehumidifier":     ["제습기", "습도", "곰팡이", "장마", "습함", "dehumidifier", "humidity", "moisture"],
}

KO_STOPWORDS = {
    "이", "가", "을", "를", "은", "는", "의", "에", "도", "로", "와", "과",
    "에서", "이다", "있다", "하다", "되다", "것", "수", "그", "저", "들",
    "및", "등", "더", "좀", "잘", "못", "너무", "정말", "진짜", "아주",
}


def extract_keywords(text: str, lang: str, product_category: str | None = None, top_n: int = 8) -> KeywordResult:
    """
    핵심 키워드 추출

    Args:
        text: 전처리된 텍스트
        lang: "ko" | "en"
        product_category: 제품군 (제품 관련 키워드 우선 추출에 활용)
        top_n: 반환할 최대 키워드 수

    Returns:
        KeywordResult
    """
    # 토큰화
    if lang == "ko":
        tokens = _tokenize_ko(text)
    else:
        tokens = _tokenize_en(text)

    # 빈도 기반 키워드 추출
    freq = Counter(tokens)
    top_tokens = [token for token, _ in freq.most_common(top_n * 2)]

    # 제품군 관련 키워드 우선 필터링
    product_kws: list[str] = []
    if product_category and product_category in PRODUCT_KEYWORDS:
        ref_kws = PRODUCT_KEYWORDS[product_category]
        product_kws = [kw for kw in ref_kws if kw in text.lower()]

    # 상위 N개 키워드 선택
    general_kws = [t for t in top_tokens if t not in product_kws][:top_n]

    return KeywordResult(
        keywords=general_kws,
        product_keywords=product_kws,
    )


def _tokenize_ko(text: str) -> list[str]:
    """Kiwi 명사 추출 — NNG(일반명사) + NNP(고유명사)"""
    try:
        from .kiwi_utils import extract_nouns
        nouns = extract_nouns(text, min_len=2)
        return [n for n in nouns if n not in KO_STOPWORDS]
    except Exception:
        # Kiwi 실패 시 정규식 폴백
        tokens = re.findall(r"[가-힣]{2,}", text)
        return [t for t in tokens if t not in KO_STOPWORDS]


def _tokenize_en(text: str) -> list[str]:
    """영어 기본 토크나이징"""
    EN_STOPWORDS = {"the", "a", "an", "is", "it", "this", "that", "and", "or",
                    "but", "in", "on", "at", "to", "for", "of", "with", "my", "i"}
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return [t for t in tokens if t not in EN_STOPWORDS]
