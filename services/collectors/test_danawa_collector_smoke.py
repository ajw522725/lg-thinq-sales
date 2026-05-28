from __future__ import annotations

import os
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT_DIR = Path(__file__).parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("USE_DEMO_DATA", "false")

from services.collectors.danawa import DanawaCollector


def main() -> None:
    collector = DanawaCollector()
    collector.RATE_LIMIT_MIN = 0
    collector.RATE_LIMIT_MAX = 0

    product_html = """
    <li class="prod_item" id="productItem12345678">
      <p class="prod_name"><a href="https://prod.danawa.com/info/?pcode=12345678">LG 퓨리케어 공기청정기</a></p>
      <input id="min_price_12345678" value="490,000" />
      <input id="productItem_categoryInfo_12345678" value="생활가전_공기청정기" />
      <div class="spec_list">PM2.5 / Wi-Fi / ThinQ</div>
      <span class="text__score">4.8점</span>
      <span class="text__number">상품의견 312건</span>
    </li>
    """
    product = collector._parse_product_item(BeautifulSoup(product_html, "html.parser").select_one("li"), "LG 공기청정기")

    assert product is not None
    assert product["pcode"] == "12345678"
    assert product["price"] == 490000
    assert product["rating"] == 4.8
    assert product["review_count"] == 312

    review_html = """
    <li class="reviewItem">
      <strong class="review_title">미세먼지 심한 날 좋습니다</strong>
      <div class="review_cont">ThinQ 앱 연결도 잘 되고 공기질 수치가 빠르게 내려갑니다. 필터 가격은 조금 부담됩니다.</div>
      <span class="date">2026.05.20</span>
      <span class="star_score">평점 5점</span>
    </li>
    """
    doc = collector._parse_review_item(BeautifulSoup(review_html, "html.parser").select_one("li"), product)

    assert doc is not None
    assert doc["source"] == "Danawa"
    assert doc["external_id"].startswith("danawa-12345678-")
    assert doc["product_category"] == "공기청정기"
    assert doc["platform_meta"]["rating"] == 5.0
    assert doc["platform_meta"]["review_count"] == 312

    same_doc = collector._parse_review_item(BeautifulSoup(review_html, "html.parser").select_one("li"), product)
    assert same_doc is not None
    assert same_doc["external_id"] == doc["external_id"]

    print("Danawa collector parser smoke test 통과")


if __name__ == "__main__":
    main()
