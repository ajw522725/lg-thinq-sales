from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.collectors.runner import DEFAULT_KEYWORDS, run_collection


ENGAGEMENT_KEYS = (
    "engagement",
    "view_count",
    "comment_count",
    "comments",
    "upvotes",
    "likes",
    "like_count",
    "helpful_count",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="collector demo output을 FastAPI ingestion endpoint로 전송한다."
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "http://127.0.0.1:8000"),
        help="FastAPI 서버 URL. 기본값: http://127.0.0.1:8000",
    )
    parser.add_argument("--keyword", action="append", help="수집 키워드. 여러 번 지정 가능")
    parser.add_argument("--all-keywords", action="store_true", help="기본 키워드 전체 수집")
    parser.add_argument("--source", action="append", help="수집 source. 예: Danawa, Reddit, NaverBlog, YouTube")
    parser.add_argument("--max", type=int, default=2, help="소스당 최대 수집 건수")
    parser.add_argument("--limit", type=int, default=0, help="전송할 최대 VOC 수. 0이면 전체 전송")
    parser.add_argument("--reset", action="store_true", help="ingestion 전 기존 pipeline 데이터를 삭제")
    parser.add_argument("--live", action="store_true", help="USE_DEMO_DATA=false로 live collector 실행")
    parser.add_argument("--save", action="store_true", help="collector raw/processed JSONL 파일 저장")
    parser.add_argument("--dry-run", action="store_true", help="API 전송 없이 매핑 결과만 출력")
    parser.add_argument("--timeout", type=float, default=30.0, help="API 요청 timeout 초")
    return parser.parse_args()


def _select_keywords(args: argparse.Namespace) -> list[str]:
    if args.keyword:
        return args.keyword
    if args.all_keywords:
        return DEFAULT_KEYWORDS
    return ["LG 공기청정기"]


def _to_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        stripped = value.replace(",", "").strip()
        if stripped.isdigit():
            return int(stripped)
    return 0


def _extract_engagement(raw: dict[str, Any]) -> int:
    platform_meta = raw.get("platform_meta") or {}
    values = []
    for key in ENGAGEMENT_KEYS:
        values.append(_to_int(raw.get(key)))
        values.append(_to_int(platform_meta.get(key)))
    return sum(values)


def _extract_rating(raw: dict[str, Any]) -> int | None:
    platform_meta = raw.get("platform_meta") or {}
    rating = raw.get("rating", platform_meta.get("rating"))
    parsed = _to_int(rating)
    return parsed if parsed > 0 else None


def _normalize_datetime(value: Any, fallback: str) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str) and value.strip():
        return value
    return fallback


def _map_raw_to_ingestion(raw_docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fallback_ts = datetime.now(timezone.utc).isoformat()
    payload: list[dict[str, Any]] = []

    for index, raw in enumerate(raw_docs):
        content = str(raw.get("content") or "").strip()
        if not content:
            continue

        source = str(raw.get("source") or "Unknown").strip()
        external_id = str(raw.get("external_id") or f"{source.lower()}-{index}").strip()
        title = str(raw.get("title") or "Untitled VOC").strip()
        published_at = _normalize_datetime(raw.get("published_at") or raw.get("collected_at"), fallback_ts)

        payload.append(
            {
                "source": source,
                "external_id": external_id,
                "title": title,
                "content": content,
                "url": str(raw.get("url") or "https://example.com/demo-voc").strip(),
                "published_at": published_at,
                "product_category": str(raw.get("product_category") or "Unknown").strip(),
                "region": raw.get("region"),
                "engagement": _extract_engagement(raw),
                "author_hash": str(raw.get("author_hash") or "collector_demo_author"),
                "rating": _extract_rating(raw),
            }
        )

    return payload


def _post_ingestion(api_url: str, payload: list[dict[str, Any]], reset: bool, timeout: float) -> dict[str, Any]:
    endpoint = f"{api_url.rstrip('/')}/api/v1/ingestion/vocs"
    response = requests.post(endpoint, params={"reset": str(reset).lower()}, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected ingestion response: {data!r}")
    return data


def main() -> int:
    args = _parse_args()
    os.environ["USE_DEMO_DATA"] = "false" if args.live else "true"

    keywords = _select_keywords(args)
    result = run_collection(keywords, max_per_source=args.max, save=args.save, sources=args.source)
    payload = _map_raw_to_ingestion(result["raw"])
    if args.limit > 0:
        payload = payload[: args.limit]

    print("\n=== Collector ingestion demo ===")
    print(f"mode              : {'live' if args.live else 'demo'}")
    print(f"keywords          : {', '.join(keywords)}")
    print(f"sources           : {', '.join(result['stats'].get('sources', []))}")
    print(f"collector raw     : {len(result['raw'])}")
    print(f"ingestion payload : {len(payload)}")

    if not payload:
        print("전송할 VOC가 없습니다.")
        return 1

    if args.dry_run:
        first = payload[0]
        print("dry-run           : true")
        print(f"first source      : {first['source']}")
        print(f"first external_id : {first['external_id']}")
        print(f"first category    : {first['product_category']}")
        return 0

    response = _post_ingestion(args.api_url, payload, reset=args.reset, timeout=args.timeout)
    print(f"api url           : {args.api_url.rstrip('/')}")
    print(f"reset             : {args.reset}")
    print(f"raw_documents     : {response.get('raw_documents')}")
    print(f"processed_docs    : {response.get('processed_documents')}")
    print(f"insights          : {response.get('insights')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
