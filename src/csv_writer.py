"""
수집 결과를 날짜별 CSV 파일로 data/ 폴더에 저장합니다.
"""

import logging
from datetime import date
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_keywords(keywords: list[dict], run_date: date | None = None) -> Path:
    """
    수집된 키워드 목록을 CSV로 저장합니다.

    파일명: data/keywords_YYYYMMDD.csv
    """
    _ensure_data_dir()
    run_date = run_date or date.today()
    filename = DATA_DIR / f"keywords_{run_date.strftime('%Y%m%d')}.csv"

    df = pd.DataFrame(keywords)
    df.insert(0, "date", run_date.isoformat())
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    logger.info("키워드 저장 완료: %s (%d행)", filename, len(df))
    return filename


def save_news(articles: list[dict], run_date: date | None = None) -> Path:
    """
    수집된 뉴스 기사를 CSV로 저장합니다.

    파일명: data/news_YYYYMMDD.csv
    """
    _ensure_data_dir()
    run_date = run_date or date.today()
    filename = DATA_DIR / f"news_{run_date.strftime('%Y%m%d')}.csv"

    df = pd.DataFrame(articles)
    df.insert(0, "date", run_date.isoformat())
    # 컬럼 순서 정렬
    cols = ["date", "keyword", "rank", "title", "source", "published", "url"]
    df = df[[c for c in cols if c in df.columns]]
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    logger.info("뉴스 저장 완료: %s (%d행)", filename, len(df))
    return filename
