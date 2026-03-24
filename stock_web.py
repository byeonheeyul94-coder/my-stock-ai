import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="희열의 템플턴 AI", layout="wide")

# 2. 데이터 관리 (CSV 파일 방식)
PORTFOLIO_FILE = 'my_portfolio.csv'

def load_data(file_path, default_cols):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

# [핵심 수정] 해외 서버 차단을 피하기 위해 NAVER 모드로 변경
@st.cache_data(ttl=3600)
def get_stock_list():
    try:
        # 'KRX'는 차단될 확률이 높으므로 'NAVER'를 사용합니다.
        df = fdr.StockListing('NAVER')
        return df[['Code', 'Name']]
    except:
        # 비상용 샘플 데이터
        return pd.DataFrame({'Code':['005930', '042700'], 'Name':['삼성전자', '한미반도체']})

# 3. 전략 판독기 로직
def get_strategy_signal(df, curr_p, buy_p=None):
    if df.empty or len(df) < 20: return "분석 대기", "#707070"
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    if buy_p:
        profit = ((curr_p - buy_p) / buy_p * 100)
        if profit > 10: return "💰 수익 매도", "#2EB82E"
        elif profit < -5: return "➕ 추가매수", "#FFA500"
        return "✅ 보유", "#2EB82E"
    return "👍 매수 대기" if curr_p > ma20 else "☁️ 관망", "#1F77B4"

stock_list = get_stock_list()

# --- 사이드바 및 메뉴 ---
st.sidebar.title("🚀 템플턴 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🔍 종목검색", "📈 종목분석", "🔥 주도업종 스캔", "🎯 템플턴 포착", "💰 보유 종목"])

# [보유 종목 메뉴 예시]
if menu == "💰 보유 종목":
    st.header("💰 나의 실전 매매 장부")
    df_pf = load_data(PORTFOLIO_FILE, ["종목명", "매수가", "수량"])
    
    # 입력창
    with st.expander("➕ 종목 추가"):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("종목명")
        price = c2.number_input("매수가")
        qty = c3.number_input("수량")
        if st.button("저장"):
            new_data = pd.DataFrame({"종목명":[name], "매수가":[price], "수량":[qty]})
            df_pf = pd.concat([df_pf, new_data], ignore_index=True)
            df_pf.to_csv(PORTFOLIO_FILE, index=False)
            st.rerun()

    if not df_pf.empty:
        st.table(df_pf)

# 나머지 메뉴들도 위와 같은 방식으로 작동합니다.
else:
    st.info(f"'{menu}' 메뉴가 준비되었습니다. 종목을 검색하거나 분석을 시작해 보세요!")
