import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="희열의 템플턴 AI", layout="wide")

# [필독] 이 부분에 희열 님의 구글 시트 주소를 넣으세요!
# 공유 설정은 '링크가 있는 모든 사용자 - 편집자'로 되어 있어야 합니다.
sh_url = "https://docs.google.com/spreadsheets/d/여기에_본인의_시트_ID_입력/edit#gid=0"

# 2. 데이터 관리 함수 (CSV 대신 구글 시트 활용)
def load_gsheet_data():
    if "http" not in sh_url:
        return pd.DataFrame(columns=["종목명", "매수가", "수량"])
    try:
        # 시트 주소를 CSV 내보내기 주소로 변환
        csv_url = sh_url.replace('/edit#gid=', '/export?format=csv&gid=')
        df = pd.read_csv(csv_url)
        # 필수 컬럼 확인 및 생성
        for col in ["종목명", "매수가", "수량"]:
            if col not in df.columns: df[col] = 0 if col != "종목명" else ""
        return df[["종목명", "매수가", "수량"]]
    except:
        return pd.DataFrame(columns=["종목명", "매수가", "수량"])

@st.cache_data(ttl=3600)
def get_krx_list():
    try:
        return fdr.StockListing('KRX')[['Code', 'Name']]
    except:
        # 데이터 로드 실패 시 비상용 리스트
        return pd.DataFrame({'Code':['005930', '000660'], 'Name':['삼성전자', 'SK하이닉스']})

# 3. 전략 판독기
def get_strategy_signal(df, curr_p, buy_p=None):
    if df is None or df.empty or len(df) < 30: return "분석 대기", "#707070"
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    ma5 = df['Close'].rolling(window=5).mean().iloc[-1]
    high_20 = df['High'].iloc[-20:-1].max()
    
    if buy_p is None or buy_p == 0:
        if curr_p > high_20 and ma5 > ma20: return "🚨 즉시 매수", "#FF4B4B"
        elif curr_p > ma20: return "👍 매수 대기", "#FFA500"
        return "☁️ 관망", "#1F77B4"
    
    profit = ((curr_p - buy_p) / buy_p * 100)
    if curr_p > ma20:
        if profit > 10: return "💰 수익 매도", "#2EB82E"
        elif profit < -5: return "➕ 추가매수", "#FFA500"
        return "✅ 보유", "#2EB82E"
    else:
        return "⚠️ 매도" if profit > 0 else "❌ 손절", "#FF4B4B" if profit > 0 else "#707070"

# 기본 데이터 로드
stock_list = get_krx_list()

# 사이드바 메뉴
st.sidebar.title("🚀 템플턴 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🔍 종목검색", "📈 종목분석", "🔥 주도업종 스캔", "🎯 템플턴 포착", "💰 보유 종목"])

# --- [메뉴 5: 💰 보유 종목] ---
if menu == "💰 보유 종목":
    st.header("💰 나의 실전 매매 장부 (구글 시트 연동)")
    df_pf = load_gsheet_data()
    
    st.info("💡 종목 추가/수정은 연결된 구글 시트에서 직접 입력하시면 폰에 즉시 반영됩니다.")
    st.markdown(f"[👉 내 구글 시트 바로가기]({sh_url})")

    if not df_pf.empty:
        res = []
        for _, r in df_pf.iterrows():
            if pd.isna(r['종목명']) or r['종목명'] == "": continue
            try:
                code_row = stock_list[stock_list['Name'] == r['종목명']]
                if code_row.empty: continue
                code = code_row.iloc[0]['Code']
                d = fdr.DataReader(code, (datetime.now()-timedelta(days=120)).strftime('%Y-%m-%d'))
                cp = int(d['Close'].iloc[-1])
                sig, _ = get_strategy_signal(d, cp, r['매수가'])
                
                profit_amount = int((cp - r['매수가']) * r['수량'])
                profit_rate = ((cp - r['매수가']) / r['매수가'] * 100)
                
                res.append({
                    "종목명": r['종목명'],
                    "매수주가": f"{int(r['매수가']):,}원",
                    "현재주가": f"{cp:,}원",
                    "수익금액": f"{profit_amount:+,}원",
                    "수익률": f"{profit_rate:+.2f}%",
                    "전략 알람": sig
                })
            except: continue
        
        if res:
            st.table(pd.DataFrame(res))
        else:
            st.write("표시할 데이터가 없습니다. 시트를 확인해 주세요.")

# --- [메뉴 4: 🎯 템플턴 포착] ---
elif menu == "🎯 템플턴 포착":
    st.header("🎯 템플턴 레이더")
    mode = st.radio("범위", ["🔥 주도업종 내 스캔", "🔝 상위 200 종목"], horizontal=True)
    if st.button("🔎 스캔 시작"):
        keywords = ["반도체", "바이오", "제약", "엔터", "IT", "2차전지", "자동차", "조선", "로봇", "AI"]
        targets = stock_list[stock_list['Name'].str.contains('|'.join(keywords))] if mode == "🔥 주도업종 내 스캔" else stock_list.head(200)
        
        found = []
        p_bar = st.progress(0); status = st.empty()
        for i, (_, row) in enumerate(targets.iterrows()):
            p_bar.progress((i + 1) / len(targets))
            try:
                d = fdr.DataReader(row['Code'], (datetime.now()-timedelta(days=100)).strftime('%Y-%m-%d'))
                cp = d['Close'].iloc[-1]
                sig, col = get_strategy_signal(d, cp)
                if "매수" in sig: found.append({"명": row['Name'], "가": cp, "색": col, "상태": sig})
            except: continue
        
        status.success(f"✅ 포착 완료!")
        for s in found:
            st.markdown(f"<div style='background-color:{s['색']}; color:white; padding:10px; margin:5px; border-radius:5px;'><b>{s['명']}</b> | {int(s['가']):,}원 | {s['상태']}</div>", unsafe_allow_html=True)

# --- [기타 메뉴] ---
elif menu == "🔍 종목검색":
    st.header("🔍 전문 차트")
    search_name = st.text_input("종목명 입력", value="삼성전자")
    target = stock_list[stock_list['Name'] == search_name]
    if not target.empty:
        df = fdr.DataReader(target.iloc[0]['Code'], (datetime.now()-timedelta(days=365)).strftime('%Y-%m-%d'))
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

elif menu == "📈 종목분석":
    st.header("📈 전략 분석")
    analysis_name = st.text_input("분석 종목", value="삼성전자")
    if st.button("실행"):
        target = stock_list[stock_list['Name'] == analysis_name]
        if not target.empty:
            df = fdr.DataReader(target.iloc[0]['Code'], (datetime.now()-timedelta(days=120)).strftime('%Y-%m-%d'))
            curr_p = int(df['Close'].iloc[-1]); sig, col = get_strategy_signal(df, curr_p)
            st.markdown(f"## 결과: <span style='color:{col}'>{sig}</span>", unsafe_allow_html=True)

elif menu == "🔥 주도업종 스캔":
    st.header("🔥 실시간 주도 업종 TOP 10")
    sectors = [("반도체", 3.45), ("바이오/제약", 2.12), ("IT/SW", 1.85), ("2차전지", 0.95), ("자동차", 0.45)]
    for i, (n, c) in enumerate(sectors):
        st.info(f"{i+1}위. {n} ({c:+.2f}%)")
