"""
구매의도 탐지 모듈
Phase 2: Kiwi 형태소 기반 한국어 매칭
예) "구매했는데" → Kiwi 분석 → "구매"(NNG) → HIGH_INTENT 매칭
"""
from .models import IntentResult


# ──────────────────────────────────────────────
# 구매의도 키워드 사전 (TRD 8.3 기준)
# ──────────────────────────────────────────────
HIGH_INTENT = {
    "ko": ["구매", "살까", "주문", "결제", "구입", "렌탈 신청", "구독 신청", "견적", "바꾸려고", "교체", "설치 예정"],
    "en": ["buy", "purchase", "order", "subscribe", "rental", "planning to get", "going to buy"],
}
MEDIUM_INTENT = {
    "ko": ["고민", "비교", "추천", "어떤게", "렌탈", "구독", "할인", "가격", "견적", "살지"],
    "en": ["considering", "comparing", "recommend", "worth it", "thinking about", "price", "discount", "quote"],
}
LOW_INTENT = {
    "ko": ["궁금", "문의", "어떻게", "후기", "사용기", "리뷰"],
    "en": ["wondering", "curious", "review", "feedback", "inquiry"],
}


def detect_purchase_intent(text: str, lang: str) -> IntentResult:
    """
    구매의도 탐지

    Args:
        text: 전처리된 텍스트
        lang: "ko" | "en"

    Returns:
        IntentResult
    """
    _lang = lang if lang in ("ko", "en") else "en"

    high_kw = HIGH_INTENT.get(_lang, HIGH_INTENT["en"])
    mid_kw  = MEDIUM_INTENT.get(_lang, MEDIUM_INTENT["en"])
    low_kw  = LOW_INTENT.get(_lang, LOW_INTENT["en"])

    if _lang == "ko":
        high_matches, mid_matches, low_matches = _match_ko(text, high_kw, mid_kw, low_kw)
    else:
        text_lower = text.lower()
        high_matches = [kw for kw in high_kw if kw in text_lower]
        mid_matches  = [kw for kw in mid_kw  if kw in text_lower]
        low_matches  = [kw for kw in low_kw  if kw in text_lower]

    all_matches = high_matches + mid_matches + low_matches

    score = 0.0
    if high_matches:
        score = min(0.8 + len(high_matches) * 0.05, 1.0)
    elif mid_matches:
        score = min(0.4 + len(mid_matches) * 0.08, 0.79)
    elif low_matches:
        score = min(0.1 + len(low_matches) * 0.05, 0.39)

    if score >= 0.7:
        label = "high"
    elif score >= 0.4:
        label = "medium"
    else:
        label = "low"

    return IntentResult(
        purchase_intent_score=round(score, 4),
        intent_label=label,
        matched_keywords=all_matches,
    )


def _match_ko(
    text: str,
    high_kw: list[str],
    mid_kw: list[str],
    low_kw: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """
    한국어 형태소 기반 매칭
    1차: Kiwi 형태소 추출 → 키워드가 형태소 목록에 있으면 매칭
    2차: 원문 서브스트링 매칭 (복합어, 구 단위 키워드 처리)
    """
    try:
        from .kiwi_utils import extract_morphemes
        morphemes = set(extract_morphemes(text, min_len=1))
    except Exception:
        morphemes = set()

    text_lower = text.lower()

    def match(kw_list: list[str]) -> list[str]:
        hits = []
        for kw in kw_list:
            # 단일 형태소 키워드 → 형태소 집합에서 검색
            # 복합 키워드 (공백 포함) → 원문 서브스트링 검색
            if " " in kw:
                if kw in text_lower:
                    hits.append(kw)
            else:
                if kw in morphemes or kw in text_lower:
                    hits.append(kw)
        return hits

    return match(high_kw), match(mid_kw), match(low_kw)
