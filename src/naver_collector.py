"""
네이버 데이터랩 검색트렌드 API로 헬스 관련 키워드 트렌드를 수집합니다.

API 문서: https://developers.naver.com/docs/serviceapi/datalab/search/search.md
"""

import logging
import os
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

NAVER_DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"

# 헬스 카테고리 키워드 그룹 (최대 5그룹 / 그룹당 최대 5키워드)
HEALTH_KEYWORD_GROUPS = [
    {"groupName": "건강검진",       "keywords": ["건강검진", "국가건강검진", "건강검진결과"]},
    {"groupName": "다이어트",       "keywords": ["다이어트", "체중감량", "칼로리"]},
    {"groupName": "운동·헬스",      "keywords": ["운동", "헬스", "피트니스", "홈트"]},
    {"groupName": "영양·건강기능식품", "keywords": ["영양제", "비타민", "건강기능식품", "유산균"]},
    {"groupName": "정신건강",       "keywords": ["우울증", "불안장애", "정신건강", "스트레스"]},
]


def _credentials() -> tuple[str, str]:
    client_id     = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise EnvironmentError(
            "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경변수가 없습니다. "
            ".env 파일을 확인해 주세요."
        )
    return client_id, client_secret


def fetch_naver_trends(
    keyword_groups: list[dict] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    time_unit: str = "date",
) -> list[dict]:
    """
    네이버 데이터랩 API로 키워드 그룹별 검색트렌드를 수집합니다.

    Args:
        keyword_groups: 키워드 그룹 목록 (None 이면 HEALTH_KEYWORD_GROUPS 사용)
        start_date:     조회 시작일 (None 이면 29일 전)
        end_date:       조회 종료일 (None 이면 오늘)
        time_unit:      집계 단위 ("date" | "week" | "month")

    Returns:
        [{"keyword_group": str, "period": str, "ratio": float}, ...]
    """
    client_id, client_secret = _credentials()

    keyword_groups = keyword_groups or HEALTH_KEYWORD_GROUPS
    end_date       = end_date   or date.today()
    start_date     = start_date or (end_date - timedelta(days=29))

    headers = {
        "X-Naver-Client-Id":     client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type":          "application/json",
    }
    body = {
        "startDate":    start_date.strftime("%Y-%m-%d"),
        "endDate":      end_date.strftime("%Y-%m-%d"),
        "timeUnit":     time_unit,
        "keywordGroups": keyword_groups,
    }

    resp = requests.post(NAVER_DATALAB_URL, headers=headers, json=body, timeout=10)
    resp.raise_for_status()

    records: list[dict] = []
    for result in resp.json().get("results", []):
        group_name = result.get("title", "")
        for point in result.get("data", []):
            records.append({
                "keyword_group": group_name,
                "period":        point["period"],
                "ratio":         point["ratio"],
            })

    logger.info(
        "네이버 트렌드 수집 완료: %d건 (%d개 그룹, %s ~ %s)",
        len(records), len(keyword_groups), start_date, end_date,
    )
    return records


def get_naver_keywords_for_csv(records: list[dict]) -> list[dict]:
    """
    네이버 트렌드 레코드에서 keywords CSV 에 추가할 행을 반환합니다.
    각 그룹의 가장 최근 날짜 ratio 를 대표값으로 사용합니다.

    Returns:
        [{"keyword": str, "source": "naver", "ratio": float}, ...]
    """
    latest: dict[str, float] = {}
    for r in records:
        latest[r["keyword_group"]] = r["ratio"]   # 뒤에 오는 날짜가 최신

    return [
        {"keyword": group, "source": "naver", "ratio": ratio}
        for group, ratio in latest.items()
    ]
