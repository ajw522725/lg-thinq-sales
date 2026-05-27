"""
헬스체크 엔드포인트
"""
from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()


@router.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "demo_mode": os.getenv("DEMO_MODE", "true"),
        "llm_provider": os.getenv("LLM_PROVIDER", "demo"),
        "version": "0.1.0",
    }
