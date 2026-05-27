"""
경쟁사 언급 탐지 모듈
TRD 8.6 기준 경쟁사 사전 기반 탐지
"""
from __future__ import annotations

import re

from .models import CompetitorResult


# ──────────────────────────────────────────────
# 경쟁사 사전 (TRD 8.6)
# ──────────────────────────────────────────────
COMPETITOR_DICT: dict[str, list[str]] = {
    "samsung":   ["삼성", "samsung", "갤럭시홈"],
    "dyson":     ["다이슨", "dyson"],
    "xiaomi":    ["샤오미", "xiaomi", "미지아"],
    "whirlpool": ["월풀", "whirlpool"],
    "carrier":   ["캐리어", "carrier"],
    "winix":     ["위니아", "winix"],
    "coway":     ["코웨이", "coway"],
    "sk_magic":  ["SK매직", "sk magic"],
}

# 비교 문맥 키워드
COMPARISON_SIGNALS = ["보다", "vs", "비교", "대신", "instead", "switched", "compared", "versus", "rather than"]


def detect_competitors(text: str) -> CompetitorResult:
    """
    경쟁사 언급 탐지

    Args:
        text: 전처리된 텍스트

    Returns:
        CompetitorResult
    """
    text_lower = text.lower()

    mentions: dict[str, int] = {}
    for company, aliases in COMPETITOR_DICT.items():
        count = sum(len(re.findall(re.escape(alias.lower()), text_lower)) for alias in aliases)
        if count > 0:
            mentions[company] = count

    total = sum(mentions.values())

    # 비교 문맥 감지
    comparison_flag = False
    comparison_ctx: str | None = None
    if mentions:
        has_comparison = any(signal in text_lower for signal in COMPARISON_SIGNALS)
        if has_comparison:
            comparison_flag = True
            comparison_ctx = _extract_comparison_context(text, COMPETITOR_DICT, mentions)

    return CompetitorResult(
        competitor_mentions=mentions,
        competitor_comparison_flag=comparison_flag,
        comparison_context=comparison_ctx,
        total_mention_count=total,
    )


def _extract_comparison_context(text: str, competitor_dict: dict, mentions: dict) -> str:
    """경쟁사 언급 전후 50자를 비교 맥락으로 추출"""
    top_competitor = max(mentions, key=lambda k: mentions[k])
    aliases = competitor_dict.get(top_competitor, [])
    for alias in aliases:
        idx = text.lower().find(alias.lower())
        if idx != -1:
            start = max(0, idx - 30)
            end = min(len(text), idx + 50)
            return text[start:end].strip()
    return ""
