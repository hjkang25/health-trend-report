"""
pytrends를 사용해 구글 한국(KR) Health 카테고리(cat=45) 상위 키워드를 수집합니다.
"""

import time
import logging
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

# 헬스 카테고리 탐색을 위한 시드 키워드
SEED_KEYWORDS = ["건강", "질병", "의료", "운동", "다이어트"]

# Google Trends 헬스 카테고리 코드
HEALTH_CATEGORY = 45


def get_trending_health_keywords(top_n: int = 10) -> list[dict]:
    """
    pytrends로 한국 헬스 카테고리 상위 키워드를 수집합니다.

    Returns:
        [{"keyword": str, "source": str}, ...]
    """
    pytrends = TrendReq(hl="ko", tz=540)  # KST (UTC+9)
    collected: dict[str, str] = {}  # keyword -> source

    # 1) 일간 트렌딩 검색어 (전체 카테고리)
    try:
        trending_df = pytrends.trending_searches(pn="south_korea")
        for kw in trending_df[0].tolist():
            collected.setdefault(kw, "trending")
        logger.info("trending_searches: %d개 수집", len(trending_df))
    except Exception as exc:
        logger.warning("trending_searches 실패: %s", exc)

    # 2) 헬스 카테고리 시드 키워드 기반 related_queries
    for seed in SEED_KEYWORDS:
        if len(collected) >= top_n * 3:
            break
        try:
            pytrends.build_payload(
                [seed],
                cat=HEALTH_CATEGORY,
                geo="KR",
                timeframe="now 1-d",
            )
            related = pytrends.related_queries()
            seed_data = related.get(seed, {})

            for query_type in ("top", "rising"):
                df = seed_data.get(query_type)
                if df is not None and not df.empty:
                    for kw in df["query"].tolist():
                        collected.setdefault(kw, f"related_{query_type}({seed})")

            time.sleep(1.5)  # 요청 제한 회피
        except Exception as exc:
            logger.warning("related_queries 실패 (seed=%s): %s", seed, exc)

    keywords = [
        {"keyword": kw, "source": src}
        for kw, src in list(collected.items())[:top_n]
    ]
    logger.info("최종 수집 키워드: %d개", len(keywords))
    return keywords
