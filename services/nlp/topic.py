"""
토픽 클러스터링 모듈
Phase 3에서 BERTopic으로 교체 예정
현재: 키워드 기반 rule-based 토픽 분류 (골격)
"""
from .models import TopicResult


# ──────────────────────────────────────────────
# 토픽 사전 (제품군별 주요 이슈)
# ──────────────────────────────────────────────
TOPIC_DICT: dict[str, dict[str, list[str]]] = {
    "subscription_pricing": {
        "ko": ["구독", "렌탈", "월정액", "가격", "요금", "할인", "혜택"],
        "en": ["subscription", "rental", "monthly", "price", "discount"],
        "label": "구독/가격",
    },
    "installation_delivery": {
        "ko": ["설치", "배송", "기사", "설치비", "파손"],
        "en": ["installation", "delivery", "setup", "damaged"],
        "label": "설치/배송",
    },
    "thinq_connectivity": {
        "ko": ["ThinQ", "앱", "연결", "와이파이", "블루투스", "끊김"],
        "en": ["ThinQ", "app", "wifi", "connection", "bluetooth"],
        "label": "앱/연결성",
    },
    "energy_efficiency": {
        "ko": ["전기세", "에너지", "효율", "전력", "절전"],
        "en": ["electricity", "energy", "efficiency", "power"],
        "label": "에너지 효율",
    },
    "air_quality": {
        "ko": ["미세먼지", "공기청정", "필터", "환기", "대기질"],
        "en": ["dust", "air quality", "filter", "ventilation"],
        "label": "공기질",
    },
    "maintenance_as": {
        "ko": ["AS", "수리", "고장", "유지", "관리", "냄새", "곰팡이"],
        "en": ["repair", "maintenance", "broken", "service", "smell"],
        "label": "유지보수/AS",
    },
    "purchase_consideration": {
        "ko": ["구매", "비교", "고민", "추천", "어떤", "살까"],
        "en": ["buy", "compare", "considering", "recommend", "which"],
        "label": "구매 고민",
    },
}


def detect_topic(text: str, lang: str) -> TopicResult:
    """
    토픽 탐지 (단일 VOC 대상)
    배치 토픽 모델링(BERTopic)과 별개로 단일 VOC에 토픽 매핑 수행

    Args:
        text: 전처리된 텍스트
        lang: "ko" | "en"

    Returns:
        TopicResult
    """
    text_lower = text.lower()
    _lang = lang if lang in ("ko", "en") else "ko"

    topic_scores: dict[str, int] = {}
    for topic_id, topic_data in TOPIC_DICT.items():
        kws = topic_data.get(_lang, topic_data.get("ko", []))
        hit = sum(1 for kw in kws if kw.lower() in text_lower)
        if hit > 0:
            topic_scores[topic_id] = hit

    if not topic_scores:
        return TopicResult()

    top_topic = max(topic_scores, key=lambda k: topic_scores[k])
    topic_info = TOPIC_DICT[top_topic]
    matched_kws = [kw for kw in topic_info.get(_lang, []) if kw.lower() in text_lower]

    return TopicResult(
        topic_id=top_topic,
        topic_label=topic_info.get("label", top_topic),
        topic_keywords=matched_kws,
    )


def run_batch_topic_modeling(texts: list[str]) -> list[TopicResult]:
    """
    BERTopic 기반 배치 토픽 모델링 (Phase 3 구현 예정)
    현재: 개별 rule-based 탐지로 대체

    Args:
        texts: 전처리된 텍스트 목록

    Returns:
        각 텍스트에 대응하는 TopicResult 목록
    """
    # TODO Phase 3: BERTopic 모델 로드 및 fit_transform 구현
    # from bertopic import BERTopic
    # from sentence_transformers import SentenceTransformer
    # embedding_model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    # topic_model = BERTopic(embedding_model=embedding_model, min_topic_size=5)
    # topics, probs = topic_model.fit_transform(texts)
    raise NotImplementedError("BERTopic 배치 모델링은 Phase 3에서 구현 예정입니다.")
