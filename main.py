import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="박스오피스 데이터 분석", layout="wide")


# [1. 데이터 불러오기]
# 캐싱 기술(@st.cache_data)을 사용하여 매번 새로 로딩하지 않고 최초 1회만 불러와 저장합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)

    # [2. 날짜 전처리 및 정렬]
    # 결측치(NaN)가 포함된 행을 삭제합니다.
    df = df.dropna()

    # '기준일자' 컬럼을 datetime 형식으로 변환합니다.
    df["기준일자"] = pd.to_datetime(df["기준일자"])

    # 데이터를 '기준일자' 오름차순으로 정렬합니다.
    df = df.sort_values(by="기준일자", ascending=True)

    return df


# 데이터 로드 실행
df = load_data()

st.title("🎬 KOBIS 박스오피스 데이터 분석 대시보드")
st.write("영화별 일별 관객수 및 누적 관객수 변화 추이를 확인하는 앱입니다.")
st.markdown("---")


# [3. 영화 선택 기능]
# 누적관객수 최대치를 기준으로 영화명을 내림차순 정렬하여 목록을 추출합니다.
movie_order = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# 셀렉트박스로 분석할 영화를 선택합니다.
selected_movie = st.selectbox("분석할 영화를 선택하세요:", movie_order)

# 사용자가 선택한 영화의 데이터만 필터링합니다.
filtered_df = df[df["영화명"] == selected_movie]


# ---------------------------------------------------------
# [구역 1: 개별 영화 일별 관객수 추이 - 선그래프]
# ---------------------------------------------------------
st.subheader(f"📌 구역 1: {selected_movie} - 일별 관객수 추이")

fig1 = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"[{selected_movie}] 일자별 관객수 변화",
    labels={"기준일자": "날짜", "해당일관객수": "해당일 관객수(명)"},
    markers=True,
)
fig1.update_layout(hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    f"{selected_movie}의 개봉 초기 관객 집중도와 일자별 흥행 유효 기간을 파악할 수 있습니다."
)

st.markdown("---")


# ---------------------------------------------------------
# [구역 2: 개별 영화 누적 관객수 성장 추이 - 영역차트]
# ---------------------------------------------------------
st.subheader(f"📌 구역 2: {selected_movie} - 누적 관객수 성장 추이")

fig2 = px.area(
    filtered_df,
    x="기준일자",
    y="누적관객수",
    title=f"[{selected_movie}] 일자별 누적 관객수 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"},
)
fig2.update_layout(hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    f"시간 경과에 따른 {selected_movie}의 총 누적 관객수 누적 완만도와 최종 흥행 규모를 확인할 수 있습니다."
)

st.markdown("---")


# ---------------------------------------------------------
# [구역 3: TOP10 20일 이상 차트인 영화 중 누적관객수 TOP 5 비교 - 다중 선그래프]
# ---------------------------------------------------------
st.subheader("📌 구역 3: 장기 흥행(20일 이상) TOP 5 영화 비교")

movie_days = df.groupby("영화명")["기준일자"].count()
long_running_movies = movie_days[movie_days >= 20].index

top5_long_running = (
    df[df["영화명"].isin(long_running_movies)]
    .groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

top5_long_running_df = df[df["영화명"].isin(top5_long_running)]

fig3 = px.line(
    top5_long_running_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",
    title="TOP 10 20일 이상 유지 영화 중 누적 관객수 TOP 5 비교",
    labels={
        "기준일자": "날짜",
        "누적관객수": "누적 관객수(명)",
        "영화명": "영화 제목",
    },
)
fig3.update_layout(hovermode="x unified")
st.plotly_chart(fig3, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    f"최소 20일 이상 상위권을 유지한 장기 흥행 영화 TOP 5('{', '.join(top5_long_running)}')의 "
    "누적 관객수 증가 속도와 최종 관객 동원력을 대조해 볼 수 있습니다."
)

st.markdown("---")


# ---------------------------------------------------------
# [구역 4: 전체 박스오피스 일별 총 관객수 및 7일 이동평균선]
# ---------------------------------------------------------
st.subheader("📌 구역 4: 전체 박스오피스 일별 총 관객수 & 7일 이동평균")

daily_total = df.groupby("기준일자")["해당일관객수"].sum().reset_index()
daily_total["7일_이동평균"] = daily_total["해당일관객수"].rolling(window=7).mean()

fig4 = go.Figure()

fig4.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["해당일관객수"],
        mode="lines",
        name="일별 총 관객수",
        line=dict(color="rgba(150, 180, 220, 0.4)", width=1.5),
    )
)

fig4.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["7일_이동평균"],
        mode="lines",
        name="7일 이동평균",
        line=dict(color="#1f77b4", width=3),
    )
)

fig4.update_layout(
    title="전체 박스오피스 일별 총 관객수 및 7일 이동평균선",
    xaxis_title="날짜",
    yaxis_title="총 관객수(명)",
    hovermode="x unified",
)

st.plotly_chart(fig4, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "주말/평일 간 단기 변동성을 제거한 7일 이동평균선(진한 선)을 통해 전체 영화 시장의 성수기/비수기 시즌 및 대형 흥행 트렌드 변화를 한눈에 파악할 수 있습니다."
)

st.markdown("---")


# ---------------------------------------------------------
# [구역 5: 월별 전체 관객수 합계 - 막대그래프]
# ---------------------------------------------------------
st.subheader("📌 구역 5: 월별 전체 관객수 합계")

daily_total["연월"] = daily_total["기준일자"].dt.strftime("%Y-%m")
monthly_total = daily_total.groupby("연월")["해당일관객수"].sum().reset_index()

fig5 = px.bar(
    monthly_total,
    x="연월",
    y="해당일관객수",
    title="월별 극장가 전체 관객수 합계",
    labels={"연월": "연월(Year-Month)", "해당일관객수": "월간 총 관객수(명)"},
    text_auto=".2s",
)

fig5.update_traces(marker_color="#2ca02c")
fig5.update_layout(xaxis_type="category")

st.plotly_chart(fig5, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "월별 총 관객수 집계를 통해 연중 어느 달에 극장가 전체 수요가 가장 집중되는지 계절성(Seasonality)을 명확하게 파악할 수 있습니다."
)

st.markdown("---")


# ---------------------------------------------------------
# [구역 6: 월(주차) × 요일별 관객수 - 캘린더 히트맵]
# ---------------------------------------------------------
st.subheader("📌 구역 6: 캘린더 히트맵 (월·요일별 관객수 분포)")

# 1. 히트맵 표현을 위한 전처리
heatmap_data = daily_total.copy()

# '연-월' 컬럼 추출
heatmap_data["월"] = heatmap_data["기준일자"].dt.strftime("%Y-%m")

# 요일명 추출 및 월요일~일요일 순서 정렬
days_order = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일",
    "일요일",
]
day_map = {0: "월요일", 1: "화요일", 2: "수요일", 3: "목요일", 4: "금요일", 5: "토요일", 6: "일요일"}
heatmap_data["요일"] = heatmap_data["기준일자"].dt.dayofweek.map(day_map)

# 날짜 문자열(yyyy-mm-dd) 생성 (호버용)
heatmap_data["날짜문자열"] = heatmap_data["기준일자"].dt.strftime("%Y-%m-%d")

# 2. Plotly Density Heatmap 생성
fig6 = px.density_heatmap(
    heatmap_data,
    x="월",
    y="요일",
    z="해당일관객수",
    category_orders={"요일": days_order},  # 월요일부터 일요일 순서로 세로축 배치
    color_continuous_scale="Viridis",  # 관객수가 많을수록 진한/밝은 시각적 구분
    title="월별·요일별 관객수 분포 캘린더 히트맵",
    labels={
        "월": "연-월",
        "요일": "요일",
        "해당일관객수": "총 관객수(명)",
    },
    hover_data={
        "날짜문자열": True,  # 마우스 올렸을 때 yyyy-mm-dd 표시
        "월": False,
        "요일": False,
    },
)

# 마우스 호버 템플릿 커스텀 (yyyy-mm-dd 날짜와 관객수 명확하게 보이기)
fig6.update_traces(
    hovertemplate="<b>날짜: %{customdata[0]}</b><br>요일: %{y}<br>관객수: %{z:,.0f}명<extra></extra>"
)

fig6.update_layout(
    xaxis_type="category",
    coloraxis_colorbar=dict(title="관객수(명)"),
)

st.plotly_chart(fig6, use_container_width=True)

# 그래프 하단 설명 란
st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "특정 월과 요일(주말 vs 평일, 공휴일) 조합에 따른 극장 관객 몰림 현상과 일자별 패턴 차이를 색상의 짙고 옅음으로 한눈에 파악할 수 있습니다."
)
