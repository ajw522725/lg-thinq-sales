"""
앱 설정 — 환경변수 기반
"""
from __future__ import annotations
import os


class Settings:
    app_name: str = "LG ThinQ-Sales API"
    version: str = "0.1.0"

    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() == "true"
    llm_provider: str = os.getenv("LLM_PROVIDER", "demo")

    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
