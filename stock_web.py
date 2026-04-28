import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="희열의 템플턴 AI v2.0", layout="wide")

# 2. 데이터 관리 함수
PORTFOLIO_FILE = 'my_portfolio.csv'
FAV_FILE = 'my_favorites.csv'

def load_data(file_path, default_cols):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            for col in default_cols:
                if col not in df.columns: df[col] = 0 if col != "종목명" else "알수없음"
            return df[default_cols]
        except: return pd.DataFrame(columns=default_cols)
    return pd.DataFrame(columns=default_cols)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# [수정] KRX 에러 방지를 위한 안정적 호출 방식
@st.cache_data(ttl=3600)
def get_krx_list():
    try:
        # 코스피와 코스닥을 합쳐서 가져오는 방식이 더 안정적입니다
        kospi = fdr.StockListing('KOSPI')
        kosdaq = fdr.StockListing('KOSDAQ')
        combined = pd.concat([kospi, kosdaq])
        return combined[['Code', 'Name']]
    except:
        # 비상시 KRX 전체 리스트 재시도
        return fdr.StockListing('KRX')[['Code', 'Name']]

# --- [학습 반영] 3. 템플턴 공부 원칙 기반 전략 판독기 ---
def get_strategy_signal(df, curr_p, buy_p=None):
    if df.empty or len(df) < 120: return "데이터 부족", "#707070"
    
    # [원칙 8, 9, 24] 이동평균선 설정 (60일선은 추세선)
    ma5 = df['Close'].rolling(window=5).mean().iloc[-1]
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
    ma120 = df['Close'].rolling(window=120).mean().iloc[-1]
    
    # [원칙 37] 6개월(약 120일) 전고점 돌파 확인
    high_6m = df['High'].iloc[-120:-1].max()
    
    # [원칙 6] 정배열 확인 (5 > 20 > 60 > 120)
    is_upward = ma5 > ma20 > ma60 > ma120
    
    # 매수 신호 로직
    if buy_p is None or buy_p == 0:
        if curr_p > high_6m: return "🚀 전고점 돌파 (눈감고 매수)", "#FF4B4B"
        if curr_p > ma60 and is_upward: return "🔥 정배열 추세전환", "#FF4B4B"
        if curr_p > ma20: return "👍 매수 대기", "#FFA500"
        return "☁️ 관망", "#1F77B4"
    
    # [원칙 19, 39] 보유/매도/손절 분석 (60일선 기준)
    profit = ((curr_p - buy_p) / buy_p * 100)
    if curr_p < ma60:
        return "❌ 60일선 붕괴 (단호한 손절)", "#707070" if profit < 0 else "⚠️ 매도 (추세종료)", "#FF4B4B"
    
    if profit > 15: return "💰 수익 매도 (ROE 15%급)", "#2EB82E"
    if profit < -5: return "➕ 추가매수 구간", "#FFA500"
    return "✅ 보유 (추세 우상향)", "#2EB82E"

stock_list = get_krx_list()

# 사이드바 메뉴
st.sidebar.title("🚀 템플턴 v2.0")
menu = st.sidebar.radio("메뉴 이동", ["🔍 종목검색", "📈 전략분석", "🎯 템플턴 포착", "💰 보유 종목", "⭐ 관심종목"])

# --- [메뉴: 💰 보유 종목] ---
if menu == "💰 보유 종목":
    st.header("💰 나의 실전 매매 장부")
    df_pf = load_data(PORTFOLIO_FILE, ["종목명", "매수가", "수량"])
    
    with st.expander("➕ 보유 종목 추가/수정"):
        c1, c2, c3 = st.columns(3)
        in_n, in_p, in_c = c1.text_input("종목명"), c2.number_input("매수가"), c3.number_input("수량")
        if st.button("장부 저장"):
            if in_n in stock_list['Name'].values:
                if in_n in df_pf['종목명'].values: 
                    df_pf.loc[df_pf['종목명'] == in_n, ['매수가', '수량']] = [in_p, in_c]
                else: 
                    df_pf = pd.concat([df_pf, pd.DataFrame({"종목명":[in_n], "매수가":[in_p], "수량":[in_c]})], ignore_index=True)
                save_data(df_pf, PORTFOLIO_FILE); st.rerun()

    if not df_pf.empty:
        res = []
        for _, r in df_pf.iterrows():
            try:
                code = stock_list[stock_list['Name'] == r['종목명']].iloc[0]['Code']
                d = fdr.DataReader(code, (datetime.now()-timedelta(days=200)).strftime('%Y-%m-%d'))
                cp = int(d['Close'].iloc[-1])
                sig = get_strategy_signal(d, cp, r['매수가'])[0]
                p_amount = int((cp - r['매수가']) * r['수량'])
                p_rate = ((cp - r['매수가']) / r['매수가'] * 100)
                res.append({"종목명": r['종목명'], "매수가": f"{int(r['매수가']):,}원", "현재가": f"{cp:,}원", "수익금": f"{p_amount:+,}원", "수익률": f"{p_rate:+.2f}%", "전략 알람": sig})
            except: continue
        st.table(pd.DataFrame(res))

# --- [메뉴: 🔍 종목검색] ---
elif menu == "🔍 종목검색":
    st.header("🔍 전문 차트 (60일 추세선 포함)")
    search_name = st.text_input("종목명", value="한미반도체")
    target = stock_list[stock_list['Name'] == search_name]
    if not target.empty:
        df = fdr.DataReader(target.iloc[0]['Code'], (datetime.now()-timedelta(days=365)).strftime('%Y-%m-%d'))
        df['MA60'] = df['Close'].rolling(window=60).mean() # 60일선 추가
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="주가")])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='orange', width=2), name="60일 추세선"))
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# --- [메뉴: 🎯 템플턴 포착] ---
elif menu == "🎯 템플턴 포착":
    st.header("🎯 템플턴 레이더 (원칙 37번 전고점 돌파)")
    if st.button("🔎 스캔 시작"):
        targets = stock_list.head(300) # 속도를 위해 상위 300개 우선 스캔
        found = []
        p_bar = st.progress(0)
        for i, (_, row) in enumerate(targets.iterrows()):
            p_bar.progress((i + 1) / len(targets))
            try:
                d = fdr.DataReader(row['Code'], (datetime.now()-timedelta(days=150)).strftime('%Y-%m-%d'))
                cp = int(d['Close'].iloc[-1])
                sig, col = get_strategy_signal(d, cp)
                if "매수" in sig or "돌파" in sig:
                    found.append({"명": row['Name'], "가": cp, "색": col, "상태": sig})
            except: continue
        for s in found:
            st.markdown(f"<div style='background-color:{s['색']}; color:white; padding:10px; margin:5px; border-radius:5px;'><b>{s['명']}</b> | {s['가']:,}원 | {s['상태']}</div>", unsafe_allow_html=True)
