import streamlit as st
import pandas as pd
from shillelagh.backends.apsw.db import connect

# 📍 [필수 수정] 희열님의 구글 시트 주소
SHEET_URL = "https://docs.google.com/spreadsheets/d/본인의_시트_아이디/edit#gid=0"

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = connect(":memory:")
        query = f'SELECT * FROM "{SHEET_URL}"'
        cursor = conn.cursor()
        cursor.execute(query)
        cols = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=cols)
    except:
        return pd.DataFrame()

# 앱 설정
st.set_page_config(page_title="희열의 템플턴 v3.0", layout="wide")
st.title("🚀 희열의 템플턴 실전 투자 시스템")

# --- [섹션 1] 업종별 주도주 및 상세 브리핑 (기존 상단 메뉴) ---
st.header("📂 업종별 주도주 및 상세 브리핑")
col1, col2 = st.columns([1, 1])

with col1:
    st.write("### 업종 선택")
    # PyQt의 버튼 기능을 셀렉트박스로 구현 (폰 최적화)
    sector = st.radio("업종을 선택하세요", ['반도체', '배터리', '자동차', '로봇'], horizontal=True)
    
    # 예시 데이터 (나중에 DB 연결 가능)
    st.write(f"**{sector} 관련주 리스트**")
    stocks = {
        '반도체': ['한미반도체', 'SK하이닉스', '에스앤에스텍'],
        '배터리': ['에코프로', 'LG에너지솔루션'],
        '자동차': ['현대로템', '현대차'],
        '로봇': ['로보티즈', '레인보우로보틱스']
    }
    selected_stock = st.selectbox("상세 분석할 종목 선택", stocks[sector])

with col2:
    st.write("### 📖 템플턴 정밀 분석")
    # PyQt의 QTextEdit 기능을 여기에 구현
    st.info(f"""
    **★ {selected_stock} 상세 분석**
    - **협업**: 주요 기업과 기술 제휴 및 협업 진행 중
    - **호재**: 업종 내 주도주로서 흑자전환 및 수주 확대
    - **계약**: 대규모 공급계약 완료 및 추가 공시 대기
    """)

st.divider()

# --- [섹션 2] 나만의 매수 종목 관리 (기존 하단 포트폴리오) ---
st.header("💰 나의 포트폴리오 (매도/추매 가이드)")

df = load_data()
if not df.empty:
    # 데이터 전처리
    for col in ['매수가', '현재가']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # 수익률 및 가이드 로직
    df['수익률'] = (df['현재가'] - df['매수가']) / df['매수가']
    df['투자 가이드'] = df['수익률'].apply(lambda x: "💰 익절 검토" if x > 0.1 else ("⚠️ 추매/손절" if x < -0.05 else "✅ 보유"))

    # 표 출력 (PyQt의 QTableWidget)
    st.dataframe(df.style.format({
        '매수가': '{:,.0f}원', 
        '현재가': '{:,.0f}원', 
        '수익률': '{:+.2%}'
    }), use_container_width=True)
else:
    st.warning("구글 시트 데이터를 불러올 수 없습니다.")

# --- [섹션 3] 내 종목 등록 (기존 입력창 기능) ---
st.sidebar.header("➕ 내 종목 등록")
st.sidebar.write("새로운 종목을 추가하려면 아래 버튼을 눌러 구글 시트로 이동하세요.")
st.sidebar.link_button("구글 시트 열기", SHEET_URL)
st.sidebar.caption("시트에 종목명, 코드, 매수가를 적으면 앱에 실시간 반영됩니다.")
