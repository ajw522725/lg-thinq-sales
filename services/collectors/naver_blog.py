"""
NaverBlogCollector — 네이버 블로그 VOC 수집기.

수집 전략:
  LIVE 모드
  ─────────
  1) [API 우선] Naver Search API (blog.json) 로 키워드 검색
       NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수 필요
  2) [Fallback] API 키 없으면 네이버 검색 결과 페이지 스크래핑
  3) 각 포스트의 iframe 본문 페이지(PostView.naver)에서 전문 수집
       .se-main-container / .se_publishDate / .se-title-text / .nick

  DEMO 모드
  ─────────
  USE_DEMO_DATA=true 시 장문 한국어 블로그 후기 샘플 10건 반환.
  구매 고민·설치 후기·라이프스타일·pain point 포함.

환경변수:
  USE_DEMO_DATA          true/false
  NAVER_CLIENT_ID        네이버 개발자센터 발급 키
  NAVER_CLIENT_SECRET    네이버 개발자센터 발급 키
"""
import os
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from services.collectors.base import BaseCollector

load_dotenv()

_NAVER_BLOG_SEARCH_URL = "https://openapi.naver.com/v1/search/blog.json"
_NAVER_SEARCH_FALLBACK_URL = "https://search.naver.com/search.naver"
_POSTVIEW_URL = "https://blog.naver.com/PostView.naver"

_HEADERS_PC = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def _parse_blog_url(link: str) -> tuple[Optional[str], Optional[str]]:
    """blog.naver.com/{blogId}/{logNo} 패턴에서 blogId, logNo를 추출한다."""
    m = re.search(r"blog\.naver\.com/([^/?#]+)/(\d+)", link)
    if m:
        return m.group(1), m.group(2)
    return None, None


class NaverBlogCollector(BaseCollector):
    """네이버 블로그 VOC 수집기."""

    RATE_LIMIT_MIN: float = 1.5
    RATE_LIMIT_MAX: float = 3.0

    def __init__(self):
        super().__init__(source_name="NaverBlog")
        self._client_id = os.getenv("NAVER_CLIENT_ID", "")
        self._client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        self._has_api_key = bool(self._client_id and self._client_secret)
        if self._has_api_key:
            self.logger.info("Naver Search API 키 감지 — API 우선 모드")
        else:
            self.logger.info("API 키 없음 — 검색 페이지 스크래핑 fallback 모드")

    # ── LIVE 수집 ──────────────────────────────────────────────────────────────

    def collect(self, keyword: str, max_items: int = 50) -> list[dict]:
        """
        네이버 블로그에서 keyword 검색 → 각 포스트 전문 수집.
        API 키 있으면 Naver Search API 사용, 없으면 검색 페이지 스크래핑.
        """
        post_links = (
            self._search_via_api(keyword, max_items)
            if self._has_api_key
            else self._search_via_web(keyword, max_items)
        )
        self.logger.info(f"블로그 포스트 링크 {len(post_links)}개 수집 | keyword={keyword!r}")

        results: list[dict] = []
        for item in post_links:
            if len(results) >= max_items:
                break
            self.rate_limiter.wait()
            doc = self._fetch_post(item, keyword)
            if doc:
                results.append(doc)

        return results

    # ── API 검색 ───────────────────────────────────────────────────────────────

    def _search_via_api(self, keyword: str, max_items: int) -> list[dict]:
        """Naver Search API로 블로그 포스트를 검색한다."""
        results = []
        display = min(max_items, 100)
        start = 1

        while len(results) < max_items:
            self.rate_limiter.wait()
            try:
                r = requests.get(
                    _NAVER_BLOG_SEARCH_URL,
                    params={"query": keyword, "display": display, "start": start, "sort": "date"},
                    headers={
                        "X-Naver-Client-Id": self._client_id,
                        "X-Naver-Client-Secret": self._client_secret,
                    },
                    timeout=10,
                )
                r.raise_for_status()
                data = r.json()
            except Exception as exc:
                self.logger.warning(f"Naver API 요청 실패: {exc}")
                break

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                link = item.get("link", "")
                if "blog.naver.com" not in link:
                    continue  # 외부 블로그 스킵
                results.append({
                    "link": link,
                    "title": re.sub(r"<[^>]+>", "", item.get("title", "")),
                    "description": re.sub(r"<[^>]+>", "", item.get("description", "")),
                    "bloggername": item.get("bloggername", ""),
                    "postdate": item.get("postdate", ""),  # YYYYMMDD
                })

            total = data.get("total", 0)
            start += display
            if start > min(total, 1000):
                break

        return results[:max_items]

    # ── 검색 페이지 스크래핑 fallback ──────────────────────────────────────────

    def _search_via_web(self, keyword: str, max_items: int) -> list[dict]:
        """네이버 검색 결과 페이지에서 블로그 포스트 링크를 스크래핑한다."""
        results = []
        seen: set[str] = set()

        for start in range(1, max_items + 1, 10):
            if len(results) >= max_items:
                break
            self.rate_limiter.wait()
            try:
                r = requests.get(
                    _NAVER_SEARCH_FALLBACK_URL,
                    params={"where": "blog", "query": keyword, "start": start, "sm": "tab_pge"},
                    headers=_HEADERS_PC,
                    timeout=12,
                )
                r.raise_for_status()
            except Exception as exc:
                self.logger.warning(f"검색 페이지 요청 실패: {exc}")
                break

            soup = BeautifulSoup(r.text, "html.parser")

            # 블로그 결과 링크 추출
            for a in soup.select('a[href*="blog.naver.com"]'):
                link = a.get("href", "")
                if not re.search(r"blog\.naver\.com/[^/?#]+/\d+", link):
                    continue
                if link in seen:
                    continue
                seen.add(link)

                # 제목과 설명 추출 — 링크 주변 텍스트
                parent = a.find_parent(class_=re.compile(r"(api_subject|total_tit|title|result)"))
                title = parent.get_text(strip=True)[:100] if parent else a.get_text(strip=True)

                results.append({
                    "link": link,
                    "title": title,
                    "description": "",
                    "bloggername": "",
                    "postdate": "",
                })
                if len(results) >= max_items:
                    break

            if not soup.select('a[href*="blog.naver.com"]'):
                break

        return results[:max_items]

    # ── 포스트 전문 수집 ───────────────────────────────────────────────────────

    def _fetch_post(self, item: dict, keyword: str) -> Optional[dict]:
        """
        포스트 URL에서 iframe 전문 페이지를 요청하여 본문·제목·날짜·작성자를 추출한다.
        """
        link = item["link"]
        blog_id, log_no = _parse_blog_url(link)
        if not blog_id or not log_no:
            return None

        try:
            r = requests.get(
                _POSTVIEW_URL,
                params={
                    "blogId": blog_id,
                    "logNo": log_no,
                    "redirect": "Dlog",
                    "widgetTypeCall": "true",
                    "noTrackingCode": "",
                },
                headers={**_HEADERS_PC, "Referer": link},
                timeout=15,
            )
            r.raise_for_status()
        except Exception as exc:
            self.logger.warning(f"포스트 수집 실패 {link}: {exc}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        content = self._extract_content(soup)
        if not content or len(content) < 50:
            return None

        title = self._extract_title(soup) or item.get("title") or ""
        author = self._extract_author(soup) or item.get("bloggername") or blog_id
        published_at = self._extract_date(soup, item.get("postdate", ""))

        return self.to_raw_document(
            content=content,
            title=title,
            url=link,
            author=author,
            published_at=published_at,
            external_id=f"{blog_id}_{log_no}",
            product_keyword=keyword,
            platform_meta={
                "blog_id": blog_id,
                "log_no": log_no,
                "bloggername": author,
                "description_snippet": item.get("description", "")[:200],
            },
        )

    @staticmethod
    def _extract_content(soup: BeautifulSoup) -> str:
        """스마트에디터(SE4) 또는 구버전 에디터에서 본문 텍스트를 추출한다."""
        # SE4 스마트에디터 (최신 네이버 블로그)
        container = soup.select_one(".se-main-container")
        if container:
            spans = container.select(".se-text-paragraph span, .se-text span")
            text = " ".join(s.get_text(strip=True) for s in spans if s.get_text(strip=True))
            if text:
                # 제로폭 공백 문자 제거
                return re.sub(r"[​‌‍﻿]+", "", text).strip()

        # 구버전 에디터 fallback
        post_area = soup.select_one("#postViewArea, .post-view, #post_1")
        if post_area:
            for tag in post_area.select("script, style, iframe"):
                tag.decompose()
            return post_area.get_text(separator=" ", strip=True)[:3000]

        return ""

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """포스트 제목을 추출한다."""
        el = soup.select_one(".se-title-text, .pcol1, h3.tit, .post_subject")
        if el:
            return el.get_text(strip=True)[:200]
        # og:title fallback
        og = soup.select_one('meta[property="og:title"]')
        return og.get("content", "")[:200] if og else ""

    @staticmethod
    def _extract_author(soup: BeautifulSoup) -> str:
        """블로거 닉네임을 추출한다."""
        el = soup.select_one(".nick, strong.nick, .blogger_name, .writer")
        return el.get_text(strip=True) if el else ""

    @staticmethod
    def _extract_date(soup: BeautifulSoup, postdate_str: str) -> Optional[datetime]:
        """
        포스트 발행일을 추출한다.
        우선순위: 페이지 내 날짜 요소 > API의 postdate > None
        """
        el = soup.select_one(".se_publishDate, span.se_publishDate, .post_date, .date")
        if el:
            raw = el.get_text(strip=True)  # "2026. 4. 16. 11:48"
            m = re.search(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})", raw)
            if m:
                try:
                    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                    tzinfo=timezone.utc)
                except ValueError:
                    pass

        # API postdate fallback: "YYYYMMDD"
        if postdate_str and len(postdate_str) == 8:
            try:
                return datetime.strptime(postdate_str, "%Y%m%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        return None

    # ── DEMO 데이터 ────────────────────────────────────────────────────────────

    def demo_data(self, keyword: str) -> list[dict]:
        """
        [DEMO] 실제 수집 없이 파이프라인 시연용 한국어 블로그 후기 샘플.
        구매 고민·라이프스타일 맥락·설치 경험·장기 사용 후기 포함.
        """
        samples = [
            {
                "id": "nb_001",
                "blog_id": "homemom2026",
                "log_no": "223900001",
                "title": "LG 휘센 에어컨 18평형 구매 후기 — 삼성이랑 고민하다 결국 LG로",
                "content": (
                    "안녕하세요, 오늘은 우리 집 거실에 설치한 LG 휘센 에어컨 구매 후기를 써볼게요. "
                    "사실 처음에는 삼성 에어컨이랑 엄청 비교를 많이 했어요. "
                    "유튜브 리뷰도 다 찾아보고, 다나와 후기도 수십 개 읽고 나서 결정한 거거든요. "
                    "삼성 비스포크랑 LG 휘센 오브제를 놓고 계속 갔다가 왔다가 했는데, "
                    "결국 LG로 결정한 이유는 듀얼 인버터 컴프레서 10년 보증이랑 "
                    "전기세 절약이 더 탁월하다는 리뷰들 때문이었어요. "
                    "설치는 빠르게 됐고 기사님도 친절하셨어요. "
                    "사용해보니 냉방 속도가 확실히 빠르고, "
                    "ThinQ 앱으로 집 오기 전에 미리 켜두면 들어오자마자 시원한 게 너무 좋아요. "
                    "전기세는 아직 한 달밖에 안 써서 모르겠지만 에너지 효율은 1등급이라 기대 중입니다. "
                    "단점은 실외기 소음이 가끔 신경 쓰일 때가 있어요. "
                    "전체적으로 만족스럽고 가격 대비 성능은 훌륭하다고 생각해요."
                ),
                "author": "홈맘이에요",
                "published_at": "2026-05-20T10:30:00Z",
                "postdate": "20260520",
                "blog_id_real": "homemom2026",
            },
            {
                "id": "nb_002",
                "blog_id": "first_home_2026",
                "log_no": "223900002",
                "title": "신혼집 가전 구성 완성! LG 냉장고 + 세탁기 패키지 구매기",
                "content": (
                    "드디어 신혼집 가전 세팅이 완성됐어요! "
                    "남편이랑 둘이서 가전 쇼핑을 몇 주 동안 했는데 정말 힘들었어요 ㅠㅠ "
                    "처음에는 삼성이냐 LG냐 엄청 싸웠는데 (웃음) "
                    "결국 냉장고는 LG 디오스 오브제, 세탁기는 LG 트롬 워시타워로 결정했어요. "
                    "패키지 구매 할인이 꽤 됐어요. 정가 대비 40만원 정도 할인받은 것 같아요. "
                    "냉장고는 836리터인데 둘이 쓰기엔 넘치지만 나중에 애기 생기면 딱이겠다 싶었어요. "
                    "노크온 기능이 처음엔 별거 아닌 줄 알았는데 야식 먹을 때 엄청 자주 쓰게 되네요 (웃음) "
                    "워시타워는 공간 절약이 진짜 짱이에요. "
                    "세탁 후 바로 건조까지 연결되니까 빨래 널 공간도 필요 없고 너무 편해요. "
                    "신혼부부에게 강력 추천합니다!"
                ),
                "author": "새댁일기",
                "published_at": "2026-05-18T14:00:00Z",
                "postdate": "20260518",
                "blog_id_real": "first_home_2026",
            },
            {
                "id": "nb_003",
                "blog_id": "airlover_dad",
                "log_no": "223900003",
                "title": "아이 천식 때문에 공기청정기 바꿨어요 — LG 퓨리케어 360 6개월 사용 후기",
                "content": (
                    "아이가 봄마다 천식이 심해지는데 미세먼지가 특히 문제였어요. "
                    "기존에 샤오미 제품을 쓰고 있었는데 솔직히 필터 교체 주기가 되면 "
                    "효과가 눈에 띄게 떨어지더라고요. 그래서 LG 퓨리케어 360으로 교체했어요. "
                    "가격 차이가 꽤 많이 나서 망설였는데 아이 건강을 생각하면 아깝지 않더라고요. "
                    "6개월 써본 결과, PM2.5 기준으로 눈에 띄게 개선됐어요. "
                    "앱에서 수치를 매일 확인할 수 있는 게 좋아요. "
                    "외출 후 돌아오면 앱이 자동으로 강풍 모드로 바뀌어 있는 것도 신기하고요. "
                    "필터 비용이 6개월에 5만원 정도 드는 건 단점이지만 "
                    "아이 알레르기 증상이 줄어든 걸 보니 충분히 가치 있는 투자인 것 같아요. "
                    "샤오미에서 LG로 갈아타길 잘했다는 생각이 드는 요즘입니다."
                ),
                "author": "세아빠",
                "published_at": "2026-05-15T09:00:00Z",
                "postdate": "20260515",
                "blog_id_real": "airlover_dad",
            },
            {
                "id": "nb_004",
                "blog_id": "renter_life",
                "log_no": "223900004",
                "title": "LG 에어컨 구독 케어 서비스 신청해봤어요 — 가입 후기 및 비용 정리",
                "content": (
                    "에어컨을 사서 쓰다 보면 여름마다 청소 문제가 고민이잖아요. "
                    "저도 매년 청소 업체 부르면 10만원 이상 드니까 올해는 LG 구독 케어 서비스를 "
                    "한번 써보기로 했어요. 월 1만9천원인데 연간으로 따지면 약 23만원이에요. "
                    "서비스 내용은 연 1회 전문 세척, 필터 자동 배송, AS 우선 접수예요. "
                    "청소만 따로 시키면 10만원 이상인데, 필터 비용이랑 AS 혜택까지 생각하면 "
                    "오히려 저렴하다고 생각했어요. "
                    "실제로 청소 기사님이 오셨는데 내부 분해 청소를 꼼꼼하게 해주셔서 만족스러웠어요. "
                    "에어컨 냄새가 확 사라졌고 냉방 효율도 좋아진 것 같아요. "
                    "렌탈이나 구독 서비스에 관심 있으신 분들은 한번 고려해보세요."
                ),
                "author": "렌탈생활자",
                "published_at": "2026-05-22T11:00:00Z",
                "postdate": "20260522",
                "blog_id_real": "renter_life",
            },
            {
                "id": "nb_005",
                "blog_id": "movein_diary",
                "log_no": "223900005",
                "title": "이사하면서 LG 냉장고 AS 경험 — 컴프레서 불량, 3주 기다린 후기",
                "content": (
                    "이사 후 2년 정도 된 LG 냉장고에서 이상한 소리가 나기 시작했어요. "
                    "처음엔 그냥 넘겼는데 냉기가 약해지더니 결국 냉동이 안 되더라고요. "
                    "LG 고객센터에 AS 신청을 했는데 방문까지 3주나 기다렸어요. "
                    "여름에 냉장고가 고장나면 진짜 패닉이잖아요. "
                    "기사님이 오셔서 보시더니 컴프레서 문제라고 하셨어요. "
                    "무상 수리 기간이라 비용은 안 들었지만 기다리는 동안 불편함이 너무 컸어요. "
                    "같은 기간 삼성 냉장고를 쓰는 이웃집은 AS가 3일 만에 됐다고 하더군요. "
                    "LG 제품 자체 품질은 나쁘지 않은데 AS 응대 속도가 개선됐으면 좋겠어요. "
                    "재구매 의사는 있지만 이번 경험으로 좀 망설여지는 게 사실입니다."
                ),
                "author": "이사요정",
                "published_at": "2026-05-12T16:00:00Z",
                "postdate": "20260512",
                "blog_id_real": "movein_diary",
            },
            {
                "id": "nb_006",
                "blog_id": "electricbill_hacks",
                "log_no": "223900006",
                "title": "올 여름 에어컨 전기세 절약 꿀팁 — LG ThinQ 앱 활용법",
                "content": (
                    "작년 여름에 에어컨 전기세가 30만원 넘게 나와서 진짜 충격 받았어요. "
                    "올해는 LG ThinQ 앱의 에너지 관리 기능을 제대로 활용해보기로 했어요. "
                    "AI 절전 모드를 켜두면 설정 온도 기준으로 자동 조절해줘서 "
                    "냉방 효율이 확실히 좋아졌어요. "
                    "외출 시엔 꺼두지 않고 26도로 올려두는 게 오히려 절전이 된다는 것도 알았고요. "
                    "최근 전기요금이 올라서 걱정이 많은데, "
                    "인버터 에어컨으로 교체하고 ThinQ 기능 잘 활용하면 확실히 차이가 나는 것 같아요. "
                    "이번 달 전기세는 전년 동기 대비 20% 정도 줄어든 것 같아서 뿌듯하네요."
                ),
                "author": "절약생활연구소",
                "published_at": "2026-05-19T08:00:00Z",
                "postdate": "20260519",
                "blog_id_real": "electricbill_hacks",
            },
            {
                "id": "nb_007",
                "blog_id": "newhouse_project",
                "log_no": "223900007",
                "title": "입주 청소 후 LG 공기청정기 필요성 절실히 느낌 — 구매 결정기",
                "content": (
                    "새 아파트에 입주했는데 새집 증후군이 생각보다 심했어요. "
                    "새 아파트 특유의 냄새랑 VOC 수치가 걱정되더라고요. "
                    "환기를 아무리 해도 냄새가 사라지지 않아서 결국 공기청정기를 사기로 했어요. "
                    "처음에는 블루에어랑 다이슨도 봤는데 "
                    "A/S 걱정 때문에 결국 LG 퓨리케어로 결정했어요. "
                    "국내 브랜드가 AS 면에서는 확실히 유리하잖아요. "
                    "사용해보니 앱에서 TVOC 수치가 '좋음'으로 내려오는 게 보여서 심리적으로 안심이 돼요. "
                    "PM2.5 뿐만 아니라 알레르겐 필터 기능도 있어서 "
                    "봄철 꽃가루 시즌에도 활약하더라고요. 입주 준비하시는 분들 강력 추천해요!"
                ),
                "author": "신축입주자",
                "published_at": "2026-05-23T07:30:00Z",
                "postdate": "20260523",
                "blog_id_real": "newhouse_project",
            },
            {
                "id": "nb_008",
                "blog_id": "apt_life_blog",
                "log_no": "223900008",
                "title": "LG 드럼세탁기 구매 3개월 후기 — 통돌이 오래 쓰다가 갈아탄 솔직 후기",
                "content": (
                    "10년 넘게 쓰던 통돌이 세탁기가 드디어 수명을 다해서 "
                    "드럼세탁기로 바꾸게 됐어요. LG 트롬 24kg으로 선택했는데요. "
                    "처음에 적응이 좀 필요했어요. 세탁 시간이 통돌이보다 길고, "
                    "코스 선택이 많아서 처음엔 헷갈렸거든요. "
                    "그래도 3개월 쓰면서 확실히 세탁력은 드럼이 훨씬 좋아요. "
                    "특히 이불이나 두꺼운 옷 세탁이 진짜 깔끔하게 돼요. "
                    "단점은 탈수 시 진동과 소음이 통돌이보다 좀 크게 느껴지고, "
                    "물을 적게 써서인지 세탁 후 향이 통돌이만 못한 것 같기도 해요. "
                    "전기세나 물값은 확실히 절약되는 것 같아서 장기적으론 이득인 것 같아요. "
                    "드럼으로 갈아타기 망설이시는 분들, 결국 후회 없는 선택이에요!"
                ),
                "author": "살림살이일기",
                "published_at": "2026-05-17T13:30:00Z",
                "postdate": "20260517",
                "blog_id_real": "apt_life_blog",
            },
            {
                "id": "nb_009",
                "blog_id": "dad_buys_home",
                "log_no": "223900009",
                "title": "장마철 제습기 추천 — LG 퓨리케어 50L 써봤어요",
                "content": (
                    "매년 장마철만 되면 집 안 습도가 80%를 넘어서 벽지에 곰팡이가 피고 "
                    "빨래도 안 마르고 진짜 힘들었어요. "
                    "이번에 드디어 LG 퓨리케어 제습기 50L를 샀는데 진짜 완전 달라졌어요! "
                    "하루 돌리면 물통이 꽉 찰 정도로 습기를 빨아들이는데, "
                    "일주일 후부터 집 분위기가 확 달라진 게 느껴지더라고요. "
                    "곰팡이 냄새가 사라지고 빨래도 실내에서 4시간이면 말라요. "
                    "기존에 위니아 제품을 쓰다가 LG로 바꿨는데 "
                    "소음은 비슷하고 제습 성능은 LG가 훨씬 낫다고 느꼈어요. "
                    "ThinQ 앱으로 원격 제어가 되는 것도 편하고요. "
                    "장마철 준비로 제습기 고민 중이신 분들, 강력 추천드려요."
                ),
                "author": "아빠의집꾸미기",
                "published_at": "2026-05-21T10:00:00Z",
                "postdate": "20260521",
                "blog_id_real": "dad_buys_home",
            },
            {
                "id": "nb_010",
                "blog_id": "tv_buff_2026",
                "log_no": "223900010",
                "title": "LG 올레드 TV 2년 사용 후기 — 번인 걱정 없이 잘 쓰고 있어요",
                "content": (
                    "LG 올레드 C2를 2년 째 쓰고 있어요. 가장 큰 걱정이 번인이었는데 "
                    "2년 동안 하루 5~6시간씩 써도 번인은 전혀 없어요. "
                    "OLED 케어 기능을 주기적으로 실행하고 있기도 하고요. "
                    "화질은 정말 말이 필요 없는데, 특히 영화 볼 때 블랙 표현이 너무 좋아요. "
                    "삼성 네오 QLED 쓰는 친구 집 가봤는데 "
                    "화사함은 삼성이 낫지만 몰입감은 올레드가 압도적인 것 같아요. "
                    "게임할 때 120Hz + 0.1ms 응답속도가 체감상 확실히 느껴지고요. "
                    "2년 된 지금도 전혀 불만 없이 만족스럽게 쓰고 있습니다. "
                    "올레드 살까 말까 고민 중인 분들, 결국 사고 나면 잘 샀다고 느낄 거에요!"
                ),
                "author": "TV덕후",
                "published_at": "2026-05-14T20:00:00Z",
                "postdate": "20260514",
                "blog_id_real": "tv_buff_2026",
            },
        ]

        results = []
        for s in samples:
            published_at = datetime.fromisoformat(s["published_at"].replace("Z", "+00:00"))
            doc = self.to_raw_document(
                content=s["content"],
                title=s["title"],
                url=f"https://blog.naver.com/{s['blog_id_real']}/{s['log_no']}",
                author=s["author"],
                published_at=published_at,
                external_id=s["id"],
                product_keyword=keyword,
                platform_meta={
                    "blog_id": s["blog_id_real"],
                    "log_no": s["log_no"],
                    "bloggername": s["author"],
                    "description_snippet": s["content"][:150],
                },
            )
            results.append(doc)

        return self.filter_demo_by_keyword(results, keyword)
