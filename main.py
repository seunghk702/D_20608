import plotly.express as px
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

# 선택된 영화의 '기준일자'별 '해당일관객수' 선 그래프 생성
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

# 선택된 영화의 '기준일자'별 '누적관객수' 영역 차트(Area Chart) 생성
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

# 1. 영화별 차트인(데이터 등장) 일수를 계산
movie_days = df.groupby("영화명")["기준일자"].count()

# 2. 20일 이상 등장한 영화의 이름만 필터링
long_running_movies = movie_days[movie_days >= 20].index

# 3. 20일 이상 등장한 영화 중에서 누적관객수 상위 5개 영화 선택
top5_long_running = (
    df[df["영화명"].isin(long_running_movies)]
    .groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

# 4. 해당 5개 영화의 데이터만 추출
top5_long_running_df = df[df["영화명"].isin(top5_long_running)]

# 5. 다중 선 그래프 생성 (color="영화명"으로 자동 색상 및 범례 분리)
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

# 그래프 하단 설명 란
st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    f"최소 20일 이상 상위권을 유지한 장기 흥행 영화 TOP 5('{', '.join(top5_long_running)}')의 "
    "누적 관객수 증가 속도와 최종 관객 동원력을 대조해 볼 수 있습니다."
)
