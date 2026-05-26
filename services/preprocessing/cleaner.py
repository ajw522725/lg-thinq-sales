from __future__ import annotations

import re


URL_PATTERN = re.compile(r"https?://\S+")
HTML_PATTERN = re.compile(r"<[^>]+>")
SPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    cleaned = HTML_PATTERN.sub(" ", text)
    cleaned = URL_PATTERN.sub(" ", cleaned)
    cleaned = cleaned.replace("\u200b", " ")
    cleaned = SPACE_PATTERN.sub(" ", cleaned)
    return cleaned.strip()
