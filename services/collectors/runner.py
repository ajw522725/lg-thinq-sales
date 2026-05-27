"""
CollectionRunner — 전체 플랫폼 VOC 수집 + 전처리 + 파일 저장 오케스트레이터.

사용법:
  python -m services.collectors.runner --keyword "LG 에어컨" --max 50
  python -m services.collectors.runner --all-keywords

환경변수 USE_DEMO_DATA=true 시 모든 수집기가 demo 데이터를 반환한다.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트를 sys.path에 추가 (직접 실행 시)
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services.collectors.danawa import DanawaCollector
from services.collectors.naver_blog import NaverBlogCollector
from services.collectors.reddit import RedditCollector
from services.collectors.youtube import YouTubeCollector
from services.collectors.utils import get_logger
from services.preprocessing.cleaner import preprocess_batch

_logger = get_logger("runner")

# 수집 대상 키워드 (Phase 1 — 에어컨/공기청정기 중심)
DEFAULT_KEYWORDS = [
    "LG 에어컨",
    "LG 공기청정기",
    "LG 냉장고",
    "LG 세탁기",
    "LG 건조기",
]

_DATA_DIR = _ROOT / "data"
_RAW_DIR = _DATA_DIR / "raw"
_DEMO_DIR = _DATA_DIR / "demo"
_PROCESSED_DIR = _DATA_DIR / "processed"


def _ensure_dirs() -> None:
    for d in [_RAW_DIR, _DEMO_DIR, _PROCESSED_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def _save_jsonl(docs: list[dict], path: Path) -> None:
    """docs 목록을 JSONL 파일로 저장한다."""
    with open(path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False, default=str) + "\n")
    _logger.info(f"저장 완료: {path} ({len(docs)}건)")


def run_collection(
    keywords: list[str],
    max_per_source: int = 50,
    save: bool = True,
) -> dict:
    """
    모든 플랫폼에서 keywords로 VOC를 수집하고 전처리 후 저장한다.

    반환: { "raw": list[dict], "processed": list[dict], "stats": dict }
    """
    _ensure_dirs()

    collectors = [
        DanawaCollector(),
        RedditCollector(),
        NaverBlogCollector(),
        YouTubeCollector(),
    ]

    is_demo = os.getenv("USE_DEMO_DATA", "true").lower() == "true"
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    mode_label = "demo" if is_demo else "live"

    all_raw: list[dict] = []
    source_stats: dict[str, int] = {}

    for keyword in keywords:
        _logger.info(f"=== keyword: {keyword!r} ===")
        for collector in collectors:
            try:
                docs = collector.run(keyword=keyword, max_items=max_per_source)
                all_raw.extend(docs)
                source_stats[collector.source_name] = (
                    source_stats.get(collector.source_name, 0) + len(docs)
                )
            except Exception as exc:
                _logger.error(f"{collector.source_name} 수집 실패: {exc}")

    _logger.info(f"수집 완료 — 총 {len(all_raw)}건 (raw)")

    # 전처리
    result = preprocess_batch(all_raw, min_len=30)
    processed = result["processed"]
    preprocess_stats = result["stats"]

    _logger.info(
        f"전처리 완료 — 통과: {preprocess_stats['passed']}건 "
        f"| 품질 필터: {preprocess_stats['filtered_quality']}건 "
        f"| 중복 제거: {preprocess_stats['filtered_duplicate']}건"
    )

    # 저장
    if save:
        target_dir = _DEMO_DIR if is_demo else _RAW_DIR
        _save_jsonl(all_raw, target_dir / f"voc_raw_{run_ts}.jsonl")
        _save_jsonl(processed, _PROCESSED_DIR / f"voc_processed_{run_ts}.jsonl")

        # 최신 파일 심볼릭 업데이트 (latest.jsonl)
        for src, dst in [
            (target_dir / f"voc_raw_{run_ts}.jsonl", target_dir / "voc_raw_latest.jsonl"),
            (_PROCESSED_DIR / f"voc_processed_{run_ts}.jsonl", _PROCESSED_DIR / "voc_processed_latest.jsonl"),
        ]:
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            dst.symlink_to(src.name)

    summary = {
        "run_ts": run_ts,
        "mode": mode_label,
        "keywords": keywords,
        "source_stats": source_stats,
        "preprocess_stats": preprocess_stats,
        "raw_count": len(all_raw),
        "processed_count": len(processed),
    }

    _logger.info(f"소스별 수집량: {source_stats}")
    return {"raw": all_raw, "processed": processed, "stats": summary}


def _print_summary(stats: dict) -> None:
    print("\n" + "=" * 55)
    print(f"  수집 완료 — {stats['mode'].upper()} 모드  {stats['run_ts']}")
    print("=" * 55)
    print(f"  키워드: {', '.join(stats['keywords'])}")
    print(f"  총 수집 (raw)    : {stats['raw_count']}건")
    print(f"  전처리 통과      : {stats['processed_count']}건")
    print()
    print("  소스별 수집량:")
    for src, cnt in stats["source_stats"].items():
        print(f"    {src:<15} {cnt}건")
    print()
    ps = stats["preprocess_stats"]
    print(f"  품질 필터 제거   : {ps['filtered_quality']}건")
    print(f"  중복 제거        : {ps['filtered_duplicate']}건")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LG ThinQ-Sales VOC 수집 runner")
    parser.add_argument("--keyword", type=str, help="단일 키워드 수집")
    parser.add_argument("--all-keywords", action="store_true", help="기본 키워드 전체 수집")
    parser.add_argument("--max", type=int, default=50, help="소스당 최대 수집 건수")
    parser.add_argument("--no-save", action="store_true", help="파일 저장 생략")
    args = parser.parse_args()

    if args.keyword:
        keywords = [args.keyword]
    elif args.all_keywords:
        keywords = DEFAULT_KEYWORDS
    else:
        keywords = DEFAULT_KEYWORDS[:2]  # 기본: 에어컨 + 공기청정기

    result = run_collection(keywords, max_per_source=args.max, save=not args.no_save)
    _print_summary(result["stats"])
