"""
v1 라우터 — 모든 엔드포인트 통합
"""
from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.pipeline import router as pipeline_router
from app.api.v1.endpoints.nlp import router as nlp_router

router = APIRouter(prefix="/api/v1")

router.include_router(health_router)
router.include_router(pipeline_router)
router.include_router(nlp_router)
