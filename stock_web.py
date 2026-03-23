import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="희열의 템플턴 AI", layout="wide")

# [중요] 희열 님의 구글 시트 주소를 여기에 꼭 넣으세요!
# 예: sh_url = "https://docs.google.com/spreadsheets/d/12345abcde/edit#gid=0"
sh_url = "여기에_구글시트_주소를_넣으세요"

# 2. 종목 리스트 가져오기 (에러 방지 로직 추가)
@st.cache_data(ttl=3600)
def get_krx_list():
    try:
        df = fdr.StockListing('KRX')
        return df[['Code', 'Name']]
    except:
        # KRX 접속 실패 시 임시 데이터 반환 (프로그램 멈춤 방지)
        return pd.DataFrame({'Code':['005930', '000660'], 'Name':['삼성전자', 'SK하이닉스']})

# 3. 구글 시트 로드 함수
def load_from_gsheet():
    if "http" not in sh_url:
        return pd.DataFrame(columns=["종목명", "매수가", "수량"])
    try:
        csv_url = sh_url.replace('/edit#gid=', '/export?format=csv&gid=')
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame(columns=["종목명", "매수가", "수량"])

# 4. 템플턴 신호 로직
def get_strategy_signal(df, curr_p, buy_p=0):
    if df is None or len(df) < 20: return "분석불가", "#707070"
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    high_20 = df['High'].iloc[-20:-1].max()
    
    if buy_p == 0:
        if curr_p > high_20: return "🚨 즉시 매수", "#FF4B4B"
        return "☁️ 관망", "#1F77B4"
    else:
        profit = ((curr_p - buy_p) / buy_p * 100)
        if curr_p > ma20: return "✅ 보유", "#2EB82E"
        return "⚠️ 매도", "#FF4B4B"

# --- 메인 화면 시작 ---
stock_list = get_krx_list()

st.sidebar.title("🚀 템플턴 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🔍 종목검색", "💰 내 계좌", "📈 시장분석"])

if menu == "🔍 종목검색":
    target = st.selectbox("종목 선택", stock_list['Name'])
    if target:
        code = stock_list[stock_list['Name'] == target]['Code'].values[0]
        df = fdr.DataReader(code, (datetime.now()-timedelta(days=100)).strftime('%Y-%m-%d'))
        cp = int(df['Close'].iloc[-1])
        sig, col = get_strategy_signal(df, cp)
        st.metric(label=target, value=f"{cp:,}원", delta=sig)
        st.line_chart(df['Close'])

elif menu == "💰 내 계좌":
    st.header("나의 구글 시트 장부")
    df_pf = load_from_gsheet()
    if not df_pf.empty:
        st.table(df_pf)
    else:
        st.warning("구글 시트 주소가 올바르지 않거나 시트가 비어 있습니다.")

elif menu == "📈 시장분석":
    st.write("시장 주도주 분석 중... (이 기능은 데이터 수집량에 따라 속도가 느릴 수 있습니다.)")
