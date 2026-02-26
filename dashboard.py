"""
Health Trend Dashboard

실행:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Health Trend Dashboard",
    page_icon="🏥",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"


# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """keywords / news / naver_trends CSV를 일괄 로드합니다."""
    kw_files     = sorted(DATA_DIR.glob("keywords_*.csv"))
    news_files   = sorted(DATA_DIR.glob("news_*.csv"))
    naver_files  = sorted(DATA_DIR.glob("naver_trends_*.csv"))

    kw_df = (
        pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in kw_files], ignore_index=True)
        if kw_files
        else pd.DataFrame(columns=["date", "keyword", "source", "ratio"])
    )
    news_df = (
        pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in news_files], ignore_index=True)
        if news_files
        else pd.DataFrame(columns=["date", "keyword", "rank", "title", "source", "published", "url"])
    )
    naver_df = (
        pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in naver_files], ignore_index=True)
        if naver_files
        else pd.DataFrame(columns=["collected_date", "keyword_group", "period", "ratio"])
    )

    if not kw_df.empty:
        kw_df["date"] = pd.to_datetime(kw_df["date"]).dt.date
        if "ratio" not in kw_df.columns:
            kw_df["ratio"] = pd.NA

    if not news_df.empty:
        news_df["date"] = pd.to_datetime(news_df["date"]).dt.date
        news_df["published_dt"] = pd.to_datetime(
            news_df["published"], format="%a, %d %b %Y %H:%M:%S %Z", errors="coerce"
        )
        news_df["rank"] = news_df["rank"].astype(int)

    if not naver_df.empty:
        naver_df["collected_date"] = pd.to_datetime(naver_df["collected_date"]).dt.date
        naver_df["period"]         = pd.to_datetime(naver_df["period"]).dt.date
        naver_df["ratio"]          = pd.to_numeric(naver_df["ratio"], errors="coerce")

    return kw_df, news_df, naver_df


# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🏥 Health Trend Dashboard")
st.caption("Google 헬스 카테고리(KR) 상위 키워드 · 네이버 검색트렌드 · 뉴스 현황")

kw_df, news_df, naver_df = load_data()

if kw_df.empty:
    st.warning("수집된 데이터가 없습니다. `python main.py`를 먼저 실행해 주세요.")
    st.stop()

# Google 키워드 / Naver 키워드 분리
google_kw_df = kw_df[kw_df["source"] != "naver"].copy()
naver_kw_df  = kw_df[kw_df["source"] == "naver"].copy()


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    # ── 날짜 범위
    date_opt = st.radio("날짜 범위", ["오늘", "최근 7일", "전체"], index=0)
    today = date.today()

    if date_opt == "오늘":
        min_date = max_date = today
    elif date_opt == "최근 7일":
        min_date = today - timedelta(days=6)
        max_date = today
    else:
        min_date = min(kw_df["date"])
        max_date = max(kw_df["date"])

    def date_mask(df: pd.DataFrame) -> pd.DataFrame:
        return df[(df["date"] >= min_date) & (df["date"] <= max_date)].copy()

    fkw_google = date_mask(google_kw_df)
    fkw_naver  = date_mask(naver_kw_df)

    # ── Google 키워드 선택
    st.markdown("---")
    st.caption("🔵 Google 키워드 필터")
    all_google_kws = sorted(fkw_google["keyword"].unique().tolist())
    selected_kws = st.multiselect(
        "키워드 선택",
        options=all_google_kws,
        default=all_google_kws,
        placeholder="키워드를 선택하세요",
    )
    if selected_kws:
        fkw_google = fkw_google[fkw_google["keyword"].isin(selected_kws)]

    # ── 뉴스 필터
    if not news_df.empty:
        fnews = date_mask(news_df)
        if selected_kws:
            fnews = fnews[fnews["keyword"].isin(selected_kws)]
    else:
        fnews = pd.DataFrame()

    # ── 네이버 그룹 필터
    st.markdown("---")
    st.caption("🟠 Naver 그룹 필터")
    if not naver_df.empty:
        naver_mask = (naver_df["collected_date"] >= min_date) & (naver_df["collected_date"] <= max_date)
        fnaver = naver_df[naver_mask].copy()
        all_naver_groups = sorted(fnaver["keyword_group"].unique().tolist())
        selected_naver_groups = st.multiselect(
            "네이버 키워드 그룹",
            options=all_naver_groups,
            default=all_naver_groups,
            placeholder="그룹을 선택하세요",
        )
        if selected_naver_groups:
            fnaver = fnaver[fnaver["keyword_group"].isin(selected_naver_groups)]
    else:
        fnaver = pd.DataFrame()
        st.caption("네이버 트렌드 데이터 없음")

    # ── 새로고침
    st.markdown("---")
    st.caption(f"📅 최근 수집일: **{max(kw_df['date'])}**")
    if st.button("🔄 데이터 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─── Summary Metrics ──────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

c1.metric("Google 키워드", f"{fkw_google['keyword'].nunique()}개")
c2.metric("뉴스 기사",     f"{len(fnews)}건")
c3.metric("Naver 그룹",    f"{fnaver['keyword_group'].nunique() if not fnaver.empty else 0}개")

if not kw_df.empty:
    d_min, d_max = min(kw_df["date"]), max(kw_df["date"])
    date_range_str = f"{d_min} ~ {d_max}" if d_min != d_max else str(d_min)
else:
    date_range_str = "—"
c4.metric("수집 날짜 범위", date_range_str)

st.divider()


# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_trend, tab_news, tab_compare = st.tabs([
    "📊 키워드 트렌드",
    "📰 뉴스 피드",
    "📈 Google vs 네이버 비교",
])


# ── Tab 1: 키워드 트렌드 (Google) ─────────────────────────────────────────────
with tab_trend:
    if fkw_google.empty:
        st.info("선택한 조건에 해당하는 Google 키워드 데이터가 없습니다.")
    else:
        col_list, col_chart = st.columns([1, 1], gap="large")

        with col_list:
            st.subheader("날짜별 상위 키워드")
            for d in sorted(fkw_google["date"].unique(), reverse=True):
                day_kws = fkw_google[fkw_google["date"] == d]["keyword"].tolist()
                label = f"📅 {d}  ({len(day_kws)}개)" + ("  ← 오늘" if d == today else "")
                with st.expander(label, expanded=(d == today)):
                    for i, kw in enumerate(day_kws, 1):
                        st.markdown(f"`{i:>2}`&nbsp;&nbsp;{kw}")

        with col_chart:
            st.subheader("키워드 수집 빈도")
            freq = (
                fkw_google["keyword"]
                .value_counts()
                .reset_index()
                .rename(columns={"keyword": "키워드", "count": "수집 횟수"})
            )
            st.bar_chart(
                freq.set_index("키워드")["수집 횟수"],
                horizontal=True,
                color="#4f8ef7",
            )


# ── Tab 2: 뉴스 피드 ──────────────────────────────────────────────────────────
with tab_news:
    if fnews.empty:
        st.info("선택한 조건에 해당하는 뉴스 데이터가 없습니다.")
    else:
        st.subheader("키워드별 뉴스 기사")
        kws_to_show = selected_kws if selected_kws else sorted(fnews["keyword"].unique())

        for kw in kws_to_show:
            kw_articles = (
                fnews[fnews["keyword"] == kw]
                .sort_values(["date", "rank"], ascending=[False, True])
            )
            if kw_articles.empty:
                continue

            with st.expander(f"🔑 **{kw}** — {len(kw_articles)}건", expanded=False):
                for _, row in kw_articles.iterrows():
                    pub_dt  = row.get("published_dt")
                    pub_str = (
                        pub_dt.strftime("%Y-%m-%d %H:%M")
                        if pd.notna(pub_dt)
                        else row.get("published", "")
                    )
                    st.markdown(
                        f"**{row['rank']}.** [{row['title']}]({row['url']})  \n"
                        f"<small>🗞️&nbsp;{row['source']}"
                        f"&nbsp;&nbsp;|&nbsp;&nbsp;🕒&nbsp;{pub_str}</small>",
                        unsafe_allow_html=True,
                    )
                    st.divider()


# ── Tab 3: Google vs 네이버 비교 ──────────────────────────────────────────────
with tab_compare:
    st.subheader("Google 트렌드 vs 네이버 검색트렌드 비교")

    col_g, col_n = st.columns(2, gap="large")

    # ── 왼쪽: Google 트렌드 ──────────────────────────────────────────────────
    with col_g:
        st.markdown("#### 🔵 Google 트렌드 키워드")
        if fkw_google.empty:
            st.info("Google 키워드 데이터가 없습니다.")
        else:
            # 최신 날짜 기준 키워드 목록
            latest_date  = max(fkw_google["date"])
            latest_kws   = fkw_google[fkw_google["date"] == latest_date]["keyword"].tolist()

            st.caption(f"기준일: {latest_date}  |  키워드 {len(latest_kws)}개")
            for i, kw in enumerate(latest_kws, 1):
                st.markdown(f"`{i:>2}`&nbsp;&nbsp;{kw}")

            if len(fkw_google["date"].unique()) > 1:
                st.markdown("---")
                st.markdown("**전체 기간 수집 빈도**")
                freq = (
                    fkw_google["keyword"]
                    .value_counts()
                    .head(15)
                    .reset_index()
                    .rename(columns={"keyword": "키워드", "count": "횟수"})
                )
                st.bar_chart(
                    freq.set_index("키워드")["횟수"],
                    horizontal=True,
                    color="#4f8ef7",
                )

    # ── 오른쪽: 네이버 트렌드 ────────────────────────────────────────────────
    with col_n:
        st.markdown("#### 🟠 네이버 검색트렌드")
        if fnaver.empty:
            st.info(
                "네이버 트렌드 데이터가 없습니다.  \n"
                "`.env` 파일에 API 키를 설정한 뒤 `python main.py`를 실행해 주세요."
            )
        else:
            # 날짜별 ratio 피벗 → 라인 차트
            pivot = (
                fnaver
                .groupby(["period", "keyword_group"])["ratio"]
                .mean()
                .reset_index()
                .pivot(index="period", columns="keyword_group", values="ratio")
                .sort_index()
            )
            pivot.index = pd.to_datetime(pivot.index)

            st.caption(
                f"수집 기간: {pivot.index.min().date()} ~ {pivot.index.max().date()}  "
                f"|  그룹 {len(pivot.columns)}개  "
                f"|  ※ 각 날짜별 전체 그룹 합계 = 100 (점유율 %)"
            )
            st.line_chart(pivot, height=320)

    # ── 공통 키워드 교집합 ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔗 Google · 네이버 공통 키워드")

    if not fkw_google.empty and not fnaver.empty:
        google_set = set(fkw_google["keyword"].str.replace(" ", "").str.lower())
        naver_set  = set(fnaver["keyword_group"].str.replace(" ", "").str.lower())
        common     = google_set & naver_set

        if common:
            st.success(f"공통 키워드 {len(common)}개 발견: {', '.join(sorted(common))}")
        else:
            st.info("두 플랫폼에서 동일하게 집계된 키워드가 없습니다.")

        # 네이버 최신 ratio 테이블 (오늘 또는 최근 수집일)
        if not fkw_naver.empty:
            st.markdown("**네이버 그룹별 최신 검색 점유율 (전체 합 = 100%)**")
            latest_naver = (
                fkw_naver
                .sort_values("date", ascending=False)
                .drop_duplicates("keyword")
                [["keyword", "ratio"]]
                .rename(columns={"keyword": "키워드 그룹", "ratio": "점유율 (%)"})
                .reset_index(drop=True)
            )
            st.dataframe(
                latest_naver,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "점유율 (%)": st.column_config.ProgressColumn(
                        "점유율 (%)",
                        min_value=0,
                        max_value=100,
                        format="%.1f",
                    )
                },
            )
    else:
        st.info("Google 또는 네이버 데이터가 부족해 비교를 표시할 수 없습니다.")
