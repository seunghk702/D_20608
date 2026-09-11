import datetime
import requests
import pandas as pd
import pytz
import streamlit as st

# Streamlit 페이지 설정
st.set_page_config(
    page_title="어제 박스오피스 순위",
    page_icon="🎬",
    layout="wide"
)

# API 응답 데이터를 1시간 동안 메모리에 저장(캐싱)하는 함수
# 같은 날짜로 다시 요청할 때 API를 중복 호출하지 않습니다.
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

def main():
    st.title("🎬 어제 일별 박스오피스 순위")

    # 1. secrets에서 인증키 불러오기
    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 API 인증키가 설정되지 않았습니다.")
        st.info("Streamlit Cloud 설정(Secrets)에 `KOBIS_KEY = '발급받은_키'`를 추가해 주세요.")
        st.stop()

    api_key = st.secrets["KOBIS_KEY"]

    # 2. 한국 시간(KST) 기준으로 '어제' 날짜 계산하기
    kst_tz = pytz.timezone("Asia/Seoul")
    now_kst = datetime.datetime.now(kst_tz)
    yesterday_kst = now_kst - datetime.timedelta(days=1)
    target_date = yesterday_kst.strftime("%Y%m%d")
    formatted_date_display = yesterday_kst.strftime("%Y년 %m월 %d일")

    st.caption(f"기준 일자: {formatted_date_display} (한국 시간)")

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
        st.warning("⚠️ 해당 날짜의 박스오피스 데이터가 비어 있습니다.")
        st.info("💡 KOBIS 집계 지연일 수 있으니 시간이 지난 후 다시 확인해 주세요.")
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

    # 6. 1위 영화 주요 지표 카드 표시
    top_1 = df.iloc[0]
    st.markdown(f"### 🏆 1위: **{top_1['movieNm']}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="일일 관객수", value=f"{top_1['audiCnt']:,} 명")
    with col2:
        st.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
    with col3:
        st.metric(label="스크린수", value=f"{top_1['scrnCnt']:,} 개")

    st.divider()

    # 7. 관객수 상위 5편 막대그래프
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)
    
    # 그래프용 데이터프레임 정리
    chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
    chart_data.columns = ["일일 관객수"]
    st.bar_chart(chart_data)

    st.divider()

    # 8. 전체 박스오피스 순위 표
    st.subheader("📋 전체 순위 목록")
    
    # 화면에 보여줄 컬럼 선택 및 이름 변경
    display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    display_df.columns = ["순위", "영화명", "개봉일", "일일 관객수", "누적 관객수", "스크린수"]

    # 표 형태로 출력 (숫자 세 자릿수 콤마 서식 적용)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "일일 관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적 관객수": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
        }
    )

if __name__ == "__main__":
    main()
