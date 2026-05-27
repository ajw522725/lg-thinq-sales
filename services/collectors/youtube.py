"""
YouTubeCollector — YouTube Data API v3 기반 댓글 VOC 수집기.

수집 전략:
  LIVE 모드
  ─────────
  1) search.list 로 keyword 관련 LG 가전 영상 검색 (type=video)
  2) 각 영상에서 commentThreads.list 로 상위 댓글 수집
  3) 댓글 50자 미만 스킵 (의미 있는 VOC만 보존)

  DEMO 모드
  ─────────
  USE_DEMO_DATA=true 시 한국어/영어 혼합 댓글 샘플 10건 반환.

환경변수:
  USE_DEMO_DATA    true/false
  YOUTUBE_API_KEY  Google Cloud Console 발급 키
"""
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

from services.collectors.base import BaseCollector

load_dotenv()

_YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_YOUTUBE_COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
_MIN_COMMENT_LEN = 50


class YouTubeCollector(BaseCollector):
    """YouTube Data API v3 기반 댓글 VOC 수집기."""

    RATE_LIMIT_MIN: float = 0.5
    RATE_LIMIT_MAX: float = 1.5

    def __init__(self):
        super().__init__(source_name="YouTube")
        self._api_key = os.getenv("YOUTUBE_API_KEY", "")
        if not self._api_key and not self.use_demo:
            self.logger.warning("YOUTUBE_API_KEY 미설정 — LIVE 모드 사용 불가")

    # ── LIVE 수집 ──────────────────────────────────────────────────────────────

    def collect(self, keyword: str, max_items: int = 50) -> list[dict]:
        """keyword로 영상 검색 후 각 영상 댓글을 수집한다."""
        import requests

        if not self._api_key:
            self.logger.error("YOUTUBE_API_KEY 없음 — 수집 불가")
            return []

        video_ids = self._search_videos(keyword, max_videos=max(5, max_items // 10))
        self.logger.info(f"영상 {len(video_ids)}개 발견")

        results: list[dict] = []
        for vid in video_ids:
            if len(results) >= max_items:
                break
            self.rate_limiter.wait()
            comments = self._fetch_comments(vid["video_id"], vid, keyword,
                                            limit=max_items - len(results))
            results.extend(comments)

        return results

    def _search_videos(self, keyword: str, max_videos: int = 10) -> list[dict]:
        """YouTube search.list API로 관련 영상을 검색한다."""
        import requests
        results = []
        try:
            r = requests.get(
                _YOUTUBE_SEARCH_URL,
                params={
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "maxResults": min(max_videos, 50),
                    "relevanceLanguage": "ko",
                    "key": self._api_key,
                },
                timeout=10,
            )
            r.raise_for_status()
            for item in r.json().get("items", []):
                results.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                })
        except Exception as exc:
            self.logger.warning(f"영상 검색 실패: {exc}")
        return results

    def _fetch_comments(self, video_id: str, video_meta: dict,
                        keyword: str, limit: int = 20) -> list[dict]:
        """commentThreads.list API로 영상 댓글을 수집한다."""
        import requests
        results = []
        page_token: Optional[str] = None

        while len(results) < limit:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(100, limit - len(results)),
                "order": "relevance",
                "key": self._api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                self.rate_limiter.wait()
                r = requests.get(_YOUTUBE_COMMENTS_URL, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
            except Exception as exc:
                self.logger.warning(f"댓글 수집 실패 video={video_id}: {exc}")
                break

            for item in data.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                text = snippet.get("textOriginal", "").strip()
                if len(text) < _MIN_COMMENT_LEN:
                    continue

                author = snippet.get("authorDisplayName", "")
                published_raw = snippet.get("publishedAt", "")
                published_at = None
                if published_raw:
                    try:
                        published_at = datetime.fromisoformat(
                            published_raw.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                doc = self.to_raw_document(
                    content=text,
                    title=video_meta.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    author=author,
                    published_at=published_at,
                    external_id=item["id"],
                    product_keyword=keyword,
                    platform_meta={
                        "video_id": video_id,
                        "video_title": video_meta.get("title", ""),
                        "channel": video_meta.get("channel", ""),
                        "like_count": snippet.get("likeCount", 0),
                        "reply_count": item["snippet"].get("totalReplyCount", 0),
                    },
                )
                results.append(doc)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return results

    # ── DEMO 데이터 ────────────────────────────────────────────────────────────

    def demo_data(self, keyword: str) -> list[dict]:
        """
        [DEMO] 한국어·영어 혼합 YouTube 댓글 샘플 10건.
        에어컨·공기청정기·냉장고·세탁기·TV 시나리오 포함.
        """
        samples = [
            {
                "id": "yt_c001",
                "video_id": "demoAC001",
                "video_title": "LG 휘센 에어컨 실제 사용 후기 | 전기세 얼마나 나올까?",
                "channel": "살림왕TV",
                "content": (
                    "저도 LG 에어컨 쓰는데요, 24도로 맞춰두면 인버터가 알아서 조절해줘서 "
                    "전기세가 진짜 많이 줄었어요. 예전에 정속형 쓸 때랑 비교하면 거의 절반이에요. "
                    "ThinQ 앱이랑 연동하면 외출했다가 도착 20분 전에 켜두는 게 가능한데 "
                    "이게 진짜 너무 편해서 이제 없으면 못 살 것 같아요."
                ),
                "author": "user_homemom",
                "published_at": "2026-05-20T08:30:00Z",
                "like_count": 87,
            },
            {
                "id": "yt_c002",
                "video_id": "demoAC001",
                "video_title": "LG 휘센 에어컨 실제 사용 후기 | 전기세 얼마나 나올까?",
                "channel": "살림왕TV",
                "content": (
                    "소음이 좀 신경 쓰이긴 한데 삼성이랑 비교해봤을 때 냉방 효율은 "
                    "확실히 LG가 낫더라고요. 실외기 소음은 신축 아파트 기준 층간소음 민원 "
                    "들어온다는 얘기도 있어서 걱정했는데 우리 집은 괜찮았어요. "
                    "근데 가격이 너무 비싸진 거 아닌가요? 구독이나 렌탈도 알아봐야 할 것 같아요."
                ),
                "author": "user_reviewer99",
                "published_at": "2026-05-19T15:20:00Z",
                "like_count": 43,
            },
            {
                "id": "yt_c003",
                "video_id": "demoAP001",
                "video_title": "LG PuriCare 360 vs Xiaomi Air Purifier — Honest Comparison",
                "channel": "HomeGadgetKorea",
                "content": (
                    "I switched from Xiaomi to LG PuriCare last year and the difference "
                    "in PM2.5 sensor accuracy is noticeable. The Xiaomi under-reports by "
                    "about 20% based on my own measurements with an external sensor. "
                    "LG is definitely worth the premium if you have kids with allergies. "
                    "Filter cost is high but you can subscribe for auto-delivery."
                ),
                "author": "airquality_dad",
                "published_at": "2026-05-18T11:00:00Z",
                "like_count": 156,
            },
            {
                "id": "yt_c004",
                "video_id": "demoAP001",
                "video_title": "LG PuriCare 360 vs Xiaomi Air Purifier — Honest Comparison",
                "channel": "HomeGadgetKorea",
                "content": (
                    "미세먼지 150 넘어가는 날에도 실내 수치가 10 이하로 유지돼요. "
                    "아이 천식이 확실히 좋아진 것 같아서 비싸도 아깝지 않아요. "
                    "다이슨이랑도 비교해봤는데 필터 크기가 LG가 더 커서 "
                    "교체 주기가 길고 유지비가 저렴한 편이에요."
                ),
                "author": "user_parentseoul",
                "published_at": "2026-05-17T09:15:00Z",
                "like_count": 72,
            },
            {
                "id": "yt_c005",
                "video_id": "demoRF001",
                "video_title": "LG 디오스 냉장고 1년 사용 솔직 후기 — 좋은 점 나쁜 점",
                "channel": "주방가전리뷰",
                "content": (
                    "컴프레서 소음 문제는 저도 겪었는데 AS 기사님이 오셔서 "
                    "가스 재충전 하고 나서 해결됐어요. "
                    "문제는 그 과정에서 거의 한 달을 기다렸다는 거죠. "
                    "위니아 쓰던 친구는 AS가 이틀 만에 됐다는데 LG는 왜 이렇게 느린지 모르겠어요. "
                    "냉장 성능 자체는 만족스럽지만 AS는 진짜 개선이 필요해요."
                ),
                "author": "frustrated_user_kr",
                "published_at": "2026-05-16T14:00:00Z",
                "like_count": 201,
            },
            {
                "id": "yt_c006",
                "video_id": "demoWM001",
                "video_title": "LG 트롬 워시타워 6개월 실사용 리뷰",
                "channel": "신혼가전채널",
                "content": (
                    "신혼집에 워시타워 들인 게 진짜 신의 한 수예요. "
                    "세탁하고 나서 건조기로 이동하는 게 너무 편하고 "
                    "공간도 절반으로 줄어드니까요. "
                    "다만 건조 시간이 2~3시간으로 좀 길어서 "
                    "타이머 예약 기능 안 쓰면 불편할 수 있어요. "
                    "세탁력은 진짜 탁월합니다. 이불도 문제없어요."
                ),
                "author": "newly_wed_lg",
                "published_at": "2026-05-22T10:00:00Z",
                "like_count": 94,
            },
            {
                "id": "yt_c007",
                "video_id": "demoTV001",
                "video_title": "LG OLED C4 — 게이머가 말하는 진짜 솔직 후기",
                "channel": "게이밍라이프",
                "content": (
                    "PS5랑 연결해서 게임하는데 진짜 레벨이 다르네요. "
                    "삼성 QLED에서 갈아탔는데 블랙 표현이나 HDR이 비교 자체가 안 돼요. "
                    "번인 걱정은 OLED Care 기능으로 어느 정도 해소됐고, "
                    "2년 쓰는 동안 번인 없었다는 후기들이 많아서 믿고 샀는데 맞는 것 같아요. "
                    "120Hz에 0.1ms 응답속도, 게이머라면 이거 사야 해요."
                ),
                "author": "gamer_oled_kr",
                "published_at": "2026-05-14T21:30:00Z",
                "like_count": 312,
            },
            {
                "id": "yt_c008",
                "video_id": "demoAC002",
                "video_title": "LG ThinQ 앱 에너지 절약 설정 완벽 가이드",
                "channel": "스마트홈TV",
                "content": (
                    "영상에서 설명해주신 AI 절전 모드 켜고 나서 "
                    "전기세가 진짜 체감될 정도로 줄었어요. "
                    "전기요금 인상되는 거 보면서 걱정했는데 "
                    "인버터 에어컨이랑 ThinQ 앱 조합이면 그나마 관리 가능한 것 같아요. "
                    "구독 케어 서비스도 알아보는 중인데 비용 계산 좀 해봐야겠어요."
                ),
                "author": "thinq_user_82",
                "published_at": "2026-05-21T16:45:00Z",
                "like_count": 58,
            },
            {
                "id": "yt_c009",
                "video_id": "demoDH001",
                "video_title": "장마철 제습기 비교 — LG vs 위니아 vs 캐리어",
                "channel": "가전비교연구소",
                "content": (
                    "캐리어 제품도 써봤는데 제습 성능 자체는 LG가 확실히 위에 있어요. "
                    "소음은 세 제품이 비슷하고요. "
                    "ThinQ 앱 연동되는 게 LG만의 장점인데 "
                    "앱으로 외출 중에도 켜고 끌 수 있는 게 진짜 편해요. "
                    "가격은 LG가 비싸지만 장기적으로 보면 이득인 것 같아요."
                ),
                "author": "humid_hater_kr",
                "published_at": "2026-05-23T08:00:00Z",
                "like_count": 130,
            },
            {
                "id": "yt_c010",
                "video_id": "demoAP002",
                "video_title": "신축 아파트 입주 후 공기청정기 필수템 추천",
                "channel": "인테리어라이프",
                "content": (
                    "입주 후 새집증후군이 심해서 공기청정기 알아보다가 "
                    "결국 LG 퓨리케어로 결정했어요. "
                    "다이슨도 봤는데 다이슨은 공기청정기보다 선풍기 느낌이 강하고 "
                    "LG가 HEPA 필터 성능이나 사후 AS 면에서 낫다고 판단했어요. "
                    "TVOC 수치 모니터링이 앱에서 되는 게 심리적으로 안심이 돼요."
                ),
                "author": "new_apt_resident",
                "published_at": "2026-05-11T12:00:00Z",
                "like_count": 89,
            },
        ]

        results = []
        for s in samples:
            published_at = datetime.fromisoformat(s["published_at"].replace("Z", "+00:00"))
            doc = self.to_raw_document(
                content=s["content"],
                title=s["video_title"],
                url=f"https://www.youtube.com/watch?v={s['video_id']}",
                author=s["author"],
                published_at=published_at,
                external_id=s["id"],
                product_keyword=keyword,
                platform_meta={
                    "video_id": s["video_id"],
                    "video_title": s["video_title"],
                    "channel": s["channel"],
                    "like_count": s["like_count"],
                    "reply_count": 0,
                },
            )
            results.append(doc)

        return self.filter_demo_by_keyword(results, keyword)
