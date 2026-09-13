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
st.write("영화별 일별 관객수 변화와 흐름을 확인하는 앱입니다.")
st.markdown("---")


# [3. 영화 선택 기능]
# 누적관객수 최대치를 기준으로 영화명을 내림차순 정렬하여 목록을 추출합니다.
movie_order = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# 사이드바 또는 메인 화면에서 선택할 수 있도록 드롭다운(select box)을 만듭니다.
selected_movie = st.selectbox("분석할 영화를 선택하세요:", movie_order)

# 사용자가 선택한 영화의 데이터만 필터링합니다.
filtered_df = df[df["영화명"] == selected_movie]


# [5. 구역 나누기]
# 추후 다른 그래프를 계속 추가할 수 있도록 구역(Container/Header)을 분리합니다.
st.subheader(f"📌 구역 1: {selected_movie} - 일별 관객수 추이")

# [4. 선그래프 그리기]
# 선택된 영화의 '기준일자'별 '해당일관객수' 선 그래프 생성 (Plotly 사용)
fig1 = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"[{selected_movie}] 일자별 관객수 변화",
    labels={"기준일자": "날짜", "해당일관객수": "해당일 관객수(명)"},
    markers=True,  # 데이터 지점에 점 표시
)

# 그래프 레이아웃 커스텀
fig1.update_layout(hovermode="x unified")

# Streamlit 화면에 그래프 출력
st.plotly_chart(fig1, use_container_width=True)

# [5. 그래프 하단 설명 란]
st.info("💡 **이 그래프로 알 수 있는 것:** " f"{selected_movie}의 개봉 초기 관객 집중도와 흥행 유효 기간을 파악할 수 있습니다.")

st.markdown("---")

# 추후 새로운 그래프를 추가할 자리를 미리 배치해 둡니다.
st.subheader("📌 구역 2: (추가 예정 구역)")
st.write("이곳에 추후 새로운 시각화 그래프를 추가할 예정입니다.")
st.info("💡 **이 그래프로 알 수 있는 것:** (추후 작성 예정)")
