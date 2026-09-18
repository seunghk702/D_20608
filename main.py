import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 타이틀
st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.markdown("---")

# 데이터 불러오기 및 전처리
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # genre: 결측치 처리 후 첫 번째 장르만 추출
    df['genre'] = df['genre'].fillna('기타').astype(str)
    df['genre'] = df['genre'].apply(lambda x: x.split('|')[0].strip() if x.strip() != '' else '기타')
    
    return df

try:
    df = load_data()
    
    # ----------------------------------------------------
    # 첫 번째 그래프: 장르별 영화 편수 (플롯리 도넛 그래프)
    # ----------------------------------------------------
    st.subheader("1. 장르별 영화 편수 분포")
    
    # 장르별 영화 편수 집계
    genre_counts = df['genre'].value_counts().reset_index()
    genre_counts.columns = ['장르', '영화 편수']
    
    # Plotly Donut Chart 생성
    fig_donut = px.pie(
        genre_counts,
        values='영화 편수',
        names='장르',
        hole=0.4,
        title='장르별 영화 편수 비중 (도넛 차트)'
    )
    
    # 호버 툴팁 및 레이아웃 설정 (편수와 비율이 마우스 올렸을 때 표시되도록 설정)
    fig_donut.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>장르:</b> %{label}<br><b>영화 편수:</b> %{value}편<br><b>비율:</b> %{percent}<extra></extra>'
    )
    fig_donut.update_layout(margin=dict(t=50, b=20, l=20, r=20))
    
    # 그래프 출력
    st.plotly_chart(fig_donut, use_container_width=True)
    
    # 이 그래프로 알 수 있는 것 구역
    st.info("💡 **이 그래프로 알 수 있는 것:** 특정 장르(예: 드라마, 액션 등)의 영화가 전체 상위권 개봉작 중에서 차지하는 비중과 편수 분포를 한눈에 파악할 수 있습니다.")
    
    st.markdown("---")

    # 추가 안내
    st.caption("※ 본 데이터는 1년간 박스오피스 10위권에 든 개봉 영화 216편의 데이터를 기반으로 구성되었습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
