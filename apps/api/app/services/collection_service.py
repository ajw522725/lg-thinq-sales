from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from sqlalchemy.orm import Session

from app.repositories.voc_repository import ingest_voc_items
from app.schemas.domain import CollectionRunRequest, CollectionRunResponse
from services.collectors.runner import run_collection


ENGAGEMENT_KEYS = (
    "engagement",
    "view_count",
    "comment_count",
    "comments",
    "upvotes",
    "likes",
    "like_count",
    "helpful_count",
    "score",
    "num_comments",
)


def run_collector_pipeline(db: Session, request: CollectionRunRequest) -> CollectionRunResponse:
    """수집기를 실행하고 기존 DB pipeline으로 결과를 저장한다."""
    max_per_source = max(1, min(request.max_per_source, 50))
    keywords = request.keywords or ["LG air purifier"]
    sources = request.sources or ["Reddit"]

    with _collector_mode(live=request.live):
        result = run_collection(
            keywords=keywords,
            max_per_source=max_per_source,
            save=request.save,
            sources=sources,
        )

    payload = _map_raw_to_ingestion(result["raw"])
    seed_response = ingest_voc_items(db, payload, reset=request.reset) if payload else None
    stats = result["stats"]

    return CollectionRunResponse(
        seeded=True,
        raw_documents=seed_response.raw_documents if seed_response else 0,
        processed_documents=seed_response.processed_documents if seed_response else 0,
        insights=seed_response.insights if seed_response else 0,
        mode="live" if request.live else "demo",
        keywords=keywords,
        sources=stats.get("sources", sources),
        collector_raw=len(result["raw"]),
        ingestion_payload=len(payload),
        source_stats=stats.get("source_stats", {}),
    )


@contextmanager
def _collector_mode(live: bool) -> Iterator[None]:
    previous = os.environ.get("USE_DEMO_DATA")
    os.environ["USE_DEMO_DATA"] = "false" if live else "true"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("USE_DEMO_DATA", None)
        else:
            os.environ["USE_DEMO_DATA"] = previous


def _map_raw_to_ingestion(raw_docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fallback_ts = datetime.now(timezone.utc).isoformat()
    payload: list[dict[str, Any]] = []

    for index, raw in enumerate(raw_docs):
        content = str(raw.get("content") or "").strip()
        if not content:
            continue

        source = str(raw.get("source") or "Unknown").strip()
        external_id = str(raw.get("external_id") or f"{source.lower()}-{index}").strip()
        product_category = str(raw.get("product_category") or raw.get("product_keyword") or "Unknown").strip()

        payload.append(
            {
                "source": source,
                "external_id": external_id,
                "title": str(raw.get("title") or "Untitled VOC").strip(),
                "content": content,
                "url": str(raw.get("url") or "https://example.com/collector-voc").strip(),
                "published_at": _normalize_datetime(raw.get("published_at") or raw.get("collected_at"), fallback_ts),
                "product_category": product_category,
                "region": raw.get("region"),
                "engagement": _extract_engagement(raw),
                "author_hash": str(raw.get("author_hash") or "collector_demo_author"),
                "rating": _extract_rating(raw),
            }
        )

    return payload


def _extract_engagement(raw: dict[str, Any]) -> int:
    platform_meta = raw.get("platform_meta") or {}
    values = []
    for key in ENGAGEMENT_KEYS:
        values.append(_to_int(raw.get(key)))
        values.append(_to_int(platform_meta.get(key)))
    return sum(values)


def _extract_rating(raw: dict[str, Any]) -> int | None:
    platform_meta = raw.get("platform_meta") or {}
    parsed = _to_int(raw.get("rating", platform_meta.get("rating")))
    return parsed if parsed > 0 else None


def _normalize_datetime(value: Any, fallback: str) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str) and value.strip():
        return value
    return fallback


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
