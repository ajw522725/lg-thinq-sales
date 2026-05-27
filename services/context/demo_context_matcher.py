from __future__ import annotations


def match_context(product_category: str, text: str, region: str | None) -> dict[str, str | float]:
    lower_text = text.lower()
    if product_category == "Air Purifier" or "fine dust" in lower_text or "미세먼지" in lower_text:
        return {"context_type": "air_quality", "region": region or "National", "match_reason": "air purifier/fine dust keyword", "match_score": 0.86}
    if product_category == "Air Conditioner" or "습도" in text or "cooling" in lower_text:
        return {"context_type": "weather", "region": region or "National", "match_reason": "air conditioner/weather keyword", "match_score": 0.82}
    if "energy" in lower_text or "전기" in text:
        return {"context_type": "energy", "region": region or "National", "match_reason": "energy efficiency keyword", "match_score": 0.74}
    if "이사" in text or "신혼" in text:
        return {"context_type": "housing", "region": region or "National", "match_reason": "moving/newlywed keyword", "match_score": 0.77}
    return {"context_type": "none", "region": region or "National", "match_reason": "no strong external context", "match_score": 0.2}
