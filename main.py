import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. CSV 데이터로 실시간 모델 학습 (캐싱을 통해 최초 1회만 빠르게 실행)
@st.cache_resource
def train_model():
    # 깃허브에 업로드된 학습 데이터 불러오기
    df = pd.read_csv('diamonds_train.csv')
    
    # 피처(X)와 타겟(y) 분리
    X = df.drop(columns=['price', 'log_price'])
    y_log = df['log_price']
    
    # 실시간 선형회귀 모델 학습
    model = LinearRegression()
    model.fit(X, y_log)
    
    # 잔차 보정 계수(Smearing Factor) 자동 계산
    train_residuals = y_log - model.predict(X)
    smearing_factor = np.mean(np.exp(train_residuals))
    
    return model, smearing_factor, X.columns.tolist()

# 학습된 모델 객체, 보정 계수, 피처 컬럼 목록 받아오기
model, smearing_factor, feature_columns = train_model()

# 2. 웹앱 화면 구성
st.title("💎 다이아몬드 가격 예측 앱")
st.write("다이아몬드의 스펙을 입력하면 머신러닝 모델이 적정 가격을 예측합니다.")

# 사이드바 입력창 구성
st.sidebar.header("다이아몬드 스펙 입력")
carat = st.sidebar.number_input("중량 (Carat)", min_value=0.2, max_value=5.0, value=1.0, step=0.01)
cut = st.sidebar.selectbox("컷팅 (Cut)", ['Ideal', 'Premium', 'Very Good', 'Good', 'Fair'])
color = st.sidebar.selectbox("색상 (Color)", ['D', 'E', 'F', 'G', 'H', 'I', 'J'])
clarity = st.sidebar.selectbox("투명도 (Clarity)", ['IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1'])

st.sidebar.subheader("세부 비율 (옵션)")
depth = st.sidebar.slider("Depth (%)", 50.0, 70.0, 61.7)
table = st.sidebar.slider("Table (%)", 40.0, 70.0, 57.0)
x_val = st.sidebar.number_input("길이 (x, mm)", value=6.5)
y_val = st.sidebar.number_input("너비 (y, mm)", value=6.5)
z_val = st.sidebar.number_input("깊이 (z, mm)", value=4.0)

# 3. 예측 버튼 클릭 시 동작
if st.button("적정 가격 예측하기 🔍"):
    # 입력값을 바탕으로 파생 변수 계산
    log_carat = np.log(carat)
    aspect_ratio = x_val / y_val if y_val != 0 else 1.0
    density_proxy = (x_val * y_val * z_val) / carat if carat != 0 else 0.0

    # 입력 데이터를 데이터프레임으로 만들고 0으로 초기화
    input_data = pd.DataFrame(0, index=[0], columns=feature_columns)
    
    # 수치형 변수 채우기
    input_data.loc[0, 'log_carat'] = log_carat
    input_data.loc[0, 'aspect_ratio'] = aspect_ratio
    input_data.loc[0, 'depth'] = depth
    input_data.loc[0, 'table'] = table
    input_data.loc[0, 'density_proxy'] = density_proxy

    # 범주형 변수(원핫 인코딩) 채우기 (해당 등급만 1로 변경)
    if f'cut_{cut}' in feature_columns: input_data.loc[0, f'cut_{cut}'] = 1
    if f'color_{color}' in feature_columns: input_data.loc[0, f'color_{color}'] = 1
    if f'clarity_{clarity}' in feature_columns: input_data.loc[0, f'clarity_{clarity}'] = 1

    # 4. 모델 예측 및 잔차 보정 계수를 적용한 달러($) 환산
    pred_log = model.predict(input_data)[0]
    final_price = np.expm1(pred_log) * smearing_factor

    # 결과 출력
    st.success(f"### 예측된 가격은 약 **${final_price:,.2f}** 입니다!")
    st.balloons()
