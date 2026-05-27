"""
텍스트 전처리 모듈
Phase 2: Kiwi 형태소 분석 기반 한국어 토크나이징
"""
from __future__ import annotations

import re
import unicodedata

from langdetect import detect, LangDetectException

from .models import PreprocessResult


# ──────────────────────────────────────────────
# 제품명 / 브랜드 보호 사전
# ──────────────────────────────────────────────
BRAND_DICT = [
    "LG전자", "LG", "삼성전자", "삼성", "다이슨", "Dyson",
    "샤오미", "Xiaomi", "캐리어", "위니아", "Whirlpool",
    "휘센", "퓨리케어", "디오스", "트롬", "ThinQ",
]

# ──────────────────────────────────────────────
# 불용어 목록 (기본)
# ──────────────────────────────────────────────
KO_STOPWORDS = {
    "이", "가", "을", "를", "은", "는", "의", "에", "도", "로",
    "와", "과", "에서", "이다", "있다", "하다", "되다", "것", "수",
    "그", "이", "저", "들", "및", "등", "더", "좀", "잘", "못",
}


def detect_language(text: str) -> str:
    """
    텍스트의 언어를 감지합니다.
    반환값: "ko" | "en" | "other"
    """
    try:
        lang = detect(text)
        if lang == "ko":
            return "ko"
        elif lang == "en":
            return "en"
        else:
            return "other"
    except LangDetectException:
        return "other"


def remove_html_tags(text: str) -> str:
    """HTML 태그 제거"""
    return re.sub(r"<[^>]+>", " ", text)


def remove_urls(text: str) -> str:
    """URL 제거"""
    return re.sub(r"https?://\S+|www\.\S+", " ", text)


def normalize_whitespace(text: str) -> str:
    """중복 공백 / 줄바꿈 정리"""
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def normalize_unicode(text: str) -> str:
    """유니코드 정규화 (NFC)"""
    return unicodedata.normalize("NFC", text)


def handle_emoji(text: str, mode: str = "remove") -> str:
    """
    이모지 처리
    mode="remove": 이모지 제거
    mode="space": 이모지를 공백으로 치환

    주의: \U000024C2-\U0001F251 범위는 한글 음절(U+AC00-U+D7A3)을 포함하므로 제외
    """
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"   # Emoticons
        "\U0001F300-\U0001F5FF"   # Misc Symbols & Pictographs
        "\U0001F680-\U0001F6FF"   # Transport & Map
        "\U0001F1E0-\U0001F1FF"   # Country flags
        "\U00002702-\U000027B0"   # Dingbats (ends at U+27B0, 한글 U+AC00 이전)
        "\U0001F900-\U0001F9FF"   # Supplemental Symbols
        "\U0001FA00-\U0001FAFF"   # Symbols and Pictographs Extended-A
        "]+",
        flags=re.UNICODE,
    )
    replacement = " " if mode == "space" else ""
    return emoji_pattern.sub(replacement, text)


def split_sentences(text: str) -> list[str]:
    """문장 단위 분리 (마침표, 개행, 느낌표, 물음표 기준)"""
    sentences = re.split(r"(?<=[.!?])\s+|(?<=다)\s+|(?<=요)\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def clean_special_chars(text: str) -> str:
    """
    특수문자 정리
    주의: 느낌표(!), 물음표(?)는 긴급도 분석에 사용되므로 유지
    """
    # 반복 특수문자 축약 (!!!!! → !)
    text = re.sub(r"([!?]){2,}", r"\1\1", text)
    # 분석에 불필요한 특수문자 제거 (단, . ! ? , 는 유지)
    text = re.sub(r"[^\w\s.!?,가-힣a-zA-Z0-9]", " ", text)
    return text


def preprocess(text: str, lang: str | None = None) -> PreprocessResult:
    """
    텍스트 전처리 메인 함수

    Args:
        text: 원문 텍스트
        lang: 언어 코드 (없으면 자동 감지)

    Returns:
        PreprocessResult: 정제된 텍스트 및 메타데이터
    """
    original = text

    # 1. 공통 정제
    text = normalize_unicode(text)
    text = remove_html_tags(text)
    text = remove_urls(text)
    text = handle_emoji(text, mode="remove")
    text = clean_special_chars(text)
    text = normalize_whitespace(text)

    # 2. 언어 감지
    detected_lang = lang or detect_language(text)

    # 3. 문장 분리
    sentences = split_sentences(text)

    # 4. 기본 토크나이징 (Phase 2에서 형태소 분석으로 대체)
    tokens = _basic_tokenize(text, detected_lang)

    return PreprocessResult(
        original_text=original,
        cleaned_text=text,
        language=detected_lang,
        sentences=sentences,
        tokens=tokens,
    )


def _basic_tokenize(text: str, lang: str) -> list[str]:
    """한국어: Kiwi 형태소 분석, 영어: 공백 기반 기본 처리"""
    if lang == "ko":
        return _kiwi_tokenize(text)
    else:
        import re
        tokens = [re.sub(r"[^a-z]", "", t) for t in text.lower().split()]
        return [t for t in tokens if len(t) > 2]


def _kiwi_tokenize(text: str) -> list[str]:
    """Kiwi 형태소 분석으로 의미 토큰 추출 (명사 + 동사 + 형용사)"""
    try:
        from .kiwi_utils import extract_morphemes
        tokens = extract_morphemes(text, min_len=2)
        return [t for t in tokens if t not in KO_STOPWORDS]
    except Exception:
        # Kiwi 실패 시 기본 공백 분리로 폴백
        tokens = re.findall(r"[가-힣]{2,}", text)
        return [t for t in tokens if t not in KO_STOPWORDS]
