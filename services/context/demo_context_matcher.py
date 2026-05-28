from __future__ import annotations

from datetime import datetime
from typing import Any

from services.context.demo_external_adapter import (
    build_demo_external_context,
    infer_context_type,
    score_context_match,
)


def match_context(
    product_category: str,
    text: str,
    region: str | None,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    context_type = infer_context_type(product_category, text)
    external_context = build_demo_external_context(context_type, region, observed_at)
    match_score, match_reason = score_context_match(context_type, product_category, text)

    return {
        "context_type": external_context["context_type"],
        "region": external_context["region"],
        "match_reason": match_reason,
        "match_score": round(match_score, 4),
        "context_summary": external_context["summary"],
        "context_data": external_context["data"],
        "source_name": external_context["source_name"],
        "observed_at": external_context["observed_at"],
    }
