"""
LLM 프롬프트 생성기
TRD 11.2 / 11.3 / 11.4 기준 — yuna0822

각 분석 결과를 받아 LLM에게 전달할 System + User 프롬프트를 구성한다.
"""
from __future__ import annotations

from ..nlp.models import NLPAnalysisResult, ProcessedVOCInput
from ..scoring.models import LeadScoreResult
from ..context.models import ContextEnrichmentResult


SYSTEM_PROMPT = """\
당신은 LG전자 영업 전략 AI 어시스턴트입니다.
주어진 VOC(고객의 소리) 분석 데이터를 바탕으로 영업 담당자가 즉시 활용할 수 있는
구체적이고 실행 가능한 전략 인사이트를 한국어로 생성하세요.

출력 형식(JSON):
{
  "title": "인사이트 제목 (20자 이내)",
  "summary": "핵심 요약 (2~3문장)",
  "recommended_action": "권장 영업 액션 (구체적, 1~2문장)",
  "reasoning": "근거 설명 (NLP/스코어 데이터 기반, 2~3문장)",
  "confidence": 0.0~1.0
}
"""


def build_insight_prompt(
    nlp: NLPAnalysisResult,
    voc: ProcessedVOCInput,
    score: LeadScoreResult,
    context: ContextEnrichmentResult | None = None,
) -> tuple[str, str]:
    """
    System 프롬프트 + User 프롬프트 튜플 반환

    Args:
        nlp: NLP 분석 결과
        voc: 원본 VOC 입력
        score: Lead Score 산출 결과
        context: 외부 데이터 Context 결합 결과 (없으면 생략)

    Returns:
        (system_prompt, user_prompt)
    """
    context_section = ""
    if context and context.matches:
        ctx_types = list({m.context_type for m in context.matches})
        context_section = (
            f"\n## 외부 환경 데이터\n"
            f"- 연관 컨텍스트 유형: {', '.join(ctx_types)}\n"
            f"- Context 점수: {context.aggregated_context_score:.2f}\n"
            f"- 설명: {context.context_description}\n"
        )

    competitor_section = ""
    if nlp.competitor_mentions:
        brands = [b for b, c in nlp.competitor_mentions.items() if c > 0]
        if brands:
            competitor_section = (
                f"\n## 경쟁사 언급\n"
                f"- 언급된 브랜드: {', '.join(brands)}\n"
                f"- 비교 구매 의도: {'있음' if nlp.competitor_comparison_flag else '없음'}\n"
            )

    user_prompt = f"""\
## VOC 기본 정보
- VOC ID: {voc.id}
- 플랫폼: {voc.source}
- 제품군: {voc.product_category}
- 원문: {voc.normalized_text[:300]}{'...' if len(voc.normalized_text) > 300 else ''}

## NLP 분석 결과
- 감성: {nlp.sentiment_label} (점수: {nlp.sentiment_score:.2f})
- 구매 의도: {nlp.intent_label} (점수: {nlp.purchase_intent_score:.2f})
- 긴급도: {nlp.urgency_score:.2f}
- 주요 토픽: {nlp.topic_label or '미분류'}
- 불만 유형: {nlp.complaint_type or '없음'}
- 핵심 키워드: {', '.join(nlp.keywords[:5]) if nlp.keywords else '없음'}

## Lead Score
- 점수: {score.lead_score} / 100
- 우선순위: {score.priority}
- 주요 기여 요소: {', '.join(score.score_reason.top_factors)}
{competitor_section}{context_section}
위 데이터를 분석하여 영업 전략 인사이트를 JSON 형식으로 생성하세요.
"""
    return SYSTEM_PROMPT, user_prompt
