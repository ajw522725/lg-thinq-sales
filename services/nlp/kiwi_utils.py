"""
Kiwi 한국어 형태소 분석기 공유 유틸리티
Java 없이 동작하는 순수 C++/Python 기반
첫 호출 시 모델 로드 (~1-2초), 이후 싱글톤으로 재사용
"""
from __future__ import annotations

from kiwipiepy import Kiwi

_kiwi: Kiwi | None = None

# 명사 태그
NOUN_TAGS = {"NNG", "NNP"}
# 의미 형태소 태그 (명사 + 동사어간 + 형용사어간 + 부사)
CONTENT_TAGS = {"NNG", "NNP", "VV", "VA", "MAG"}


def get_kiwi() -> Kiwi:
    """Kiwi 인스턴스 싱글톤 반환"""
    global _kiwi
    if _kiwi is None:
        _kiwi = Kiwi()
    return _kiwi


def extract_nouns(text: str, min_len: int = 2) -> list[str]:
    """
    명사 추출 (NNG 일반명사 + NNP 고유명사)
    keywords.py에서 사용
    """
    kiwi = get_kiwi()
    tokens = kiwi.tokenize(text)
    return [t.form for t in tokens if t.tag in NOUN_TAGS and len(t.form) >= min_len]


def extract_morphemes(text: str, min_len: int = 1) -> list[str]:
    """
    의미 형태소 추출 (명사 + 동사 + 형용사 + 부사)
    intent.py에서 키워드 매칭에 사용:
    예) "구매했는데" → ["구매", "하"] 에서 "구매" 추출 가능
    """
    kiwi = get_kiwi()
    tokens = kiwi.tokenize(text)
    return [t.form for t in tokens if t.tag in CONTENT_TAGS and len(t.form) >= min_len]
