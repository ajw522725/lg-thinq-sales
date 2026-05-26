from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router

app = FastAPI(
    title="LG ThinQ-Sales API",
    version="0.1.0",
    description="Demo mode API for the LG ThinQ-Sales Phase 0 + Phase 1 MVP.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
