"""
Google News RSS를 사용해 키워드별 뉴스 상위 10개를 수집합니다.
"""

import logging
import time
from urllib.parse import quote

import feedparser
import requests

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
MAX_ARTICLES = 10
REQUEST_DELAY = 1.0  # 요청 간 딜레이 (초)


def _build_rss_url(keyword: str) -> str:
    encoded = quote(keyword)
    return f"{GOOGLE_NEWS_RSS}?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"


def fetch_news(keyword: str, max_articles: int = MAX_ARTICLES) -> list[dict]:
    """
    Google News RSS에서 키워드 관련 뉴스를 수집합니다.

    Returns:
        [{"keyword", "rank", "title", "url", "source", "published"}, ...]
    """
    url = _build_rss_url(keyword)
    articles = []

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for rank, entry in enumerate(feed.entries[:max_articles], start=1):
            articles.append(
                {
                    "keyword": keyword,
                    "rank": rank,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "source": entry.get("source", {}).get("title", ""),
                    "published": entry.get("published", ""),
                }
            )

        logger.info("키워드 '%s': %d개 기사 수집", keyword, len(articles))
    except Exception as exc:
        logger.warning("뉴스 수집 실패 (keyword=%s): %s", keyword, exc)

    time.sleep(REQUEST_DELAY)
    return articles


def fetch_all_news(keywords: list[dict]) -> list[dict]:
    """
    키워드 목록 전체에 대해 뉴스를 수집합니다.

    Args:
        keywords: trend_collector.get_trending_health_keywords() 반환값
    Returns:
        모든 기사 목록
    """
    all_articles = []
    for item in keywords:
        articles = fetch_news(item["keyword"])
        all_articles.extend(articles)
    return all_articles
