"""
Phase 3: KoBERT/KoRoBERTa 기반 감성분석
USE_ML_MODELS=true 시 활성화, 실패 시 rule-based 자동 fallback

지원 모델 (SENTIMENT_MODEL 환경변수로 선택):
  - snunlp/KR-FinBert-SC  (한국어 금융 감성 — 기본값)
  - klue/roberta-base      (범용 한국어)
  - monologg/koelectra-base-finetuned-sentiment
"""
from __future__ import annotations

import logging
import os

from .models import SentimentResult

logger = logging.getLogger(__name__)

_pipeline = None   # transformers pipeline 싱글톤


def _load_pipeline() -> bool:
    """감성분석 모델 lazy load. 성공 여부 반환."""
    global _pipeline
    if _pipeline is not None:
        return True
    try:
        from transformers import pipeline as hf_pipeline

        model_name = os.getenv("SENTIMENT_MODEL", "snunlp/KR-FinBert-SC")
        logger.info(f"감성분석 모델 로드 중: {model_name}")
        _pipeline = hf_pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            top_k=None,         # 모든 레이블 확률 반환
            truncation=True,
            max_length=int(os.getenv("NLP_MAX_LENGTH", "512")),
        )
        logger.info(f"감성분석 모델 로드 완료: {model_name}")
        return True
    except Exception as e:
        logger.warning(f"ML 모델 로드 실패({e}) — rule-based 사용")
        return False


# KR-FinBert-SC 레이블 매핑 (모델마다 레이블명이 다를 수 있음)
_LABEL_MAP: dict[str, str] = {
    "positive": "positive", "pos": "positive", "LABEL_2": "positive",
    "negative": "negative", "neg": "negative", "LABEL_0": "negative",
    "neutral":  "neutral",  "neu": "neutral",  "LABEL_1": "neutral",
}


def analyze_sentiment_ml(
    text: str,
    lang: str,
    rating: float | None = None,
) -> SentimentResult:
    """
    ML 기반 감성분석.
    USE_ML_MODELS=true이고 모델 로드 성공 시 사용.
    그 외 자동으로 rule-based fallback.
    """
    use_ml = os.getenv("USE_ML_MODELS", "false").lower() == "true"
    if not use_ml or not _load_pipeline():
        from .sentiment import analyze_sentiment
        return analyze_sentiment(text, lang, rating)

    try:
        results = _pipeline(text[:512])[0]  # list of {label, score}
        label_scores: dict[str, float] = {
            _LABEL_MAP.get(r["label"].lower(), "neutral"): r["score"]
            for r in results
        }

        best_label = max(label_scores, key=lambda k: label_scores[k])
        best_score = label_scores[best_label]
        confidence = best_score

        # rating 보정 (rule-based와 동일)
        if rating is not None:
            rating_score = (rating - 1) / 4.0
            blended = best_score * 0.5 + rating_score * 0.5
            if blended >= 0.6:
                best_label = "positive"
            elif blended <= 0.4:
                best_label = "negative"
            else:
                best_label = "neutral"
            best_score = blended

        return SentimentResult(
            label=best_label,
            score=round(best_score, 4),
            confidence=round(confidence, 4),
            model_used=os.getenv("SENTIMENT_MODEL", "ko_finbert"),
        )

    except Exception as e:
        logger.error(f"ML 감성분석 실패: {e} — rule-based fallback")
        from .sentiment import analyze_sentiment
        return analyze_sentiment(text, lang, rating)
