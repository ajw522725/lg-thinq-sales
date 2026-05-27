"""
Phase 6 스모크 테스트 — End-to-End 파이프라인
VOC → NLP → Lead Score → Strategy Insight 전체 흐름 검증
DEMO_MODE=true (API 키 불필요)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from services.nlp.models import DemoVOCItem
from services.nlp.pipeline import run_nlp_pipeline
from services.scoring.pipeline import run_lead_scoring
from services.insights.pipeline import generate_insight

DEMO_DATA_PATH = Path(__file__).parents[2] / "data" / "demo" / "sample_voc.json"


def main():
    print("=" * 70)
    print("LG ThinQ-Sales  End-to-End 파이프라인 스모크 테스트 (Phase 6)")
    print("VOC -> NLP -> Lead Score -> Strategy Insight")
    print("=" * 70)

    raw = json.loads(DEMO_DATA_PATH.read_text(encoding="utf-8"))
    items = [DemoVOCItem(**item) for item in raw]

    for item in items:
        voc = item.to_processed_voc()
        nlp = run_nlp_pipeline(voc)
        score = run_lead_scoring(nlp, voc)
        result = generate_insight(nlp, voc, score)
        ins = result.insight

        print(f"\n{'='*70}")
        print(f"[{item.id}]  {voc.source} / {voc.product_category}")
        print(f"  NLP    감성={nlp.sentiment_label:<8} 의도={nlp.intent_label:<6} "
              f"토픽={nlp.topic_label or '-'}")
        print(f"  Score  {score.lead_score:>5.1f}점  우선순위={score.priority}")
        print(f"  제목   {ins.title}")
        print(f"  요약   {ins.summary[:80]}{'...' if len(ins.summary) > 80 else ''}")
        print(f"  액션   {ins.recommended_action[:80]}{'...' if len(ins.recommended_action) > 80 else ''}")
        print(f"  신뢰도 {ins.confidence:.2f}  모델={ins.llm_model}")

    print(f"\n{'='*70}")
    print(f"총 {len(items)}개 VOC End-to-End 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
