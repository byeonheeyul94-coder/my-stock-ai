import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="희열의 템플턴 AI", layout="wide")

# 2. 데이터 관리 함수 (종목 저장용)
PORTFOLIO_FILE = 'my_portfolio.csv'

def load_data():
    if os.path.exists(PORTFOLIO_FILE):
        return pd.read_csv(PORTFOLIO_FILE)
    return pd.DataFrame(columns=["종목코드", "종목명", "매수가", "수량"])

# 3. 주식 데이터 가져오기 (해외 서버 대응)
@st.cache_data(ttl=3600)
def get_stock_list():
    try:
        df = fdr.StockListing('NAVER') # 해외 배포 환경에 강함
        return df[['Code', 'Name']]
    except:
        return pd.DataFrame({'Code':['005930'], 'Name':['삼성전자']})

# 4. 차트 그리기 함수
def draw_chart(df, name):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name=name)])
    fig.update_layout(xaxis_rangeslider_visible=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- 사이드바 및 메뉴 ---
st.sidebar.title("🚀 템플턴 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🔍 종목검색", "💰 나의 포트폴리오"])

stock_list = get_stock_list()

# [메뉴 1: 종목 검색 및 분석]
if menu == "🔍 종목검색":
    st.header("🔍 종목 분석 및 진단")
    
    # 종목 선택
    selected_stock = st.selectbox("분석할 종목을 선택하거나 검색하세요", stock_list['Name'])
    code = stock_list[stock_list['Name'] == selected_stock]['Code'].values[0]
    
    # 기간 설정 (최근 1년)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    df = fdr.DataReader(code, start_date, end_date)
    
    if not df.empty:
        curr_price = int(df['Close'].iloc[-1])
        st.metric(label=f"{selected_stock} 현재가", value=f"{curr_price:,}원")
        
        # 차트 출력
        draw_chart(df, selected_stock)
        
        # 템플턴 전략 판독 (간이)
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        if curr_price > ma20:
            st.success("✅ **템플턴 신호:** 현재 20일선 위에서 힘을 내고 있습니다. 매수 검토 가능!")
        else:
            st.warning("☁️ **템플턴 신호:** 현재 조정 구간입니다. 20일선 돌파를 기다리세요.")

# [메뉴 2: 포트폴리오 관리]
elif menu == "💰 나의 포트폴리오":
    st.header("💰 나의 실전 매매 장부")
    df_pf = load_data()
    
    # 종목 추가 폼
    with st.expander("➕ 새 종목 등록하기"):
        c1, c2, c3 = st.columns(3)
        new_name = c1.selectbox("종목 선택", stock_list['Name'])
        new_price = c2.number_input("매수가(원)", min_value=0, step=100)
        new_qty = c3.number_input("수량(주)", min_value=0, step=1)
        
        if st.button("내 장부에 저장"):
            new_code = stock_list[stock_list['Name'] == new_name]['Code'].values[0]
            new_row = pd.DataFrame({"종목코드":[new_code], "종목명":[new_name], "매수가":[new_price], "수량":[new_qty]})
            df_pf = pd.concat([df_pf, new_row], ignore_index=True)
            df_pf.to_csv(PORTFOLIO_FILE, index=False)
            st.rerun()

    if not df_pf.empty:
        st.table(df_pf)
        if st.button("장부 초기화"):
            if os.path.exists(PORTFOLIO_FILE):
                os.remove(PORTFOLIO_FILE)
                st.rerun()
    else:
        st.info("아직 등록된 종목이 없습니다.")
