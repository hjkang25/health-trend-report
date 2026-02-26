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

    반환 ratio는 기간(period)별 전체 그룹의 합이 100이 되도록 정규화됩니다.
    즉 ratio_i = (API raw ratio_i / Σ raw ratio_j) × 100 으로,
    같은 날짜의 그룹 간 점유율을 직접 비교할 수 있습니다.

    Args:
        keyword_groups: 키워드 그룹 목록 (None 이면 HEALTH_KEYWORD_GROUPS 사용)
        start_date:     조회 시작일 (None 이면 29일 전)
        end_date:       조회 종료일 (None 이면 오늘)
        time_unit:      집계 단위 ("date" | "week" | "month")

    Returns:
        [{"keyword_group": str, "period": str, "ratio": float}, ...]
        ratio 합계: 각 period 내 모든 그룹의 ratio 합 = 100
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
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate":   end_date.strftime("%Y-%m-%d"),
        "timeUnit":  time_unit,
    }

    # 네이버 API는 요청당 최대 5개 그룹만 허용한다.
    # 그룹이 5개를 초과하면 배치로 나눠 호출하되, 각 배치는 배치 내부에서
    # 독립적으로 정규화(배치 최대=100)되므로 배치 간 절대 비교는 불가능하다.
    # 5개 이하 단일 배치가 표준 사용 패턴이다.
    MAX_GROUPS_PER_REQUEST = 5
    batches = [
        keyword_groups[i : i + MAX_GROUPS_PER_REQUEST]
        for i in range(0, len(keyword_groups), MAX_GROUPS_PER_REQUEST)
    ]
    if len(batches) > 1:
        logger.warning(
            "키워드 그룹 수(%d)가 API 한도(5)를 초과하여 %d번 분할 요청합니다. "
            "배치 간 ratio는 서로 다른 기준으로 정규화되어 직접 비교가 불가능합니다.",
            len(keyword_groups), len(batches),
        )

    records: list[dict] = []
    for batch in batches:
        batch_body = {**body, "keywordGroups": batch}
        resp = requests.post(NAVER_DATALAB_URL, headers=headers, json=batch_body, timeout=10)
        resp.raise_for_status()

        for result in resp.json().get("results", []):
            group_name = result.get("title", "")
            for point in result.get("data", []):
                raw_ratio = float(point["ratio"])

                # 네이버 API는 요청 내 전체 그룹·기간의 최대 검색량=100으로
                # 정규화한다. 부동소수점 오차로 100을 미세하게 초과하는 경우
                # 경고 후 100.0으로 클램핑한다.
                if raw_ratio > 100.0:
                    logger.warning(
                        "API ratio가 100을 초과합니다 "
                        "(group=%s, period=%s, raw=%.5f). 100.0으로 클램핑.",
                        group_name, point["period"], raw_ratio,
                    )
                ratio = round(min(max(raw_ratio, 0.0), 100.0), 5)
                records.append({
                    "keyword_group": group_name,
                    "period":        point["period"],
                    "ratio":         ratio,
                })

    # ── 기간별 점유율 정규화 ─────────────────────────────────────────────────
    # 같은 period에 속한 모든 그룹의 raw ratio 합계를 구하고,
    # 각 그룹 ratio를 (ratio / 합계) × 100 으로 변환한다.
    # 결과: 특정 날짜의 전체 그룹 ratio 합 = 100 → 그룹 간 점유율 비교 가능.
    period_sums: dict[str, float] = {}
    for r in records:
        period_sums[r["period"]] = period_sums.get(r["period"], 0.0) + r["ratio"]

    for r in records:
        period_sum = period_sums[r["period"]]
        r["ratio"] = round(r["ratio"] / period_sum * 100.0, 5) if period_sum > 0 else 0.0

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
