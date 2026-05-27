"""
발표용 데모 데이터셋 빌드 스크립트 (Day 3/4).

실행:
  python scripts/build_demo_dataset.py

생성물:
  data/demo/voc_demo_full.jsonl          — 전체 41건 정제 데이터
  data/demo/scenario_aircon.jsonl        — 에어컨 시나리오 (Day 4)
  data/demo/scenario_airpurifier.jsonl   — 공기청정기 시나리오 (Day 4)
  data/demo/manifest.json                — 데이터셋 메타정보
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services.collectors.runner import run_collection, DEFAULT_KEYWORDS
from services.preprocessing.cleaner import preprocess_batch

DEMO_DIR = _ROOT / "data" / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def _save_jsonl(docs: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False, default=str) + "\n")
    print(f"  저장: {path.name} ({len(docs)}건)")


def build() -> None:
    print("=== 발표용 데모 데이터셋 빌드 시작 ===\n")

    # 전체 키워드 수집
    result = run_collection(DEFAULT_KEYWORDS, max_per_source=50, save=False)
    all_processed = result["processed"]

    # 1) 전체 데이터셋
    _save_jsonl(all_processed, DEMO_DIR / "voc_demo_full.jsonl")

    # 2) 에어컨 시나리오 (Day 4)
    aircon_docs = [d for d in all_processed if d.get("product_category") == "에어컨"]
    _save_jsonl(aircon_docs, DEMO_DIR / "scenario_aircon.jsonl")

    # 3) 공기청정기 시나리오 (Day 4)
    ap_docs = [d for d in all_processed if d.get("product_category") == "공기청정기"]
    _save_jsonl(ap_docs, DEMO_DIR / "scenario_airpurifier.jsonl")

    # 4) manifest.json
    manifest = _build_manifest(all_processed, result["stats"])
    manifest_path = DEMO_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str))
    print(f"  저장: manifest.json")

    # 요약 출력
    print()
    print("=== 데이터셋 요약 ===")
    cats = Counter(d.get("product_category") or "미분류" for d in all_processed)
    for cat, cnt in cats.most_common():
        print(f"  {cat:<12} {cnt}건")
    print(f"\n  에어컨 시나리오: {len(aircon_docs)}건")
    print(f"  공기청정기 시나리오: {len(ap_docs)}건")
    print(f"\n  전체: {len(all_processed)}건")
    print("\n=== 완료 ===")


def _build_manifest(docs: list[dict], stats: dict) -> dict:
    cats = Counter(d.get("product_category") or "미분류" for d in docs)
    sources = Counter(d.get("source") for d in docs)
    langs = Counter(d.get("language") for d in docs)
    sentiments_available = sum(1 for d in docs if d.get("platform_meta", {}).get("rating"))
    competitors_all = [
        c for d in docs
        for c in d.get("platform_meta", {}).get("competitor_mentions", [])
    ]
    comp_counts = Counter(competitors_all)

    return {
        "dataset_name": "LG ThinQ-Sales VOC Demo Dataset",
        "version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "demo",
        "description": (
            "LG 가전 VOC 분석 플랫폼 시연용 데이터셋. "
            "다나와·Reddit·네이버 블로그·YouTube에서 수집한 리뷰/후기/댓글."
        ),
        "files": {
            "voc_demo_full.jsonl": {
                "description": "전체 정제 VOC 데이터",
                "count": len(docs),
            },
            "scenario_aircon.jsonl": {
                "description": "에어컨 시나리오 VOC",
                "count": cats.get("에어컨", 0),
            },
            "scenario_airpurifier.jsonl": {
                "description": "공기청정기 시나리오 VOC",
                "count": cats.get("공기청정기", 0),
            },
        },
        "statistics": {
            "total_documents": len(docs),
            "by_category": dict(cats.most_common()),
            "by_source": dict(sources.most_common()),
            "by_language": dict(langs.most_common()),
            "with_rating": sentiments_available,
            "competitor_mentions": dict(comp_counts.most_common(10)),
        },
        "schema": {
            "source": "수집 플랫폼 (Danawa/Reddit/NaverBlog/YouTube)",
            "title": "포스트/리뷰 제목",
            "content": "정규화된 VOC 본문",
            "normalized_text": "전처리된 본문 (content와 동일)",
            "content_hash": "중복 탐지용 해시 (SHA-256 앞 16자리)",
            "language": "언어 코드 (ko/en)",
            "product_category": "추론된 제품군",
            "product_keyword": "수집 시 사용된 검색어",
            "published_at": "원본 게시일 (ISO 8601)",
            "collected_at": "수집 시각 (ISO 8601)",
            "platform_meta": "플랫폼별 추가 메타데이터",
        },
        "keywords_used": DEFAULT_KEYWORDS,
        "collection_stats": stats,
    }


if __name__ == "__main__":
    build()
