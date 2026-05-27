"""
NLP 파이프라인 오케스트레이터
전처리 → 분석 6종 → NLPAnalysisResult 반환
"""
import json
import logging
from pathlib import Path
from uuid import uuid4

from .models import (
    DemoVOCItem,
    NLPAnalysisResult,
    ProcessedVOCInput,
)
from .preprocessor import preprocess
from .sentiment import analyze_sentiment
from .intent import detect_purchase_intent
from .complaint import classify_complaint
from .urgency import analyze_urgency
from .keywords import extract_keywords
from .competitor import detect_competitors
from .topic import detect_topic

logger = logging.getLogger(__name__)

DEMO_DATA_PATH = Path(__file__).parents[2] / "data" / "demo" / "sample_voc.json"


def run_nlp_pipeline(voc: ProcessedVOCInput) -> NLPAnalysisResult:
    """
    단일 VOC에 대해 전체 NLP 분석 파이프라인 실행

    Args:
        voc: ProcessedVOCInput

    Returns:
        NLPAnalysisResult — DB NLPAnalysis 테이블에 저장할 결과
    """
    logger.info(f"NLP 파이프라인 시작: voc_id={voc.id}")

    # 1. 전처리
    preprocessed = preprocess(voc.normalized_text, lang=voc.language)
    text = preprocessed.cleaned_text
    lang = preprocessed.language

    # 2. 감성분석
    sentiment = analyze_sentiment(text, lang, rating=voc.rating)

    # 3. 구매의도 탐지
    intent = detect_purchase_intent(text, lang)

    # 4. 불만 유형 분류
    complaint = classify_complaint(text, lang)

    # 5. 긴급도 분석
    urgency = analyze_urgency(text, lang, sentiment=sentiment)

    # 6. 키워드 추출
    keywords = extract_keywords(text, lang, product_category=voc.product_category)

    # 7. 경쟁사 언급 탐지
    competitor = detect_competitors(text)

    # 8. 토픽 탐지
    topic = detect_topic(text, lang)

    result = NLPAnalysisResult(
        id=uuid4(),
        voc_id=voc.id,
        sentiment_label=sentiment.label,
        sentiment_score=sentiment.score,
        confidence=sentiment.confidence,
        purchase_intent_score=intent.purchase_intent_score,
        intent_label=intent.intent_label,
        urgency_score=urgency.urgency_score,
        complaint_type=complaint.complaint_type if complaint.is_complaint else None,
        topic_id=topic.topic_id,
        topic_label=topic.topic_label,
        keywords=keywords.keywords + keywords.product_keywords,
        competitor_mentions=competitor.competitor_mentions,
        competitor_comparison_flag=competitor.competitor_comparison_flag,
        model_version="rule_based_v1.0",
    )

    logger.info(
        f"NLP 완료: voc_id={voc.id} | "
        f"sentiment={result.sentiment_label} | "
        f"intent={result.intent_label} | "
        f"topic={result.topic_label}"
    )
    return result


def run_pipeline_on_demo_data() -> list[NLPAnalysisResult]:
    """
    Demo 모드: sample_voc.json을 읽어 전체 파이프라인 실행
    API key 없이 동작 검증에 활용
    """
    if not DEMO_DATA_PATH.exists():
        raise FileNotFoundError(f"Demo 데이터 없음: {DEMO_DATA_PATH}")

    raw = json.loads(DEMO_DATA_PATH.read_text(encoding="utf-8"))
    items = [DemoVOCItem(**item) for item in raw]

    results: list[NLPAnalysisResult] = []
    for item in items:
        voc = item.to_processed_voc()
        try:
            result = run_nlp_pipeline(voc)
            results.append(result)
        except Exception as e:
            logger.error(f"파이프라인 실패: id={item.id}, error={e}")
            # 개별 실패는 전체를 중단하지 않음 (TRD 16.2)

    return results
