# Health Trend Report
> GC 헬스 트렌드 주간 리포트 외부 데이터 수집

구글 헬스 카테고리(cat=45) 상위 검색 키워드를 매일 수집하고,
해당 키워드로 Google News RSS 뉴스를 스크래핑해 CSV로 저장하는 파이썬 프로젝트입니다.

---

## 폴더 구조

```
health-trend-report/
├── data/                    # 수집 결과 CSV 저장 (날짜별 자동 생성)
│   ├── keywords_YYYYMMDD.csv
│   └── news_YYYYMMDD.csv
├── src/
│   ├── __init__.py
│   ├── trend_collector.py   # pytrends 키워드 수집 (KR, cat=45)
│   ├── news_scraper.py      # Google News RSS 뉴스 수집
│   └── csv_writer.py        # CSV 저장 유틸리티
├── main.py                  # 메인 실행 파일
├── requirements.txt
└── README.md
```

---

## 설치 방법

```bash
# 1. 가상환경 생성 (선택)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt
```

---

## 실행 방법

```bash
# 기본 실행 (오늘 날짜, 키워드 10개)
python main.py

# 키워드 15개 수집
python main.py --top 15

# 특정 날짜로 파일 저장
python main.py --date 20260225
```

---

## 출력 CSV 파일

### `data/keywords_YYYYMMDD.csv`

| 컬럼 | 설명 |
|------|------|
| date | 수집 날짜 |
| keyword | 트렌드 키워드 |
| source | 수집 출처 (trending / related_top / related_rising) |

### `data/news_YYYYMMDD.csv`

| 컬럼 | 설명 |
|------|------|
| date | 수집 날짜 |
| keyword | 검색 키워드 |
| rank | 기사 순위 (1~10) |
| title | 기사 제목 |
| source | 언론사 |
| published | 발행 일시 |
| url | 기사 URL |

---

## 자동화 (cron 예시)

매일 오전 8시에 자동 실행:

```bash
# crontab -e
0 8 * * * cd /path/to/health-trend-report && python main.py >> logs/cron.log 2>&1
```

---

## 주의사항

- Google Trends API는 비공식이므로 과도한 요청 시 일시적으로 차단될 수 있습니다.
- pytrends의 `related_queries`는 시드 키워드에 따라 결과가 달라질 수 있습니다.
- 수집 간격은 `trend_collector.py`의 `time.sleep(1.5)` 로 조절할 수 있습니다.
