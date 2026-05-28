"""
BaseCollector — 모든 VOC/SNS 수집기의 추상 기반 클래스.

하위 클래스 구현 의무:
  - collect()   : 실제 플랫폼에서 데이터를 수집하여 표준 포맷 리스트를 반환
  - demo_data() : USE_DEMO_DATA=true 일 때 반환할 샘플 데이터

공통 제공 기능:
  - run()             : demo 분기 + 에러 격리 실행
  - to_raw_document() : 표준 VOC 포맷 변환
  - rate_limiter      : 요청 간격 제어
  - logger            : 수집기별 로거
"""
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

from services.collectors.utils import (
    RateLimiter,
    detect_language,
    detect_product_category,
    get_logger,
    hash_author,
)

load_dotenv()


class BaseCollector(ABC):

    # 하위 클래스에서 덮어쓸 수 있는 기본 rate limit (초)
    RATE_LIMIT_MIN: float = 1.0
    RATE_LIMIT_MAX: float = 3.0

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.use_demo: bool = os.getenv("USE_DEMO_DATA", "true").lower() == "true"
        self.logger = get_logger(source_name)
        self.rate_limiter = RateLimiter(self.RATE_LIMIT_MIN, self.RATE_LIMIT_MAX)

    # ── 하위 클래스 구현 의무 ────────────────────────────────────────────────

    @abstractmethod
    def collect(self, keyword: str, max_items: int = 50) -> list[dict]:
        """
        실제 플랫폼에서 데이터를 수집한다.
        반드시 to_raw_document()를 통해 표준 포맷으로 반환해야 한다.
        """

    @abstractmethod
    def demo_data(self, keyword: str) -> list[dict]:
        """
        USE_DEMO_DATA=true 일 때 반환할 샘플 데이터.
        실제 API 없이 전체 파이프라인을 시연하기 위한 stub.
        """

    # ── 실행 진입점 ───────────────────────────────────────────────────────────

    def run(self, keyword: str, max_items: int = 50) -> list[dict]:
        """
        수집 실행 진입점.
        - demo 모드: demo_data() 반환
        - 실제 모드: collect() 실행, 실패해도 빈 리스트 반환 (파이프라인 중단 없음)
        """
        if self.use_demo:
            self.logger.info(f"[DEMO] {self.source_name} | keyword={keyword!r}")
            results = self.demo_data(keyword)[:max_items]
            self.logger.info(f"[DEMO] {len(results)}건 반환")
            return results

        self.logger.info(f"[START] {self.source_name} | keyword={keyword!r} | max={max_items}")
        try:
            results = self.collect(keyword, max_items)
            self.logger.info(f"[DONE] {self.source_name} | {len(results)}건 수집")
            return results
        except Exception as exc:
            # 단일 소스 실패가 전체 파이프라인을 멈추지 않도록 격리
            self.logger.error(f"[ERROR] {self.source_name} | {type(exc).__name__}: {exc}")
            return []

    # ── 표준 포맷 변환 ────────────────────────────────────────────────────────

    def to_raw_document(
        self,
        content: str,
        *,
        title: Optional[str] = None,
        url: Optional[str] = None,
        author: Optional[str] = None,
        published_at: Optional[datetime] = None,
        external_id: Optional[str] = None,
        product_keyword: Optional[str] = None,
        platform_meta: Optional[dict] = None,
        language: Optional[str] = None,
    ) -> dict:
        """
        수집 결과를 RawDocument 표준 포맷 dict으로 변환한다.

        - author는 자동으로 hash 처리 (개인정보 비식별화)
        - language는 명시하지 않으면 자동 감지
        - product_category는 content + title에서 자동 추론
        """
        combined_text = f"{title or ''} {content}"
        return {
            "source": self.source_name,
            "external_id": external_id,
            "title": title,
            "content": content,
            "url": url,
            "author_hash": hash_author(author),
            "published_at": (
                published_at.isoformat()
                if isinstance(published_at, datetime)
                else published_at
            ),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "language": language or detect_language(content),
            "product_keyword": product_keyword,
            "product_category": detect_product_category(combined_text),
            "platform_meta": platform_meta or {},
        }

    # ── 유틸리티 ─────────────────────────────────────────────────────────────

    # keyword → 우선 노출 카테고리 매핑
    _KEYWORD_CATEGORY_HINTS: dict[str, list[str]] = {
        "에어컨": ["에어컨"],
        "공기청정기": ["공기청정기"],
        "냉장고": ["냉장고"],
        "세탁기": ["세탁기", "건조기"],
        "건조기": ["세탁기", "건조기"],
        "제습기": ["제습기"],
        "청소기": ["청소기"],
        "tv": ["TV"],
        "올레드": ["TV"],
        "qned": ["TV"],
    }

    def filter_demo_by_keyword(self, docs: list[dict], keyword: str) -> list[dict]:
        """
        keyword에 해당하는 카테고리 문서를 앞에 배치한다.
        매칭 카테고리가 없으면 원본 순서 그대로 반환.
        """
        lower_kw = keyword.lower()
        priority_cats: list[str] = []
        for hint_kw, cats in self._KEYWORD_CATEGORY_HINTS.items():
            if hint_kw in lower_kw:
                priority_cats.extend(cats)

        if not priority_cats:
            return docs

        matched = [d for d in docs if d.get("product_category") in priority_cats]
        rest = [d for d in docs if d.get("product_category") not in priority_cats]
        return matched + rest

    def __repr__(self) -> str:
        mode = "DEMO" if self.use_demo else "LIVE"
        return f"<{self.__class__.__name__} source={self.source_name!r} mode={mode}>"
