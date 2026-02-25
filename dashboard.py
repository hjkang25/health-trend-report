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
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    kw_files  = sorted(DATA_DIR.glob("keywords_*.csv"))
    news_files = sorted(DATA_DIR.glob("news_*.csv"))

    kw_df = (
        pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in kw_files], ignore_index=True)
        if kw_files
        else pd.DataFrame(columns=["date", "keyword", "source"])
    )
    news_df = (
        pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in news_files], ignore_index=True)
        if news_files
        else pd.DataFrame(columns=["date", "keyword", "rank", "title", "source", "published", "url"])
    )

    if not kw_df.empty:
        kw_df["date"] = pd.to_datetime(kw_df["date"]).dt.date

    if not news_df.empty:
        news_df["date"] = pd.to_datetime(news_df["date"]).dt.date
        news_df["published_dt"] = pd.to_datetime(
            news_df["published"], format="%a, %d %b %Y %H:%M:%S %Z", errors="coerce"
        )
        news_df["rank"] = news_df["rank"].astype(int)

    return kw_df, news_df


# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🏥 Health Trend Dashboard")
st.caption("Google 헬스 카테고리(KR) 상위 키워드 · 뉴스 현황")

kw_df, news_df = load_data()

if kw_df.empty:
    st.warning("수집된 데이터가 없습니다. `python main.py`를 먼저 실행해 주세요.")
    st.stop()


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

    fkw = kw_df[(kw_df["date"] >= min_date) & (kw_df["date"] <= max_date)].copy()

    # ── 키워드 선택
    st.markdown("---")
    all_kws = sorted(fkw["keyword"].unique().tolist())
    selected_kws = st.multiselect(
        "키워드 선택",
        options=all_kws,
        default=all_kws,
        placeholder="키워드를 선택하세요",
    )

    # 키워드 필터 적용
    if selected_kws:
        fkw = fkw[fkw["keyword"].isin(selected_kws)]

    # 뉴스 필터 적용
    if not news_df.empty:
        fnews = news_df[(news_df["date"] >= min_date) & (news_df["date"] <= max_date)].copy()
        if selected_kws:
            fnews = fnews[fnews["keyword"].isin(selected_kws)]
    else:
        fnews = pd.DataFrame()

    # ── 새로고침
    st.markdown("---")
    st.caption(f"📅 최근 수집일: **{max(kw_df['date'])}**")
    if st.button("🔄 데이터 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ─── Summary Metrics ──────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

c1.metric("수집 날짜", f"{fkw['date'].nunique()}일")
c2.metric("키워드 수", f"{fkw['keyword'].nunique()}개")
c3.metric("뉴스 기사", f"{len(fnews)}건")

if not fkw.empty:
    d_min, d_max = min(fkw["date"]), max(fkw["date"])
    date_range_str = f"{d_min} ~ {d_max}" if d_min != d_max else str(d_min)
else:
    date_range_str = "—"
c4.metric("날짜 범위", date_range_str)

st.divider()


# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_trend, tab_news = st.tabs(["📊 키워드 트렌드", "📰 뉴스 피드"])


# ── Tab 1: 키워드 트렌드 ──────────────────────────────────────────────────────
with tab_trend:
    if fkw.empty:
        st.info("선택한 조건에 해당하는 키워드 데이터가 없습니다.")
    else:
        col_list, col_chart = st.columns([1, 1], gap="large")

        # 날짜별 키워드 목록
        with col_list:
            st.subheader("날짜별 상위 키워드")
            for d in sorted(fkw["date"].unique(), reverse=True):
                day_kws = fkw[fkw["date"] == d]["keyword"].tolist()
                label = f"📅 {d}  ({len(day_kws)}개)" + ("  ← 오늘" if d == today else "")
                with st.expander(label, expanded=(d == today)):
                    for i, kw in enumerate(day_kws, 1):
                        st.markdown(f"`{i:>2}`&nbsp;&nbsp;{kw}")

        # 키워드 빈도 차트
        with col_chart:
            st.subheader("키워드 수집 빈도")
            freq = (
                fkw["keyword"]
                .value_counts()
                .reset_index()
                .rename(columns={"keyword": "키워드", "count": "수집 횟수"})
            )
            st.bar_chart(
                freq.set_index("키워드")["수집 횟수"],
                horizontal=True,
                color="#4f8ef7",
            )


# ── Tab 2: 뉴스 피드 ─────────────────────────────────────────────────────────
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
                    # 발행일 포맷
                    pub_dt = row.get("published_dt")
                    pub_str = (
                        pub_dt.strftime("%Y-%m-%d %H:%M")
                        if pd.notna(pub_dt)
                        else row.get("published", "")
                    )

                    st.markdown(
                        f"**{row['rank']}.** [{row['title']}]({row['url']})  \n"
                        f"<small>🗞️&nbsp;{row['source']}"
                        f"&nbsp;&nbsp;|&nbsp;&nbsp;"
                        f"🕒&nbsp;{pub_str}</small>",
                        unsafe_allow_html=True,
                    )
                    st.divider()
