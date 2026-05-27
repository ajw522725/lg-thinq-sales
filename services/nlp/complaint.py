"""
불만 유형 분류 모듈
9가지 카테고리 분류 (TRD 8.4 기준)
"""
from .models import ComplaintResult


# ──────────────────────────────────────────────
# 불만 카테고리별 키워드 사전
# ──────────────────────────────────────────────
COMPLAINT_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "price":          {"ko": ["비싸", "가격", "돈", "환불", "할인", "가성비"],
                       "en": ["expensive", "price", "overpriced", "refund", "cost"]},
    "performance":    {"ko": ["성능", "약하다", "안 됨", "작동", "오작동", "불량"],
                       "en": ["performance", "doesn't work", "malfunction", "broken", "defective"]},
    "installation":   {"ko": ["설치", "배송", "기사", "지연", "파손"],
                       "en": ["installation", "delivery", "damaged", "delay", "setup"]},
    "as_service":     {"ko": ["AS", "수리", "서비스", "응대", "연락", "기다"],
                       "en": ["service", "repair", "support", "wait", "response", "contact"]},
    "noise":          {"ko": ["소음", "시끄럽", "소리", "진동", "떨림"],
                       "en": ["noise", "loud", "vibration", "sound", "rattle"]},
    "energy":         {"ko": ["전기세", "전기요금", "에너지", "전력", "효율"],
                       "en": ["electricity", "energy", "power consumption", "efficiency", "utility"]},
    "hygiene":        {"ko": ["냄새", "곰팡이", "세균", "위생", "청소"],
                       "en": ["smell", "mold", "bacteria", "hygiene", "odor", "clean"]},
    "connectivity":   {"ko": ["앱", "연결", "와이파이", "ThinQ", "블루투스", "끊김"],
                       "en": ["app", "wifi", "connection", "bluetooth", "ThinQ", "disconnect"]},
    "competitor":     {"ko": ["삼성", "다이슨", "샤오미", "캐리어", "비교", "대신"],
                       "en": ["samsung", "dyson", "xiaomi", "competitor", "instead", "switched"]},
}


def classify_complaint(text: str, lang: str) -> ComplaintResult:
    """
    불만 유형 분류

    Args:
        text: 전처리된 텍스트
        lang: "ko" | "en"

    Returns:
        ComplaintResult
    """
    text_lower = text.lower()
    _lang = lang if lang in ("ko", "en") else "ko"

    scores: dict[str, int] = {}
    for category, kw_map in COMPLAINT_KEYWORDS.items():
        kws = kw_map.get(_lang, kw_map.get("ko", []))
        hit = sum(1 for kw in kws if kw in text_lower)
        if hit > 0:
            scores[category] = hit

    if not scores:
        return ComplaintResult(is_complaint=False)

    top_category = max(scores, key=lambda k: scores[k])
    total_hits = sum(scores.values())
    complaint_score = min(scores[top_category] / max(total_hits, 1), 1.0)

    return ComplaintResult(
        complaint_type=top_category,
        complaint_score=round(complaint_score, 4),
        is_complaint=True,
    )
