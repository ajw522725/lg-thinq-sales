from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router
from app.core.config import settings
from app.db import models
from app.db.base import Base
from app.db.session import engine

app = FastAPI(
    title="LG ThinQ-Sales API",
    version="0.1.0",
    description="Demo mode API for the LG ThinQ-Sales Phase 0 + Phase 1 MVP.",
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
    Base.metadata.create_all(bind=engine)


app.include_router(router)
