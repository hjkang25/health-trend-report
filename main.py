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
from src.naver_collector import fetch_naver_trends, get_naver_keywords_for_csv
from src.csv_writer import save_keywords, save_news, save_naver_trends

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

    # 1. Google 키워드 수집
    logger.info("[1/4] 구글 헬스 카테고리 키워드 수집 중... (top %d)", args.top)
    keywords = get_trending_health_keywords(top_n=args.top)

    if not keywords:
        logger.error("Google 키워드 수집 결과가 없습니다. 종료합니다.")
        sys.exit(1)

    # 2. 네이버 트렌드 수집 (API 키 없으면 건너뜀)
    logger.info("[2/4] 네이버 검색트렌드 수집 중...")
    naver_records: list[dict] = []
    try:
        naver_records = fetch_naver_trends()
        naver_kw_rows = get_naver_keywords_for_csv(naver_records)
        keywords = keywords + naver_kw_rows          # Google + Naver 통합
        naver_file = save_naver_trends(naver_records, run_date=run_date)
        logger.info("네이버 트렌드 저장: %s", naver_file)
    except EnvironmentError as e:
        logger.warning("네이버 수집 건너뜀 — %s", e)
    except Exception as e:
        logger.warning("네이버 API 오류 (건너뜀): %s", e)

    # 3. 키워드 CSV 저장 (Google + Naver 통합)
    kw_file = save_keywords(keywords, run_date=run_date)
    logger.info("키워드 저장: %s", kw_file)

    # 4. 뉴스 수집 (Google 키워드만 사용)
    logger.info("[3/4] 키워드별 뉴스 수집 중...")
    google_kws = [kw for kw in keywords if kw.get("source") != "naver"]
    articles = fetch_all_news(google_kws)

    if not articles:
        logger.warning("수집된 뉴스 기사가 없습니다.")
    else:
        news_file = save_news(articles, run_date=run_date)
        logger.info("뉴스 저장: %s", news_file)

    # 요약
    logger.info("=== 수집 완료 ===")
    logger.info("  Google 키워드: %d개", len(google_kws))
    logger.info("  Naver 트렌드 그룹: %d개", len(naver_records) // 30 if naver_records else 0)
    logger.info("  뉴스 기사: %d개", len(articles))
    logger.info("  저장 위치: data/")

    print("\n[수집 키워드 목록]")
    for i, item in enumerate(keywords, 1):
        ratio_str = f"  ratio={item['ratio']:.1f}" if item.get("ratio") is not None else ""
        print(f"  {i:>2}. {item['keyword']}  ({item['source']}){ratio_str}")


if __name__ == "__main__":
    main()
