"""
Phase 1 Step 2 — Lead Scoring 스모크 테스트
NLP 파이프라인 → Lead Score 연동 검증
pip install langdetect pydantic 후 실행 가능
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from services.nlp.models import DemoVOCItem
from services.nlp.pipeline import run_nlp_pipeline
from services.scoring.pipeline import run_lead_scoring

DEMO_DATA_PATH = Path(__file__).parents[2] / "data" / "demo" / "sample_voc.json"


def main():
    print("=" * 65)
    print("LG ThinQ-Sales  NLP → Lead Scoring 스모크 테스트")
    print("=" * 65)

    raw = json.loads(DEMO_DATA_PATH.read_text(encoding="utf-8"))
    items = [DemoVOCItem(**item) for item in raw]

    high_count = medium_count = low_count = 0

    for item in items:
        voc = item.to_processed_voc()
        nlp = run_nlp_pipeline(voc)
        score = run_lead_scoring(nlp, voc)

        if score.priority == "high":
            high_count += 1
        elif score.priority == "medium":
            medium_count += 1
        else:
            low_count += 1

        bd = score.score_reason
        print(f"\n[VOC {str(nlp.voc_id)[:8]}...]  source={voc.source}  product={voc.product_category}")
        print(f"  NLP  감성={nlp.sentiment_label:<8} 구매의도={nlp.intent_label:<6} 긴급도={nlp.urgency_score:.2f}")
        print(f"  Score {score.lead_score:>5.1f}점  우선순위={score.priority}")
        print(f"  근거  {bd.explanation}")

    print("\n" + "=" * 65)
    print(f"총 {len(items)}개 VOC 처리 완료")
    print(f"  High={high_count}  Medium={medium_count}  Low={low_count}")
    print("=" * 65)


if __name__ == "__main__":
    main()
