"""
헬스 트렌드 수집 메인 실행 파일

실행:
    python main.py            # 오늘 날짜로 수집
    python main.py --top 15   # 키워드 15개 수집
"""

import argparse
import logging
import sys
from datetime import date

# Windows 터미널 한글 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.trend_collector import get_trending_health_keywords
from src.news_scraper import fetch_all_news
from src.csv_writer import save_keywords, save_news

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="구글 헬스 카테고리 트렌드 수집기")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="수집할 키워드 수 (기본값: 10)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="저장 기준 날짜 YYYYMMDD (기본값: 오늘)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_date = date.today()
    if args.date:
        run_date = date.fromisoformat(
            f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:]}"
        )

    logger.info("=== 헬스 트렌드 수집 시작 (날짜: %s) ===", run_date)

    # 1. 키워드 수집
    logger.info("[1/3] 헬스 카테고리 키워드 수집 중... (top %d)", args.top)
    keywords = get_trending_health_keywords(top_n=args.top)

    if not keywords:
        logger.error("키워드 수집 결과가 없습니다. 종료합니다.")
        sys.exit(1)

    kw_file = save_keywords(keywords, run_date=run_date)
    logger.info("키워드 저장: %s", kw_file)

    # 2. 뉴스 수집
    logger.info("[2/3] 키워드별 뉴스 수집 중...")
    articles = fetch_all_news(keywords)

    if not articles:
        logger.warning("수집된 뉴스 기사가 없습니다.")
    else:
        news_file = save_news(articles, run_date=run_date)
        logger.info("뉴스 저장: %s", news_file)

    # 3. 요약
    logger.info("=== 수집 완료 ===")
    logger.info("  키워드: %d개", len(keywords))
    logger.info("  뉴스 기사: %d개", len(articles))
    logger.info("  저장 위치: data/")

    print("\n[수집 키워드 목록]")
    for i, item in enumerate(keywords, 1):
        print(f"  {i:>2}. {item['keyword']}  ({item['source']})")


if __name__ == "__main__":
    main()
