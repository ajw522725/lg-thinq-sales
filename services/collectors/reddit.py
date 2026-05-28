"""
RedditCollector — PRAW 기반 글로벌 VOC 수집기.

수집 대상:
  - r/homeappliances, r/Appliances, r/AirPurifiers, r/LGTV, r/Renovations,
    r/FirstTimeHomeBuyer, r/HomeImprovement 등 가전 관련 서브레딧
  - keyword 검색 (LG, product-specific terms)

LIVE 모드: REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET 필요
DEMO 모드: USE_DEMO_DATA=true 시 실제 API 없이 샘플 데이터 반환
"""
import os
from datetime import datetime, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

from services.collectors.base import BaseCollector

load_dotenv()

# 수집 대상 서브레딧 (VOC 관련성 높은 순)
_TARGET_SUBREDDITS = [
    "homeappliances",
    "Appliances",
    "AirPurifiers",
    "LGTV",
    "Renovations",
    "HomeImprovement",
    "FirstTimeHomeBuyer",
    "BuyItForLife",
    "frugal",
]

# 경쟁사 키워드 — NLP 전처리 전 빠른 탐지용
_COMPETITOR_KEYWORDS = [
    "samsung", "삼성", "dyson", "다이슨", "whirlpool",
    "xiaomi", "샤오미", "carrier", "캐리어", "winix", "위니아",
]


class RedditCollector(BaseCollector):
    """PRAW 또는 public JSON fallback을 이용한 Reddit VOC 수집기."""

    RATE_LIMIT_MIN: float = 1.5
    RATE_LIMIT_MAX: float = 3.0

    def __init__(self):
        super().__init__(source_name="Reddit")
        self._reddit = None  # lazy init — LIVE 모드에서만 생성
        self._timeout: float = float(os.getenv("REDDIT_REQUEST_TIMEOUT", "15"))
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": os.getenv(
                    "REDDIT_USER_AGENT", "lg-thinq-sales/1.0 by wldnjsrla085"
                ),
                "Accept": "application/json",
            }
        )

    # ── LIVE 수집 ──────────────────────────────────────────────────────────────

    def _has_praw_credentials(self) -> bool:
        return bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"))

    def _get_reddit_client(self):
        """PRAW 클라이언트를 lazy하게 초기화한다."""
        if self._reddit is None:
            import praw
            self._reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID", ""),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
                user_agent=os.getenv(
                    "REDDIT_USER_AGENT", "lg-thinq-sales/1.0 by wldnjsrla085"
                ),
            )
        return self._reddit

    def collect(self, keyword: str, max_items: int = 50) -> list[dict]:
        """
        Reddit 전체 검색 + 타깃 서브레딧에서 keyword로 포스트를 수집한다.

        전략:
        1. PRAW credentials가 있으면 reddit.subreddit("all").search(keyword)
        2. credentials가 없으면 public JSON search endpoint fallback
        3. 타깃 서브레딧 검색으로 부족분 보완
        중복은 external_id(post id) 기준으로 제거한다.
        """
        if not self._has_praw_credentials():
            self.logger.info("Reddit API credential 없음 — public JSON fallback 사용")
            return self._collect_with_public_json(keyword, max_items)

        reddit = self._get_reddit_client()
        seen_ids: set[str] = set()
        results: list[dict] = []

        # 1) 전체 검색
        try:
            for post in reddit.subreddit("all").search(
                keyword, sort="new", time_filter="month", limit=max_items
            ):
                self.rate_limiter.wait()
                if post.id in seen_ids:
                    continue
                seen_ids.add(post.id)
                doc = self._post_to_doc(post, keyword)
                if doc:
                    results.append(doc)
                if len(results) >= max_items:
                    break
        except Exception as exc:
            self.logger.warning(f"전체 검색 실패: {exc}")

        # 2) 타깃 서브레딧 top posts (부족할 때 보완)
        if len(results) < max_items:
            remaining = max_items - len(results)
            for sub_name in _TARGET_SUBREDDITS:
                if len(results) >= max_items:
                    break
                try:
                    sub = reddit.subreddit(sub_name)
                    for post in sub.search(keyword, sort="relevance", limit=remaining):
                        self.rate_limiter.wait()
                        if post.id in seen_ids:
                            continue
                        seen_ids.add(post.id)
                        doc = self._post_to_doc(post, keyword)
                        if doc:
                            results.append(doc)
                except Exception as exc:
                    self.logger.warning(f"r/{sub_name} 수집 실패: {exc}")

        return results

    def _collect_with_public_json(self, keyword: str, max_items: int) -> list[dict]:
        """API key 없이 public JSON endpoint로 Reddit 포스트를 수집한다."""
        seen_ids: set[str] = set()
        results: list[dict] = []

        endpoints = [("all", "https://www.reddit.com/search.json", {"q": keyword, "sort": "new", "t": "month"})]
        endpoints.extend(
            (
                sub_name,
                f"https://www.reddit.com/r/{sub_name}/search.json",
                {"q": keyword, "restrict_sr": "1", "sort": "relevance", "t": "year"},
            )
            for sub_name in _TARGET_SUBREDDITS
        )

        for source_name, url, params in endpoints:
            if len(results) >= max_items:
                break
            try:
                self.rate_limiter.wait()
                response = self._session.get(
                    url,
                    params={**params, "limit": max_items},
                    timeout=self._timeout,
                )
                if response.status_code in {403, 429}:
                    self.logger.warning(f"Reddit public JSON 제한 응답 source={source_name} status={response.status_code}")
                    continue
                response.raise_for_status()
                children = response.json().get("data", {}).get("children", [])
            except Exception as exc:
                self.logger.warning(f"Reddit public JSON 수집 실패 source={source_name}: {exc}")
                continue

            for child in children:
                raw = child.get("data", {})
                post_id = str(raw.get("id") or "").strip()
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                doc = self._json_post_to_doc(raw, keyword)
                if doc:
                    results.append(doc)
                if len(results) >= max_items:
                    break

        return results[:max_items]

    def _post_to_doc(self, post, keyword: str) -> Optional[dict]:
        """PRAW Submission 객체를 표준 RawDocument 포맷으로 변환한다."""
        content = post.selftext or post.title
        if len(content.strip()) < 20:  # 너무 짧은 포스트 제외
            return None

        lower = content.lower()
        competitors = [c for c in _COMPETITOR_KEYWORDS if c in lower]

        published_at = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)

        return self.to_raw_document(
            content=content,
            title=post.title,
            url=f"https://www.reddit.com{post.permalink}",
            author=str(post.author) if post.author else None,
            published_at=published_at,
            external_id=post.id,
            product_keyword=keyword,
            platform_meta={
                "subreddit": post.subreddit.display_name,
                "score": post.score,
                "num_comments": post.num_comments,
                "upvote_ratio": post.upvote_ratio,
                "flair": post.link_flair_text,
                "competitor_mentions": competitors,
            },
        )

    def _json_post_to_doc(self, raw: dict, keyword: str) -> Optional[dict]:
        """Reddit public JSON post dict를 표준 RawDocument 포맷으로 변환한다."""
        title = str(raw.get("title") or "").strip()
        selftext = str(raw.get("selftext") or "").strip()
        content = selftext or title
        if len(content) < 20:
            return None

        lower = f"{title} {content}".lower()
        competitors = [c for c in _COMPETITOR_KEYWORDS if c in lower]
        permalink = str(raw.get("permalink") or "")
        url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else str(raw.get("url") or "")
        created_utc = float(raw.get("created_utc") or 0)
        published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else datetime.now(timezone.utc)

        return self.to_raw_document(
            content=content,
            title=title or "Untitled Reddit VOC",
            url=url or "https://www.reddit.com",
            author=str(raw.get("author") or "") or None,
            published_at=published_at,
            external_id=str(raw.get("id")),
            product_keyword=keyword,
            platform_meta={
                "subreddit": raw.get("subreddit"),
                "score": int(raw.get("score") or 0),
                "num_comments": int(raw.get("num_comments") or 0),
                "upvote_ratio": float(raw.get("upvote_ratio") or 0),
                "flair": raw.get("link_flair_text"),
                "competitor_mentions": competitors,
                "collection_method": "public_json",
            },
        )

    # ── DEMO 데이터 ────────────────────────────────────────────────────────────

    def demo_data(self, keyword: str) -> list[dict]:
        """
        [DEMO] 실제 API 없이 파이프라인 시연용 샘플 데이터.
        에어컨·공기청정기·냉장고 시나리오 포함, 경쟁사 비교 반응 다수 포함.
        """
        samples = [
            {
                "id": "demo_r001",
                "title": "LG dual inverter AC vs Samsung — which one should I buy?",
                "content": (
                    "I'm torn between LG dual inverter and Samsung Wind-Free. "
                    "The LG seems more energy efficient based on reviews I've read, "
                    "but the Samsung has a better app interface. Budget is around $800. "
                    "Anyone have long-term experience with either? Leaning toward LG "
                    "because of the compressor warranty but not sure."
                ),
                "subreddit": "homeappliances",
                "score": 142,
                "num_comments": 67,
                "upvote_ratio": 0.94,
                "author": "user_hvac_curious",
                "published_at": "2026-05-20T14:32:00Z",
                "competitors": ["samsung"],
            },
            {
                "id": "demo_r002",
                "title": "LG PuriCare air purifier — 6 months review",
                "content": (
                    "Been using the LG PuriCare 360 for half a year in my apartment. "
                    "Pros: very quiet, the ThinQ app auto-adjusts based on air quality sensor. "
                    "Cons: replacement filters are expensive (~$50 each, every 6 months). "
                    "PM2.5 dropped from 35 to 8 on average. Worth it if you have allergies."
                ),
                "subreddit": "AirPurifiers",
                "score": 289,
                "num_comments": 104,
                "upvote_ratio": 0.97,
                "author": "clean_air_2026",
                "published_at": "2026-05-18T09:15:00Z",
                "competitors": [],
            },
            {
                "id": "demo_r003",
                "title": "My LG refrigerator compressor failed after 3 years — nightmare",
                "content": (
                    "LG linear compressor died on my French door fridge. "
                    "It's the 3rd time I've heard this happening to people in this sub. "
                    "LG extended the compressor warranty to 10 years after a class action, "
                    "but getting a repair scheduled took 3 weeks and the technician "
                    "was rude. Never buying LG again, switching to Whirlpool or Samsung."
                ),
                "subreddit": "Appliances",
                "score": 512,
                "num_comments": 231,
                "upvote_ratio": 0.89,
                "author": "frustrated_homeowner",
                "published_at": "2026-05-15T18:47:00Z",
                "competitors": ["samsung", "whirlpool"],
            },
            {
                "id": "demo_r004",
                "title": "Thinking about LG ThinQ subscription for HVAC — is it worth it?",
                "content": (
                    "LG is offering a subscription-based AC care plan in my area ($19/month). "
                    "Includes annual cleaning, filter replacement, and priority support. "
                    "Has anyone tried this? Comparing to just buying filters on Amazon. "
                    "The subscription seems expensive but my last AC service cost $200 "
                    "without the plan so maybe it makes sense?"
                ),
                "subreddit": "homeappliances",
                "score": 78,
                "num_comments": 43,
                "upvote_ratio": 0.92,
                "author": "thrifty_homemaker",
                "published_at": "2026-05-22T11:20:00Z",
                "competitors": [],
            },
            {
                "id": "demo_r005",
                "title": "LG OLED C4 TV — best purchase I've made this year",
                "content": (
                    "Finally pulled the trigger on the LG OLED C4 65 inch during the sale. "
                    "Coming from a 2018 Samsung QLED and the difference is night and day. "
                    "Blacks are incredible, gaming mode with 0.1ms response time is perfect. "
                    "The only downside is LG's WebOS ads but you can disable them. "
                    "If you're on the fence, just buy it."
                ),
                "subreddit": "LGTV",
                "score": 934,
                "num_comments": 312,
                "upvote_ratio": 0.98,
                "author": "tv_enthusiast_kr",
                "published_at": "2026-05-10T20:05:00Z",
                "competitors": ["samsung"],
            },
            {
                "id": "demo_r006",
                "title": "Moving into new apartment — LG washer/dryer combo or separate units?",
                "content": (
                    "Just signed a lease for a small studio. Space is tight so considering "
                    "LG WashTower vs their combo washer-dryer. The WashTower seems much better "
                    "for performance but costs $400 more. Anyone has experience with the combo? "
                    "Also looked at Dyson but they don't make washers lol. Main concern is "
                    "drying performance since combo units have a reputation for being slow."
                ),
                "subreddit": "FirstTimeHomeBuyer",
                "score": 156,
                "num_comments": 88,
                "upvote_ratio": 0.91,
                "author": "new_renter_2026",
                "published_at": "2026-05-23T07:30:00Z",
                "competitors": ["dyson"],
            },
            {
                "id": "demo_r007",
                "title": "LG PuriCare vs Xiaomi Mi Air Purifier — budget option worth it?",
                "content": (
                    "Living in Seoul and air quality has been terrible lately. "
                    "LG PuriCare costs 3x more than Xiaomi Mi 4 Pro. "
                    "The Xiaomi has decent specs but I've heard the sensors aren't as accurate. "
                    "Is the LG premium worth it for real PM2.5 performance? "
                    "My child has asthma so accuracy matters more than price."
                ),
                "subreddit": "AirPurifiers",
                "score": 203,
                "num_comments": 95,
                "upvote_ratio": 0.88,
                "author": "parent_seoul_air",
                "published_at": "2026-05-19T13:10:00Z",
                "competitors": ["xiaomi", "샤오미"],
            },
            {
                "id": "demo_r008",
                "title": "LG side-by-side refrigerator making loud noise — normal?",
                "content": (
                    "My 8-month old LG LRSOS2706S started making a humming noise last week. "
                    "It gets louder at night. Called LG support and they said it might be "
                    "the ice maker. Scheduled a technician but 2-week wait is frustrating. "
                    "Paid $1,800 for this fridge and already having issues. "
                    "Should I demand a replacement?"
                ),
                "subreddit": "Appliances",
                "score": 67,
                "num_comments": 51,
                "upvote_ratio": 0.85,
                "author": "noise_complaints_here",
                "published_at": "2026-05-21T16:45:00Z",
                "competitors": [],
            },
            {
                "id": "demo_r009",
                "title": "LG energy consumption — surprisingly good for an old model?",
                "content": (
                    "Running a 2021 LG split AC on a hot summer. My electricity bill went up "
                    "but less than I expected. The inverter tech seems to actually work — "
                    "bill was $40 less than my neighbor's Samsung unit of same capacity. "
                    "Setting auto-mode in the ThinQ app at 24°C seems to be the sweet spot. "
                    "Anyone else track their energy usage through the app?"
                ),
                "subreddit": "homeappliances",
                "score": 118,
                "num_comments": 37,
                "upvote_ratio": 0.96,
                "author": "energy_tracker_us",
                "published_at": "2026-05-17T08:22:00Z",
                "competitors": ["samsung"],
            },
            {
                "id": "demo_r010",
                "title": "Bought LG dehumidifier for basement — game changer",
                "content": (
                    "After three summers dealing with musty basement smell, finally got the "
                    "LG PuriCare dehumidifier 50-pint. Set it to 45% humidity and left it. "
                    "A week later, no more smell and the hygrometer confirms 44%. "
                    "Easy to empty, surprisingly quiet. Highly recommend if you have "
                    "basement humidity issues. Only gripe is the Wi-Fi setup was confusing."
                ),
                "subreddit": "HomeImprovement",
                "score": 387,
                "num_comments": 142,
                "upvote_ratio": 0.97,
                "author": "basement_fixer",
                "published_at": "2026-05-14T11:55:00Z",
                "competitors": [],
            },
        ]

        results = []
        for s in samples:
            published_at = datetime.fromisoformat(s["published_at"].replace("Z", "+00:00"))
            doc = self.to_raw_document(
                content=s["content"],
                title=s["title"],
                url=f"https://www.reddit.com/r/{s['subreddit']}/comments/{s['id']}/",
                author=s["author"],
                published_at=published_at,
                external_id=s["id"],
                product_keyword=keyword,
                platform_meta={
                    "subreddit": s["subreddit"],
                    "score": s["score"],
                    "num_comments": s["num_comments"],
                    "upvote_ratio": s["upvote_ratio"],
                    "flair": None,
                    "competitor_mentions": s["competitors"],
                },
            )
            results.append(doc)

        return self.filter_demo_by_keyword(results, keyword)
