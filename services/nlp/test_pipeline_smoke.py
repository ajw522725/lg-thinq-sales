"""
Phase 1 Step 1 — 스모크 테스트
pip install langdetect pydantic 후 실행 가능
"""
import sys
from pathlib import Path

# 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parents[2]))

from services.nlp.pipeline import run_pipeline_on_demo_data


def main():
    print("=" * 60)
    print("LG ThinQ-Sales NLP 파이프라인 스모크 테스트")
    print("=" * 60)

    results = run_pipeline_on_demo_data()

    for r in results:
        print(f"\n[VOC {r.voc_id}]")
        print(f"  감성     : {r.sentiment_label} (score={r.sentiment_score})")
        print(f"  구매의도  : {r.intent_label} (score={r.purchase_intent_score})")
        print(f"  불만유형  : {r.complaint_type or '-'}")
        print(f"  긴급도    : {r.urgency_score}")
        print(f"  토픽      : {r.topic_label or '-'}")
        print(f"  키워드    : {r.keywords[:5]}")
        print(f"  경쟁사    : {r.competitor_mentions or '-'}")

    print(f"\n총 {len(results)}개 VOC 분석 완료")


if __name__ == "__main__":
    main()
