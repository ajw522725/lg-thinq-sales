"""
Phase 3: BERTopic 기반 토픽 클러스터링
USE_ML_MODELS=true + TOPIC_MODEL_MIN_DOCS 이상 문서 수 시 활성화

단일 VOC 토픽: rule-based detect_topic() 유지
배치 토픽 학습: BERTopic fit_transform() 사용
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from .models import TopicResult

logger = logging.getLogger(__name__)

_topic_model = None   # BERTopic 모델 싱글톤
_MODEL_PATH = Path(os.getenv("TOPIC_MODEL_PATH", "models/bertopic_model"))

# BERTopic topic_id → 우리 토픽 레이블 매핑 (학습 후 수동 레이블링)
_TOPIC_LABEL_MAP: dict[int, tuple[str, str]] = {
    # topic_id: (topic_id_str, topic_label)
    # 학습 완료 후 채워야 함
}


def fit_batch_topic_model(texts: list[str]) -> list[TopicResult]:
    """
    BERTopic으로 텍스트 배치 학습 및 토픽 할당.
    USE_ML_MODELS=false 또는 최소 문서 수 미달 시 빈 리스트 반환.

    Args:
        texts: 전처리된 텍스트 목록 (최소 TOPIC_MODEL_MIN_DOCS 개 권장)

    Returns:
        각 텍스트에 대응하는 TopicResult 목록
    """
    use_ml = os.getenv("USE_ML_MODELS", "false").lower() == "true"
    min_docs = int(os.getenv("TOPIC_MODEL_MIN_DOCS", "10"))

    if not use_ml:
        logger.info("USE_ML_MODELS=false — BERTopic 비활성화")
        return []

    if len(texts) < min_docs:
        logger.warning(f"문서 수 부족({len(texts)} < {min_docs}) — BERTopic 스킵")
        return []

    try:
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer

        embedding_model = SentenceTransformer("jhgan/ko-sroberta-multitask")
        topic_model = BERTopic(
            embedding_model=embedding_model,
            min_topic_size=max(3, len(texts) // 5),
            language="multilingual",
            verbose=False,
        )
        topics, probs = topic_model.fit_transform(texts)
        logger.info(f"BERTopic 완료: {len(set(topics))}개 토픽 발견")

        results: list[TopicResult] = []
        for topic_id in topics:
            if topic_id == -1:  # 노이즈 토픽
                results.append(TopicResult())
                continue

            topic_words = topic_model.get_topic(topic_id) or []
            keywords = [word for word, _ in topic_words[:5]]
            label_info = _TOPIC_LABEL_MAP.get(topic_id)

            results.append(TopicResult(
                topic_id=str(topic_id),
                topic_label=label_info[1] if label_info else f"Topic-{topic_id}",
                topic_keywords=keywords,
            ))

        # 모델 저장 (재사용)
        _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        topic_model.save(str(_MODEL_PATH))
        logger.info(f"BERTopic 모델 저장: {_MODEL_PATH}")

        return results

    except Exception as e:
        logger.error(f"BERTopic 실패: {e}")
        return []


def load_and_predict(text: str) -> TopicResult:
    """
    저장된 BERTopic 모델로 단일 텍스트 토픽 예측.
    모델 없으면 rule-based detect_topic() fallback.
    """
    use_ml = os.getenv("USE_ML_MODELS", "false").lower() == "true"
    if not use_ml or not _MODEL_PATH.exists():
        return TopicResult()   # caller가 rule-based fallback 처리

    try:
        from bertopic import BERTopic
        model = BERTopic.load(str(_MODEL_PATH))
        topics, _ = model.transform([text])
        topic_id = topics[0]

        if topic_id == -1:
            return TopicResult()

        topic_words = model.get_topic(topic_id) or []
        keywords = [word for word, _ in topic_words[:5]]
        label_info = _TOPIC_LABEL_MAP.get(topic_id)

        return TopicResult(
            topic_id=str(topic_id),
            topic_label=label_info[1] if label_info else f"Topic-{topic_id}",
            topic_keywords=keywords,
        )
    except Exception as e:
        logger.error(f"BERTopic 예측 실패: {e}")
        return TopicResult()
