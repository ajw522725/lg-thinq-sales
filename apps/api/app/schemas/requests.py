"""
API 요청 스키마
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class VOCRequest(BaseModel):
    """단일 VOC 분석 요청 — /pipeline/run, /nlp/analyze 공용"""
    text: str = Field(..., min_length=5, description="VOC 원문 텍스트")
    source: str = Field("unknown", description="플랫폼 (danawa, reddit, naver_blog, youtube, twitter)")
    language: str | None = Field(None, description="언어 코드 ko/en (없으면 자동 감지)")
    product_category: str = Field("general", description="제품군 (air_conditioner, air_purifier, ...)")
    product_keyword: str | None = Field(None, description="제품 키워드")
    rating: float | None = Field(None, ge=1.0, le=5.0, description="플랫폼 평점 1-5")
    engagement: int = Field(0, ge=0, description="좋아요+댓글 수")
    platform_meta: dict[str, Any] = Field(default_factory=dict)
