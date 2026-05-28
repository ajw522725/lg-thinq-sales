from __future__ import annotations

import sys
from pathlib import Path

_API_DIR = Path(__file__).parents[1]
_ROOT = Path(__file__).parents[3]
for _path in [str(_ROOT), str(_API_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router
from app.core.config import settings
from app.db import models
from app.db.base import Base
from app.db.session import engine

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "LG ThinQ-Sales API\n\n"
        "- `POST /api/v1/demo/seed` — demo data DB seed\n"
        "- `POST /api/v1/ingestion/vocs` — collector VOC ingestion\n"
        "- `POST /api/v1/pipeline/run` — VOC 단일 분석(NLP+Score+Insight)\n"
        "- `GET /api/v1/demo/run` — yuna demo pipeline 실행\n"
        "- `POST /api/v1/nlp/analyze` — NLP 단독 분석\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)


app.include_router(router)
