from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

ROOT_DIR = Path(__file__).parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.context.demo_context_matcher import match_context
from services.context.matcher import fetch_and_match
from services.nlp.models import ProcessedVOCInput


def main() -> None:
    air_quality = match_context("공기청정기", "미세먼지가 심해서 공기청정기 필터 구독을 고민합니다.", "Seoul")
    assert air_quality["context_type"] == "air_quality"
    assert air_quality["region"] == "서울"
    assert air_quality["match_score"] >= 0.8
    assert air_quality["context_data"]["pm25"] == 22

    weather = match_context("Air Conditioner", "cooling performance and humidity are important", None)
    assert weather["context_type"] == "weather"
    assert weather["match_score"] >= 0.7

    voc = ProcessedVOCInput(
        id=uuid4(),
        raw_document_id=uuid4(),
        normalized_text="서울 미세먼지가 심해서 LG 공기청정기를 구매하려고 합니다.",
        product_category="공기청정기",
        source="NaverBlog",
        platform="blog",
        language="ko",
    )
    enriched = fetch_and_match(voc)
    assert enriched.aggregated_context_score > 0
    assert any(match.context_type == "air_quality" for match in enriched.matches)

    print("Context demo adapter smoke test 통과")


if __name__ == "__main__":
    main()
