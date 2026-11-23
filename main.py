import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. CSV 데이터로 실시간 모델 학습
@st.cache_resource
def train_model():
    df = pd.read_csv('diamonds_train.csv')
    
    X = df.drop(columns=['price', 'log_price'])
    y_log = df['log_price']
    
    model = LinearRegression()
    model.fit(X, y_log)
    
    train_residuals = y_log - model.predict(X)
    smearing_factor = np.mean(np.exp(train_residuals))
    
    return model, smearing_factor, X.columns.tolist()

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

# Depth, Table 슬라이더 원상 복구
st.sidebar.subheader("세부 비율 (옵션)")
depth = st.sidebar.slider("Depth (%)", 50.0, 70.0, 61.7)
table = st.sidebar.slider("Table (%)", 40.0, 70.0, 57.0)
x_val = st.sidebar.number_input("길이 (x, mm)", value=6.5)
y_val = st.sidebar.number_input("너비 (y, mm)", value=6.5)
z_val = st.sidebar.number_input("깊이 (z, mm)", value=4.0)

# 3. 예측 버튼 클릭 시 동작
if st.button("적정 가격 예측하기 🔍"):
    # 파생 변수 계산 (밀도 공식 정상화 및 구문 오류 수정)
    log_carat = np.log(carat)
    aspect_ratio = x_val / y_val if y_val != 0 else 1.0
    volume = x_val * y_val * z_val
    density_proxy = carat / volume if volume != 0 else 0.0

    # 입력 데이터를 실수형(0.0)으로 초기화
    input_data = pd.DataFrame(0.0, index=[0], columns=feature_columns)
    
    # 수치형 변수 채우기
    input_data.loc[0, 'log_carat'] = log_carat
    input_data.loc[0, 'aspect_ratio'] = aspect_ratio
    input_data.loc[0, 'depth'] = depth
    input_data.loc[0, 'table'] = table
    input_data.loc[0, 'density_proxy'] = density_proxy

    # 범주형 변수(원핫 인코딩) 채우기
    if f'cut_{cut}' in feature_columns: input_data.loc[0, f'cut_{cut}'] = 1.0
    if f'color_{color}' in feature_columns: input_data.loc[0, f'color_{color}'] = 1.0
    if f'clarity_{clarity}' in feature_columns: input_data.loc[0, f'clarity_{clarity}'] = 1.0

    # 4. 가격 예측 및 출력
    pred_log = model.predict(input_data)[0]
    final_price = np.expm1(pred_log) * smearing_factor

    st.success(f"### 예측된 가격은 약 **${final_price:,.2f}** 입니다!")
