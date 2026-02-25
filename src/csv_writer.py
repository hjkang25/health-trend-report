"""
수집 결과를 날짜별 CSV 파일로 data/ 폴더에 저장합니다.

keywords_YYYYMMDD.csv  - Google·Naver 통합 키워드 목록
news_YYYYMMDD.csv      - 키워드별 뉴스 기사
naver_trends_YYYYMMDD.csv - 네이버 검색트렌드 시계열
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
    Google 키워드(source != "naver")와 Naver 키워드(source == "naver")를
    함께 저장하며, Naver 행에는 ratio 컬럼이 추가됩니다.

    파일명: data/keywords_YYYYMMDD.csv
    컬럼:   date, keyword, source[, ratio]
    """
    _ensure_data_dir()
    run_date = run_date or date.today()
    filename = DATA_DIR / f"keywords_{run_date.strftime('%Y%m%d')}.csv"

    df = pd.DataFrame(keywords)
    df.insert(0, "date", run_date.isoformat())

    # ratio 컬럼이 없으면 추가 (Google 키워드만 있는 경우)
    if "ratio" not in df.columns:
        df["ratio"] = pd.NA

    cols = ["date", "keyword", "source", "ratio"]
    df = df[[c for c in cols if c in df.columns]]
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    logger.info("키워드 저장 완료: %s (%d행)", filename, len(df))
    return filename


def save_naver_trends(records: list[dict], run_date: date | None = None) -> Path:
    """
    네이버 검색트렌드 시계열 데이터를 CSV로 저장합니다.

    파일명: data/naver_trends_YYYYMMDD.csv
    컬럼:   collected_date, keyword_group, period, ratio
    """
    _ensure_data_dir()
    run_date = run_date or date.today()
    filename = DATA_DIR / f"naver_trends_{run_date.strftime('%Y%m%d')}.csv"

    df = pd.DataFrame(records)
    df.insert(0, "collected_date", run_date.isoformat())
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    logger.info("네이버 트렌드 저장 완료: %s (%d행)", filename, len(df))
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
