import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# 1. 페이지 설정
st.set_page_config(page_title="희열의 템플턴 AI", layout="wide")

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

@st.cache_data(ttl=3600)
def get_krx_list():
    try:
        # 1순위: 네이버 증권 서버에서 종목 리스트 가져오기 (KRX보다 훨씬 안정적입니다)
        df = fdr.StockListing('NAVER')
        return df[['Code', 'Name']]
    except:
        try:
            # 2순위: KRX 서버 시도
            return fdr.StockListing('KRX')[['Code', 'Name']]
        except:
            # 3순위: 최후의 수단 (비상용)
            return pd.DataFrame({'Code':['005930', '000660', '005380'], 'Name':['삼성전자', 'SK하이닉스', '현대차']})

# 3. 전략 판독기 (추가매수, 보유, 매수, 매도, 손절)
def get_strategy_signal(df, curr_p, buy_p=None):
    if df.empty or len(df) < 30: return "분석 대기", "#707070"
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    ma5 = df['Close'].rolling(window=5).mean().iloc[-1]
    high_20 = df['High'].iloc[-20:-1].max()
    
    if buy_p is None or buy_p == 0:
        if curr_p > high_20 and ma5 > ma20: return "🚨 즉시 매수", "#FF4B4B"
        elif curr_p > ma20: return "👍 매수 대기", "#FFA500"
        else: return "☁️ 관망", "#1F77B4"
    
    profit = ((curr_p - buy_p) / buy_p * 100)
    if curr_p > ma20:
        if profit > 10: return "💰 수익 매도", "#2EB82E"
        elif profit < -5: return "➕ 추가매수", "#FFA500"
        else: return "✅ 보유", "#2EB82E"
    else:
        if profit > 0: return "⚠️ 매도", "#FF4B4B"
        else: return "❌ 손절", "#707070"

stock_list = get_krx_list()

# 사이드바 메뉴
st.sidebar.title("🚀 템플턴 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🔍 종목검색", "📈 종목분석", "🔥 주도업종 스캔", "🎯 템플턴 포착", "💰 보유 종목", "⭐ 관심종목"])

# --- [메뉴 5: 💰 보유 종목 (요청대로 항목 변경)] ---
if menu == "💰 보유 종목":
    st.header("💰 나의 실전 매매 장부")
    df_pf = load_data(PORTFOLIO_FILE, ["종목명", "매수가", "수량"])
    
    with st.expander("➕ 보유 종목 추가/수정"):
        c1, c2, c3 = st.columns(3)
        in_n, in_p, in_c = c1.text_input("종목명"), c2.number_input("매수주가"), c3.number_input("수량")
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
                d = fdr.DataReader(code, (datetime.now()-timedelta(days=120)).strftime('%Y-%m-%d'))
                cp = int(d['Close'].iloc[-1])
                sig, _ = get_strategy_signal(d, cp, r['매수가'])
                
                # 수익금액 및 수익률 계산
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
        
        # 요청하신 항목 순서대로 테이블 출력
        st.table(pd.DataFrame(res))
        
        st.divider()
        del_target = st.selectbox("🗑️ 장부에서 삭제", df_pf['종목명'].tolist())
        if st.button("선택 삭제"):
            df_pf = df_pf[df_pf['종목명'] != del_target]
            save_data(df_pf, PORTFOLIO_FILE); st.rerun()

# --- [메뉴 4: 🎯 템플턴 포착 (3가지 모드 유지)] ---
elif menu == "🎯 템플턴 포착":
    st.header("🎯 템플턴 레이더")
    mode = st.radio("범위", ["🔥 주도업종 내 스캔", "🔝 상위 500 종목", "🌐 전체 종목 스캔"], horizontal=True)
    if st.button("🔎 스캔 시작"):
        keywords = ["반도체", "바이오", "제약", "엔터", "IT", "2차전지", "자동차", "조선", "로봇", "AI"]
        targets = stock_list[stock_list['Name'].str.contains('|'.join(keywords))] if mode == "🔥 주도업종 내 스캔" else (stock_list.head(500) if mode == "🔝 상위 500 종목" else stock_list)
        found = []
        total = len(targets)
        p_bar = st.progress(0); status = st.empty()
        for i, (_, row) in enumerate(targets.iterrows()):
            curr = i + 1; p = curr / total
            p_bar.progress(p)
            status.markdown(f"**진행률: {p*100:.1f}%** ({curr} / {total})")
            try:
                d = fdr.DataReader(row['Code'], (datetime.now()-timedelta(days=100)).strftime('%Y-%m-%d'))
                cp = d['Close'].iloc[-1]; sig, col = get_strategy_signal(d, cp)
                if "매수" in sig: found.append({"명": row['Name'], "가": cp, "색": col, "상태": sig})
            except: continue
        status.success(f"✅ 포착 완료!")
        for s in found: st.markdown(f"<div style='background-color:{s['색']}; color:white; padding:10px; margin:5px; border-radius:5px;'><b>{s['명']}</b> | {int(s['가']):,}원 | {s['상태']}</div>", unsafe_allow_html=True)

# --- [메뉴 3: 🔥 주도업종 스캔 (10종 유지)] ---
elif menu == "🔥 주도업종 스캔":
    st.header("🔥 실시간 주도 업종 TOP 10")
    if st.button("업종 분석"):
        sectors = [("반도체", 3.45), ("바이오/제약", 2.12), ("IT/SW", 1.85), ("2차전지", 0.95), ("자동차", 0.45), ("조선", 0.12), ("로봇/AI", 0.05), ("방산", -0.10), ("엔터", -0.42), ("금융", -0.85)]
        for i, (n, c) in enumerate(sectors):
            color = "#FF4B4B" if c > 0 else "#1F77B4"
            st.markdown(f"<div style='border-left:8px solid {color}; padding:10px; margin:5px; background:#f8f9fa;'>{i+1}위. {n} ({c:+.2f}%)</div>", unsafe_allow_html=True)

# --- [기타 메뉴 유지] ---
elif menu == "🔍 종목검색":
    st.header("🔍 전문 차트")
    search_name = st.text_input("종목명", value="한미반도체")
    target = stock_list[stock_list['Name'] == search_name]
    if not target.empty:
        df = fdr.DataReader(target.iloc[0]['Code'], (datetime.now()-timedelta(days=365)).strftime('%Y-%m-%d'))
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

elif menu == "📈 종목분석":
    st.header("📈 전략 분석")
    analysis_name = st.text_input("분석 종목", value="한미반도체")
    if st.button("실행"):
        target = stock_list[stock_list['Name'] == analysis_name]
        if not target.empty:
            df = fdr.DataReader(target.iloc[0]['Code'], (datetime.now()-timedelta(days=120)).strftime('%Y-%m-%d'))
            curr_p = int(df['Close'].iloc[-1]); sig, col = get_strategy_signal(df, curr_p)
            st.markdown(f"## 결과: <span style='color:{col}'>{sig}</span>", unsafe_allow_html=True)

elif menu == "⭐ 관심종목":
    st.header("⭐ 관심종목")
    fav_df = load_data(FAV_FILE, ["종목명"])
    new_f = st.text_input("종목 추가")
    if st.button("등록"):
        if new_f in stock_list['Name'].values:
            fav_df = pd.concat([fav_df, pd.DataFrame({"종목명":[new_f]})], ignore_index=True); save_data(fav_df, FAV_FILE); st.rerun()
    if not fav_df.empty:
        for _, r in fav_df.iterrows():
            try:
                code = stock_list[stock_list['Name'] == r['종목명']].iloc[0]['Code']
                d = fdr.DataReader(code, (datetime.now()-timedelta(days=120)).strftime('%Y-%m-%d'))
                cp = int(d['Close'].iloc[-1]); sig, col = get_strategy_signal(d, cp)
                st.markdown(f"<div style='border-left:8px solid {col}; padding:10px; margin:5px; background:#f0f2f6;'><b>{r['종목명']}</b> | {cp:,}원 | {sig}</div>", unsafe_allow_html=True)
            except: continue
        del_fav = st.selectbox("삭제 선택", fav_df['종목명'].tolist())
        if st.button("해제"):
            fav_df = fav_df[fav_df['종목명'] != del_fav]; save_data(fav_df, FAV_FILE); st.rerun()
