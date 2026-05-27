"""
DanawaCollector — 다나와 가전 리뷰 수집기.

수집 전략:
  LIVE 모드
  ─────────
  1) 검색 결과 페이지에서 상품 목록(pcode, 상품명, 스펙, 평점, 리뷰수) 파싱
  2) 각 상품에 대해 companyProductReview AJAX 엔드포인트로 리뷰 텍스트 시도
     - 로그인 세션 없으면 빈 응답 → 스킵 (조작 없음)
     - DANAWA_SESSION_COOKIE 환경변수에 세션쿠키 설정 시 풀 수집 가능
  3) Playwright fallback: 브라우저 설치 + DANAWA_USE_PLAYWRIGHT=true 시 활성화

  DEMO 모드
  ─────────
  USE_DEMO_DATA=true 시 실제 API 없이 한국어 샘플 리뷰 12건 반환.
  에어컨·냉장고·공기청정기·세탁기·건조기 시나리오 포함.

환경변수:
  USE_DEMO_DATA         true/false
  DANAWA_SESSION_COOKIE 다나와 로그인 쿠키 (선택, LIVE 모드 풀 수집용)
  DANAWA_USE_PLAYWRIGHT true/false (선택, Playwright 브라우저 설치 필요)
"""
import os
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from services.collectors.base import BaseCollector

load_dotenv()

_SEARCH_URL = "https://search.danawa.com/dsearch.php"
_REVIEW_AJAX_URL = "https://prod.danawa.com/info/dpg/ajax/companyProductReview.ajax.php"
_PRODUCT_BASE_URL = "https://prod.danawa.com/info/"

_HEADERS_BASE = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class DanawaCollector(BaseCollector):
    """다나와 상품 리뷰 수집기."""

    RATE_LIMIT_MIN: float = 2.0
    RATE_LIMIT_MAX: float = 4.0

    def __init__(self):
        super().__init__(source_name="Danawa")
        session_cookie = os.getenv("DANAWA_SESSION_COOKIE", "")
        self._session = requests.Session()
        self._session.headers.update(_HEADERS_BASE)
        if session_cookie:
            self._session.cookies.update(self._parse_cookie_str(session_cookie))
            self.logger.info("세션 쿠키 적용됨 — 로그인 상태로 리뷰 수집")
        self._use_playwright: bool = (
            os.getenv("DANAWA_USE_PLAYWRIGHT", "false").lower() == "true"
        )

    # ── LIVE 수집 ──────────────────────────────────────────────────────────────

    def collect(self, keyword: str, max_items: int = 50) -> list[dict]:
        """
        다나와에서 keyword로 상품 검색 후 각 상품의 리뷰를 수집한다.

        단계:
        1. 검색 결과 페이지에서 상품 목록 파싱
        2. 각 상품의 리뷰 AJAX 엔드포인트 호출
        3. Playwright 활성화 시 JS 렌더링으로 리뷰 전문 수집

        세션 쿠키 없으면 리뷰 텍스트는 수집되지 않음 (DANAWA_SESSION_COOKIE 설정 필요).
        """
        products = self._search_products(keyword, max_items=max_items * 2)
        self.logger.info(f"상품 {len(products)}개 발견 | keyword={keyword!r}")

        results: list[dict] = []

        for product in products:
            if len(results) >= max_items:
                break
            self.rate_limiter.wait()

            reviews = self._fetch_reviews(product)

            if reviews:
                results.extend(reviews[: max_items - len(results)])
            elif self._use_playwright:
                pw_reviews = self._collect_with_playwright(product, keyword)
                results.extend(pw_reviews[: max_items - len(results)])

        self.logger.info(
            f"리뷰 {len(results)}건 수집 완료 "
            f"(세션쿠키={'있음' if self._session.cookies else '없음'})"
        )
        return results

    def _search_products(self, keyword: str, max_items: int = 30) -> list[dict]:
        """검색 결과 페이지에서 상품 목록을 파싱한다."""
        products = []
        page = 1

        while len(products) < max_items:
            self.rate_limiter.wait()
            try:
                r = self._session.get(
                    _SEARCH_URL,
                    params={"query": keyword, "tab": "main", "page": page},
                    timeout=15,
                )
                r.raise_for_status()
            except Exception as exc:
                self.logger.warning(f"검색 페이지 요청 실패 (page={page}): {exc}")
                break

            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select("li.prod_item")
            if not items:
                break

            for item in items:
                product = self._parse_product_item(item, keyword)
                if product:
                    products.append(product)

            # 마지막 페이지 감지
            next_btn = soup.select_one("a.nav_next")
            if not next_btn or len(items) < 10:
                break
            page += 1

        return products[:max_items]

    def _parse_product_item(self, item, keyword: str) -> Optional[dict]:
        """검색 결과 li 항목에서 상품 메타데이터를 추출한다."""
        pcode_raw = item.get("id", "")
        if not pcode_raw.startswith("productItem"):
            return None
        pcode = pcode_raw.replace("productItem", "").strip()
        if not pcode.isdigit():
            return None

        name_el = item.select_one("p.prod_name a")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)

        price_el = item.select_one(f"input[id^=min_price_]")
        price = price_el.get("value") if price_el else None

        cat_el = item.select_one("input[id^=productItem_categoryInfo_]")
        category_raw = cat_el.get("value", "") if cat_el else ""

        spec_el = item.select_one(".spec_list")
        spec = spec_el.get_text(separator=" / ", strip=True) if spec_el else ""

        star_el = item.select_one(".text__score")
        rating = float(star_el.get_text(strip=True)) if star_el else None

        review_num_el = item.select_one(".text__number")
        review_count = 0
        if review_num_el:
            raw_num = re.sub(r"[^\d]", "", review_num_el.get_text(strip=True))
            review_count = int(raw_num) if raw_num else 0

        url = name_el.get("href", "")
        if not url.startswith("http"):
            url = _PRODUCT_BASE_URL + "?" + urlencode({"pcode": pcode})

        return {
            "pcode": pcode,
            "name": name,
            "price": int(price) if price and price.isdigit() else None,
            "category_raw": category_raw,
            "spec": spec,
            "rating": rating,
            "review_count": review_count,
            "url": url,
            "keyword": keyword,
        }

    def _fetch_reviews(self, product: dict) -> list[dict]:
        """
        companyProductReview AJAX 엔드포인트로 리뷰를 수집한다.
        로그인 세션 없으면 빈 리스트 반환.
        """
        pcode = product["pcode"]
        results = []

        for page in range(1, 4):  # 최대 3페이지
            try:
                self.rate_limiter.wait()
                r = self._session.get(
                    _REVIEW_AJAX_URL,
                    params={
                        "page": page, "limit": 10, "score": 0,
                        "sortType": "NEW", "onlyPhotoReview": 0,
                        "usefullScore": 0, "productCodes": pcode,
                        "pageType": "list",
                    },
                    headers={"Referer": f"{_PRODUCT_BASE_URL}?pcode={pcode}"},
                    timeout=15,
                )
                r.raise_for_status()
            except Exception as exc:
                self.logger.warning(f"리뷰 요청 실패 pcode={pcode}: {exc}")
                break

            soup = BeautifulSoup(r.text, "html.parser")

            if soup.select_one(".no_data"):
                break  # 더 이상 리뷰 없음

            review_items = soup.select("li[class*='reviewItem'], li.danawa-prodBlog-companyReview, .review_item")
            if not review_items:
                break

            for rev in review_items:
                doc = self._parse_review_item(rev, product)
                if doc:
                    results.append(doc)

            if len(review_items) < 10:
                break

        return results

    def _parse_review_item(self, item, product: dict) -> Optional[dict]:
        """리뷰 li 항목을 표준 RawDocument 포맷으로 변환한다."""
        content_el = item.select_one(".review_cont, .cont, [class*='content']")
        content = content_el.get_text(strip=True) if content_el else item.get_text(strip=True)
        if len(content) < 15:
            return None

        title_el = item.select_one(".review_title, .title, h4")
        title = title_el.get_text(strip=True) if title_el else product["name"]

        date_el = item.select_one(".date, .reg_date, [class*='date']")
        date_str = date_el.get_text(strip=True) if date_el else None
        published_at = self._parse_date(date_str)

        star_el = item.select_one(".star_score, .score, [class*='star']")
        star_score = None
        if star_el:
            m = re.search(r"(\d+\.?\d*)", star_el.get_text())
            star_score = float(m.group(1)) if m else None

        review_id_el = item.get("id") or item.get("data-seq") or ""

        doc = self.to_raw_document(
            content=content,
            title=title,
            url=product["url"],
            published_at=published_at,
            external_id=str(review_id_el) if review_id_el else None,
            product_keyword=product["keyword"],
            platform_meta={
                "pcode": product["pcode"],
                "product_name": product["name"],
                "rating": star_score,
                "product_rating": product.get("rating"),
                "review_count": product.get("review_count"),
                "price": product.get("price"),
                "spec": product.get("spec", "")[:200],
                "category_raw": product.get("category_raw", ""),
            },
        )
        return self._enrich_category(doc, product.get("category_raw", ""))

    # 다나와 카테고리 raw 값 → 표준 제품군 매핑
    _CATEGORY_RAW_MAP: dict[str, str] = {
        "에어컨": "에어컨", "냉방": "에어컨",
        "냉장고": "냉장고", "김치냉장고": "냉장고",
        "세탁기": "세탁기", "건조기": "세탁기",
        "공기청정기": "공기청정기",
        "제습기": "제습기",
        "청소기": "청소기",
        "식기세척기": "식기세척기",
        "전자레인지": "전자레인지",
        "TV": "TV", "OLED": "TV", "QNED": "TV", "모니터": "TV",
    }

    def _enrich_category(self, doc: dict, category_raw: str) -> dict:
        """
        detect_product_category()가 None을 반환했을 때
        category_raw(다나와 카테고리 문자열)로 product_category를 보완한다.
        """
        if doc.get("product_category"):
            return doc
        for key, mapped in self._CATEGORY_RAW_MAP.items():
            if key in category_raw:
                doc["product_category"] = mapped
                return doc
        return doc

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """다나와 날짜 문자열을 datetime으로 변환한다."""
        if not date_str:
            return None
        patterns = ["%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d", "%y.%m.%d"]
        for pat in patterns:
            try:
                return datetime.strptime(date_str.strip(), pat).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_cookie_str(cookie_str: str) -> dict:
        """'key=val; key2=val2' 형식 쿠키 문자열을 dict으로 변환한다."""
        result = {}
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, _, v = part.partition("=")
                result[k.strip()] = v.strip()
        return result

    def _collect_with_playwright(self, product: dict, keyword: str) -> list[dict]:
        """
        Playwright로 상품 페이지를 렌더링하여 리뷰를 수집한다.
        DANAWA_USE_PLAYWRIGHT=true + playwright 브라우저 설치 필요.
        브라우저 미설치 시 빈 리스트 반환.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return []

        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=_HEADERS_BASE["User-Agent"],
                    locale="ko-KR",
                )
                page = context.new_page()
                page.goto(
                    f"{_PRODUCT_BASE_URL}?pcode={product['pcode']}",
                    wait_until="networkidle",
                    timeout=30_000,
                )
                page.wait_for_timeout(2000)

                # 쇼핑몰 리뷰 탭 클릭
                try:
                    page.click("#danawa-prodBlog-productOpinion-button-tab-companyReview", timeout=5000)
                    page.wait_for_timeout(1500)
                except Exception:
                    pass

                html = page.content()
                browser.close()

            soup = BeautifulSoup(html, "html.parser")
            for rev in soup.select("li[class*='reviewItem'], li.cmt_item"):
                doc = self._parse_review_item(rev, product)
                if doc:
                    results.append(doc)
        except Exception as exc:
            self.logger.warning(f"Playwright 수집 실패 pcode={product['pcode']}: {exc}")

        return results

    # ── DEMO 데이터 ────────────────────────────────────────────────────────────

    def demo_data(self, keyword: str) -> list[dict]:
        """
        [DEMO] 실제 수집 없이 파이프라인 시연용 한국어 리뷰 샘플.
        에어컨·냉장고·공기청정기·세탁기·건조기 시나리오 포함.
        감성 긍/부/중립, 구매의도, 불만 유형 다양하게 구성.
        """
        samples = [
            # ── 에어컨 ─────────────────────────────────────────────────────
            {
                "id": "dw_ac_001",
                "product_name": "LG전자 휘센 AI 에어컨 FQ18GV3EA2",
                "pcode": "122627387",
                "title": "설치 다음날부터 진짜 더위 탈출!",
                "content": (
                    "처음엔 가격이 좀 부담됐는데 써보니 돈 아깝지 않네요. "
                    "전기세가 걱정돼서 인버터 제품으로 골랐는데, "
                    "지난달 전기요금이 예상보다 3만원 넘게 덜 나왔어요. "
                    "ThinQ 앱으로 외출 전에 미리 켜두면 집 들어올 때 딱 맞게 시원해져 있고 "
                    "AI 절전 모드도 꽤 똑똑하게 작동해요. "
                    "소음은 수면 모드 기준 거의 안 들려서 만족합니다."
                ),
                "rating": 5.0,
                "review_count": 405,
                "price": 890000,
                "category_raw": "계절가전_에어컨",
                "spec": "벽걸이 에어컨 / 냉방면적: 18평 / 인버터 / 듀얼인버터 / Wi-Fi",
                "published_at": "2026-05-20T10:15:00Z",
            },
            {
                "id": "dw_ac_002",
                "product_name": "LG전자 휘센 스탠드 에어컨 SQ20BDAWBS",
                "pcode": "41504753",
                "title": "소음 문제로 AS 두 번 불렀습니다",
                "content": (
                    "처음 설치 때부터 실외기 소음이 심해서 AS 신청했는데 "
                    "기사님이 정상 범위라고 하더라고요. "
                    "근데 옆집에서도 들린다는 말을 들을 정도로 시끄러워요. "
                    "냉방 성능 자체는 20평 거실도 30분이면 충분히 시원해지지만 "
                    "소음 때문에 별점 두 개 깎겠습니다. "
                    "삼성 제품이랑 비교했는데 냉방 효율은 LG가 낫고 소음은 삼성이 나은 것 같아요."
                ),
                "rating": 3.0,
                "review_count": 231,
                "price": 1250000,
                "category_raw": "계절가전_에어컨",
                "spec": "스탠드형 에어컨 / 냉방면적: 20평 / 인버터",
                "published_at": "2026-05-18T14:30:00Z",
            },
            {
                "id": "dw_ac_003",
                "product_name": "LG전자 휘센 벽걸이 에어컨 SQ06EZ1WBS",
                "pcode": "41504753",
                "title": "구독 서비스 가입할까 고민 중입니다",
                "content": (
                    "에어컨 구독 케어 서비스 광고를 보고 가입을 고려하고 있어요. "
                    "매년 청소비가 10만원 넘게 드는데 월 1만9천원이면 비슷한 것 같기도 하고요. "
                    "렌탈이랑 일시불 중에 뭐가 유리한지도 계산 중이에요. "
                    "냉방은 6평 방에서 완벽하게 잘 되고요, "
                    "에너지 소비효율 1등급 제품인데 실제로 전기세 차이가 있는지 궁금합니다."
                ),
                "rating": 4.0,
                "review_count": 89,
                "price": 510090,
                "category_raw": "계절가전_에어컨",
                "spec": "벽걸이 에어컨 / 6평 / 듀얼인버터 / 에너지 5등급",
                "published_at": "2026-05-22T09:00:00Z",
            },
            # ── 냉장고 ─────────────────────────────────────────────────────
            {
                "id": "dw_rf_001",
                "product_name": "LG전자 디오스 냉장고 S834MEE35",
                "pcode": "98321445",
                "title": "이사하면서 새로 장만했는데 대만족",
                "content": (
                    "신혼집에 들어오면서 처음으로 양문형 냉장고를 구입했어요. "
                    "LG 디오스 오브제 컬렉션인데 색상이 진짜 예쁘고 주방 인테리어랑 너무 잘 맞아요. "
                    "836리터 용량이라 두 명이 쓰기엔 넘치지만 나중을 위해 여유 있게 골랐어요. "
                    "InstaView 노크온 기능은 생각보다 자주 쓰게 됩니다. "
                    "배달비 포함해서 약 170만원인데 가성비 괜찮다고 생각해요."
                ),
                "rating": 5.0,
                "review_count": 156,
                "price": 1690000,
                "category_raw": "주방가전_냉장고",
                "spec": "양문형 / 836L / 노크온 / 오브제컬렉션",
                "published_at": "2026-05-15T11:20:00Z",
            },
            {
                "id": "dw_rf_002",
                "product_name": "LG전자 디오스 냉장고 R-H814PMSB",
                "pcode": "87452113",
                "title": "컴프레서 소음 AS 처리 너무 오래 걸렸어요",
                "content": (
                    "구매 8개월 만에 냉장고에서 윙윙 소리가 나기 시작했어요. "
                    "AS 신청을 했더니 3주 후에야 방문해서 황당했습니다. "
                    "기사님은 컴프레서 교체가 필요하다고 했고, 무상 수리였지만 "
                    "그동안 냉동식품을 다 버려야 했어요. "
                    "냉장 성능 자체는 문제없는데 AS 대응이 너무 느려서 실망스럽습니다. "
                    "위니아나 삼성은 이런 경우 어떤지 모르겠지만 경험 공유드려요."
                ),
                "rating": 2.0,
                "review_count": 78,
                "price": 1320000,
                "category_raw": "주방가전_냉장고",
                "spec": "일반형 양문 / 814L / 냉장고",
                "published_at": "2026-05-10T16:45:00Z",
            },
            # ── 공기청정기 ─────────────────────────────────────────────────
            {
                "id": "dw_ap_001",
                "product_name": "LG 퓨리케어 공기청정기 AS201VWNA",
                "pcode": "75123456",
                "title": "미세먼지 심한 날 진가를 발휘해요",
                "content": (
                    "요즘 공기질이 너무 안 좋아서 구입했어요. "
                    "PM2.5 수치가 35 이상일 때 자동으로 강풍으로 바뀌는데 "
                    "30분 안에 수치가 8 이하로 내려오더라고요. "
                    "ThinQ 앱에서 실시간으로 확인할 수 있어서 아이 있는 집에 딱이에요. "
                    "샤오미 제품도 봤는데 센서 정확도가 LG가 확실히 낫다는 후기를 믿고 골랐어요. "
                    "필터 교체 비용이 좀 부담이지만 성능으로 납득은 돼요."
                ),
                "rating": 5.0,
                "review_count": 312,
                "price": 490000,
                "category_raw": "생활가전_공기청정기",
                "spec": "공기청정기 / 54㎡ / PM2.5 / Wi-Fi / 자동운전",
                "published_at": "2026-05-19T08:30:00Z",
            },
            {
                "id": "dw_ap_002",
                "product_name": "LG 퓨리케어 360도 공기청정기 AS301VWFA",
                "pcode": "65432187",
                "title": "필터 냄새 이슈 있었지만 교체 후 해결",
                "content": (
                    "처음 받았을 때 플라스틱 냄새가 좀 났는데 "
                    "일주일 정도 가동하니 사라졌어요. "
                    "혹시나 해서 AS 문의했더니 초기 냄새는 정상이라고 하더군요. "
                    "그 이후엔 쾌적하게 잘 쓰고 있어요. "
                    "360도 흡입 방식이라 거실 한 가운데 놔도 어디서든 잘 되고요. "
                    "구독 필터 서비스 신청했더니 6개월마다 자동 배송돼서 편해요."
                ),
                "rating": 4.0,
                "review_count": 198,
                "price": 620000,
                "category_raw": "생활가전_공기청정기",
                "spec": "360도 공기청정기 / 62㎡ / 필터구독 가능",
                "published_at": "2026-05-17T13:10:00Z",
            },
            # ── 세탁기/건조기 ──────────────────────────────────────────────
            {
                "id": "dw_wm_001",
                "product_name": "LG전자 트롬 워시타워 WL21GUB",
                "pcode": "54321098",
                "title": "신혼집에 들였는데 공간 절약 끝판왕",
                "content": (
                    "원룸에서 투룸으로 이사하면서 세탁기와 건조기를 따로 사려다가 "
                    "워시타워로 결정했어요. 공간을 반도 안 차지하는 느낌이에요. "
                    "AI DD 기능이 빨래 무게를 감지해서 코스를 자동 추천해주는데 "
                    "처음엔 신기해서 계속 봤어요. 세탁 후 건조까지 2.5시간 걸리는 건 "
                    "단점이지만 타이머 예약 걸어두면 아침에 바로 꺼낼 수 있어요."
                ),
                "rating": 5.0,
                "review_count": 87,
                "price": 2190000,
                "category_raw": "생활가전_세탁기",
                "spec": "워시타워 / 세탁21kg 건조16kg / AI DD / Wi-Fi",
                "published_at": "2026-05-21T15:00:00Z",
            },
            {
                "id": "dw_wm_002",
                "product_name": "LG전자 트롬 드럼세탁기 F24WDWP",
                "pcode": "43219876",
                "title": "진동이 심해요, 세탁력은 좋지만",
                "content": (
                    "통돌이를 10년 쓰다가 드럼으로 바꿨어요. "
                    "세탁력은 드럼이 확실히 좋은데 탈수 시 진동이 심해서 "
                    "아랫집에 신경이 쓰여요. 수평 조절을 해봤는데도 그렇더라고요. "
                    "AS 기사님이 바닥 재질 문제일 수 있다고 했는데 "
                    "방진 매트 깔면 좀 나아진다고 하더군요. "
                    "세탁 용량은 24kg이라 이불 빨기에도 문제없어요."
                ),
                "rating": 3.0,
                "review_count": 65,
                "price": 1080000,
                "category_raw": "생활가전_세탁기",
                "spec": "드럼세탁기 / 24kg / 인버터 DD모터",
                "published_at": "2026-05-14T10:40:00Z",
            },
            # ── 제습기 ─────────────────────────────────────────────────────
            {
                "id": "dw_dh_001",
                "product_name": "LG 퓨리케어 오브제 제습기 UD501KOGR",
                "pcode": "32109876",
                "title": "장마철 지하창고 구세주",
                "content": (
                    "매년 장마 때 지하 창고에 곰팡이가 생겨서 고민이었는데 "
                    "이번에 제습기 하나 들여놨어요. "
                    "50L짜리인데 하루에 물통이 꽉 찰 정도로 제습이 잘 돼요. "
                    "습도를 50%로 설정해두면 알아서 조절해주고요. "
                    "예상보다 전기세 영향이 적어서 만족이에요. "
                    "오브제 디자인이라 거실에 내놔도 인테리어 해치지 않네요."
                ),
                "rating": 5.0,
                "review_count": 143,
                "price": 430000,
                "category_raw": "계절가전_제습기",
                "spec": "제습기 / 제습용량 50L/일 / Wi-Fi / 오브제컬렉션",
                "published_at": "2026-05-23T07:50:00Z",
            },
            # ── TV ────────────────────────────────────────────────────────
            {
                "id": "dw_tv_001",
                "product_name": "LG전자 올레드 TV OLED65C4KNA",
                "pcode": "21098765",
                "title": "4년 쓴 삼성 QLED에서 갈아탔습니다",
                "content": (
                    "삼성 QLED 65인치 쓰다가 결국 LG 올레드로 넘어왔어요. "
                    "블랙 표현이 정말 비교가 안 됩니다. 영화 볼 때 체감이 커요. "
                    "PS5 연결해서 게임할 때 응답속도 0.1ms는 확실히 느껴지고요. "
                    "번인 걱정이 있었는데 OLED 케어 기능이 있어서 어느 정도 커버된다고 해요. "
                    "가격이 좀 부담이지만 세일 때 잡아서 210만원에 구입했어요."
                ),
                "rating": 5.0,
                "review_count": 892,
                "price": 2100000,
                "category_raw": "TV_OLED",
                "spec": "OLED / 65인치 / 4K / 게이밍 / 0.1ms",
                "published_at": "2026-05-12T20:15:00Z",
            },
            {
                "id": "dw_tv_002",
                "product_name": "LG전자 QNED TV QNED75TQNA",
                "pcode": "10987654",
                "title": "올레드 살까 QNED 살까 고민했는데",
                "content": (
                    "올레드는 예산이 부족해서 QNED로 타협했어요. "
                    "솔직히 올레드에 비하면 블랙은 좀 아쉽지만 "
                    "밝은 방에서는 QNED가 오히려 더 잘 보이는 경우도 있어요. "
                    "75인치 기준 130만원대에 구매했는데 가성비는 최고입니다. "
                    "번인 걱정 없이 오래 쓸 수 있다는 것도 장점이에요."
                ),
                "rating": 4.0,
                "review_count": 234,
                "price": 1320000,
                "category_raw": "TV_QNED",
                "spec": "QNED / 75인치 / 4K / 120Hz",
                "published_at": "2026-05-08T18:30:00Z",
            },
        ]

        results = []
        for s in samples:
            published_at = datetime.fromisoformat(s["published_at"].replace("Z", "+00:00"))
            doc = self.to_raw_document(
                content=s["content"],
                title=s["title"],
                url=f"https://prod.danawa.com/info/?pcode={s['pcode']}",
                published_at=published_at,
                external_id=s["id"],
                product_keyword=keyword,
                platform_meta={
                    "pcode": s["pcode"],
                    "product_name": s["product_name"],
                    "rating": s["rating"],
                    "review_count": s["review_count"],
                    "price": s["price"],
                    "spec": s["spec"],
                    "category_raw": s["category_raw"],
                },
            )
            doc = self._enrich_category(doc, s["category_raw"])
            results.append(doc)

        return self.filter_demo_by_keyword(results, keyword)
