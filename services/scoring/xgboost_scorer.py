"""
Phase 3: XGBoost 기반 Lead Score 보정
USE_ML_MODELS=true + 학습된 모델 파일 존재 시 활성화
그 외 rule_based_score() 자동 fallback

학습 방법 (모델 파일 생성):
  python services/scoring/train_xgb.py
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from .models import ScoringFeatures, LeadScoreResult

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "models" / "xgb_lead_score.pkl"

# XGBoost 입력 Feature 순서 (학습 시와 동일하게 유지)
FEATURE_NAMES = [
    "purchase_intent_score",
    "urgency_score",
    "competitor_mention_count",
    "competitor_comparison_flag",
    "complaint_intensity",
    "product_category_weight",
    "platform_weight",
    "engagement_score",
    "external_context_score",
]


def xgb_score(features: ScoringFeatures) -> LeadScoreResult | None:
    """
    XGBoost 모델로 Lead Score 예측.
    USE_ML_MODELS=false 또는 모델 파일 없으면 None 반환 → rule-based fallback.
    """
    use_ml = os.getenv("USE_ML_MODELS", "false").lower() == "true"
    if not use_ml:
        return None

    if not MODEL_PATH.exists():
        logger.debug(f"XGBoost 모델 없음: {MODEL_PATH} — rule-based 사용")
        return None

    try:
        import pickle
        import numpy as np
        from uuid import uuid4
        from datetime import datetime

        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)

        X = np.array([[
            features.purchase_intent_score,
            features.urgency_score,
            features.competitor_mention_count,
            float(features.competitor_comparison_flag),
            features.complaint_intensity,
            features.product_category_weight,
            features.platform_weight,
            features.engagement_score,
            features.external_context_score,
        ]])
        raw_score = float(model.predict(X)[0])
        score = round(max(0.0, min(100.0, raw_score)), 2)

        priority: str
        if score >= 80:
            priority = "high"
        elif score >= 50:
            priority = "medium"
        else:
            priority = "low"

        from .models import ScoreBreakdown
        breakdown = ScoreBreakdown(
            purchase_intent_contribution=round(features.purchase_intent_score * 35, 2),
            urgency_contribution=round(features.urgency_score * 15, 2),
            competitor_contribution=round(min(features.competitor_mention_count * 3, 10), 2),
            product_weight_contribution=round(features.product_category_weight * 10, 2),
            external_context_contribution=round(features.external_context_score * 10, 2),
            sentiment_adjustment=round(features.sentiment_score * 10, 2),
            engagement_contribution=round(features.engagement_score * 10, 2),
            top_factors=["XGBoost 예측"],
            explanation=f"Lead Score {score}점: XGBoost 모델 예측",
        )

        logger.info(f"XGBoost 예측: score={score}, priority={priority}")
        return LeadScoreResult(
            voc_id=features.voc_id,
            lead_score=score,
            priority=priority,
            score_reason=breakdown,
            model_version="xgboost_v1.0",
        )

    except Exception as e:
        logger.error(f"XGBoost 예측 실패: {e} — rule-based fallback")
        return None


def train_xgb_model(
    feature_matrix,   # np.ndarray shape (N, 9)
    labels,           # np.ndarray shape (N,) — 0~100 점수
    save_path: Path = MODEL_PATH,
) -> None:
    """
    XGBoost 모델 학습 및 저장.
    실제 라벨링 데이터가 충분할 때 실행.

    Args:
        feature_matrix: FEATURE_NAMES 순서로 정렬된 Feature 행렬
        labels: 각 VOC의 실제(정답) Lead Score (0~100)
        save_path: 저장할 모델 파일 경로
    """
    try:
        import pickle
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error

        X_train, X_test, y_train, y_test = train_test_split(
            feature_matrix, labels, test_size=0.2, random_state=42
        )
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        mae = mean_absolute_error(y_test, model.predict(X_test))
        logger.info(f"XGBoost 학습 완료: MAE={mae:.2f}")

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump(model, f)
        logger.info(f"모델 저장: {save_path}")

    except Exception as e:
        logger.error(f"XGBoost 학습 실패: {e}")
        raise
