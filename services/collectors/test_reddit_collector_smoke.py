from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("USE_DEMO_DATA", "false")

from services.collectors.reddit import RedditCollector


def main() -> None:
    collector = RedditCollector()
    raw = {
        "id": "abc123",
        "title": "LG PuriCare vs Samsung air purifier",
        "selftext": (
            "I am comparing LG PuriCare with Samsung because the air quality in my apartment "
            "has been bad. ThinQ looks useful, but filter subscription cost worries me."
        ),
        "permalink": "/r/AirPurifiers/comments/abc123/lg_puricare_vs_samsung/",
        "author": "air_user",
        "created_utc": 1779271200,
        "subreddit": "AirPurifiers",
        "score": 42,
        "num_comments": 11,
        "upvote_ratio": 0.93,
        "link_flair_text": "Buying Advice",
    }

    doc = collector._json_post_to_doc(raw, "LG air purifier")

    assert doc is not None
    assert doc["source"] == "Reddit"
    assert doc["external_id"] == "abc123"
    assert doc["product_category"] == "공기청정기"
    assert doc["platform_meta"]["collection_method"] == "public_json"
    assert "samsung" in doc["platform_meta"]["competitor_mentions"]
    assert doc["platform_meta"]["score"] == 42

    short_doc = collector._json_post_to_doc({"id": "short", "title": "LG", "selftext": ""}, "LG")
    assert short_doc is None

    irrelevant = collector._json_post_to_doc(
        {
            "id": "noise",
            "title": "A fantasy story about cooling fans",
            "selftext": "This is a long story about malware, cooling fans, filter rules, and a computer review mentioning LG once with no appliance VOC.",
        },
        "LG air purifier",
    )
    assert irrelevant is None

    print("Reddit collector JSON fallback smoke test 통과")


if __name__ == "__main__":
    main()
