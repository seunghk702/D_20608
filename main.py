import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# Streamlit 페이지 설정
st.set_page_config(
    page_title="일별 박스오피스 순위",
    page_icon="🎬",
    layout="wide"
)

# API 응답 데이터를 1시간 동안 메모리에 저장(캐싱)하는 함수
# 선택한 날짜가 같으면 API를 중복 호출하지 않고 저장된 결과를 사용합니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(api_key, target_date):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": target_date
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        # HTTP 요청이 성공했는지 확인
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

# 전날 대비 순위 증감(rankInten)에 따라 화살표 및 아이콘 생성 함수
def format_rank_change(inten):
    try:
        val = int(inten)
        if val > 0:
            return f":red[▲ {val}]"  # 순위 상승 (빨간 위 화살표)
        elif val < 0:
            return f":blue[▼ {abs(val)}]"  # 순위 하락 (파란 아래 화살표)
        else:
            return "-"  # 변동 없음
    except ValueError:
        return "-"

def main():
    st.title("🎬 일별 박스오피스 순위")

    # 1. secrets에서 인증키 불러오기
    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 API 인증키가 설정되지 않았습니다.")
        st.info("Streamlit Cloud 설정(Secrets)에 `KOBIS_KEY = '발급받은_키'`를 추가해 주세요.")
        st.stop()

    api_key = st.secrets["KOBIS_KEY"]

    # 2. 한국 시간(KST) 기준으로 선택 가능한 최신 날짜(어제) 계산
    kst_tz = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(kst_tz)
    yesterday_kst = (now_kst - datetime.timedelta(days=1)).date()

    # 사이드바에서 조회할 날짜 선택 (기본값: 어제, 선택 가능 최대 날짜: 어제)
    selected_date = st.sidebar.date_input(
        "📅 조회할 날짜 선택",
        value=yesterday_kst,
        max_value=yesterday_kst
    )

    # API 호출용 YYYYMMDD 포맷 및 화면 표시용 포맷 생성
    target_date = selected_date.strftime("%Y%m%d")
    formatted_date_display = selected_date.strftime("%Y년 %m월 %d일")

    st.caption(f"조회 일자: {formatted_date_display} (한국 시간 기준)")

    # 3. API 데이터 요청
    data = fetch_box_office_data(api_key, target_date)

    # 4. 예외 및 오류 처리
    if not data:
        st.error("❌ KOBIS 서버와 통신할 수 없습니다.")
        st.info("💡 네트워크 연결 상태를 확인하거나 잠시 후 다시 시도해 주세요.")
        st.stop()

    # 인증키 오류 등으로 faultInfo가 반환된 경우
    if "faultInfo" in data:
        st.error("❌ API 요청 중 오류가 발생했습니다.")
        st.warning(f"오류 메시지: {data['faultInfo'].get('message', '알 수 없는 오류')}")
        st.info("💡 Streamlit Secrets에 입력한 KOBIS_KEY가 올바른지 확인해 주세요.")
        st.stop()

    # 정상 응답 구조 확인
    box_office_result = data.get("boxOfficeResult", {})
    daily_list = box_office_result.get("dailyBoxOfficeList", [])

    # 영화 목록이 비어 있는 경우
    if not daily_list:
        st.warning("⚠️ 그날은 아직 집계 전입니다.")
        st.info("💡 KOBIS 집계 지연이거나 해당 날짜의 데이터가 아직 업데이트되지 않았을 수 있습니다.")
        st.stop()

    # 5. 데이터 전처리 (문자열 -> 숫자 변환)
    df = pd.DataFrame(daily_list)

    # 필요한 컬럼 정제 및 타입 변환
    df["rank"] = pd.to_numeric(df["rank"])
    df["audiCnt"] = pd.to_numeric(df["audiCnt"])
    df["audiAcc"] = pd.to_numeric(df["audiAcc"])
    df["scrnCnt"] = pd.to_numeric(df["scrnCnt"])

    # 순위 기준으로 정렬
    df = df.sort_values("rank")

    # 6. 전날 대비 순위 증감 및 누적 관객 100만 이상 트로피 처리
    df["rank_change"] = df["rankInten"].apply(format_rank_change)
    df["display_name"] = df.apply(
        lambda row: f"🏆 {row['movieNm']}" if row["audiAcc"] >= 1000000 else row["movieNm"],
        axis=1
    )

    # 7. 1위 영화 주요 지표 카드 표시
    top_1 = df.iloc[0]
    st.markdown(f"### 🏆 1위: **{top_1['display_name']}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="일일 관객수", value=f"{top_1['audiCnt']:,} 명")
    with col2:
        st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    with col3:
        st.metric(label="스크린수", value=f"{top_1['scrnCnt']:,} 개")

    st.divider()

    # 8. 관객수 상위 5편 막대그래프
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)
    
    # 그래프용 데이터프레임 정리 (그래프 레이블에는 원본 영화명 사용)
    chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
    chart_data.columns = ["일일 관객수"]
    st.bar_chart(chart_data)

    st.divider()

    # 9. 전체 박스오피스 순위 표
    st.subheader("📋 전체 순위 목록")
    
    # 화면에 보여줄 컬럼 선택 및 이름 변경
    display_df = df[["rank", "rank_change", "display_name", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    display_df.columns = ["순위", "전날 대비", "영화명", "개봉일", "일일 관객수", "누적 관객수", "스크린수"]

    # 표 형태로 출력 (숫자 세 자릿수 콤마 서식 적용)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "전날 대비": st.column_config.TextColumn(
                "전날 대비",
                help="▲ : 순위 상승 (빨간색), ▼ : 순위 하락 (파란색)"
            ),
            "일일 관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적 관객수": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
        }
    )

if __name__ == "__main__":
    main()
