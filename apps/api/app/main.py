"""
LG ThinQ-Sales FastAPI 앱 진입점
프로젝트 루트에서 실행:
  uvicorn apps.api.app.main:app --reload
또는:
  cd apps/api && uvicorn app.main:app --reload
"""
from __future__ import annotations

import sys
from pathlib import Path

# sys.path 설정
# parents[1] = apps/api/  → app.* 임포트 가능
# parents[3] = 프로젝트 루트 → services.* 임포트 가능
_API_DIR = Path(__file__).parents[1]
_ROOT = Path(__file__).parents[3]
for _p in [str(_ROOT), str(_API_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "LG ThinQ-Sales NLP/Insight API\n\n"
        "- `POST /api/v1/pipeline/run` — VOC 단일 분석 (NLP+Score+Insight)\n"
        "- `GET  /api/v1/demo/run`     — 데모 데이터 10건 일괄 분석\n"
        "- `POST /api/v1/nlp/analyze`  — NLP 분석만\n"
        "- `GET  /api/v1/health`       — 헬스체크\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
