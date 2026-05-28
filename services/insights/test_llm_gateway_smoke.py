from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.insights.llm_client import call_llm


def main() -> None:
    os.environ["DEMO_MODE"] = "true"
    os.environ["LLM_PROVIDER"] = "demo"
    demo = call_llm(
        "system",
        "user",
        priority="high",
        nlp_context={
            "topic_id": "air_quality",
            "sentiment_label": "neutral",
            "keywords": ["미세먼지", "공기청정기"],
            "competitor_mentions": {},
            "product_category": "공기청정기",
            "urgency_score": 0.2,
        },
    )
    assert demo["_llm_provider"] == "demo"
    assert demo["_llm_model"] == "demo-rule-generator"
    assert demo["_llm_is_demo"] is True
    assert demo["title"]
    assert 0 <= demo["confidence"] <= 1

    os.environ["DEMO_MODE"] = "false"
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["LLM_FALLBACK_TO_DEMO"] = "true"
    fallback = call_llm("system", "user", priority="medium", nlp_context={})
    assert fallback["_llm_provider"] == "openai"
    assert fallback["_llm_model"] == "demo-rule-generator"
    assert fallback["_llm_is_demo"] is True
    assert fallback.get("_fallback_reason")

    print("LLM gateway smoke test 통과")


if __name__ == "__main__":
    main()
