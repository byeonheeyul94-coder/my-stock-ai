import streamlit as st
import pandas as pd
from shillelagh.backends.apsw.db import connect

# 1. [중요] 희열 님의 구글 시트 주소로 꼭 바꾸세요!
# 시트 공유 설정: '링크가 있는 모든 사용자'로 되어 있어야 합니다.
SHEET_URL = "https://docs.google.com/spreadsheets/d/본인의_시트_아이디/edit#gid=0"

@st.cache_data(ttl=60) # 1분마다 자동 새로고침
def load_data():
    try:
        conn = connect(":memory:")
        query = f'SELECT * FROM "{SHEET_URL}"'
        cursor = conn.cursor()
        cursor.execute(query)
        cols = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=cols)
    except Exception as e:
        st.error(f"시트 연결 에러: {e}")
        return pd.DataFrame()

# --- 앱 화면 구성 (희열의 템플턴 v3.0) ---
st.set_page_config(page_title="희열의 템플턴 v3.0", layout="wide")
st.title("🚀 희열의 템플턴 실전 투자 시스템")

# 사이드바 메뉴 (기존 PyQt6의 버튼 기능)
st.sidebar.header("📂 업종 분석")
sector = st.sidebar.selectbox("주도주 선택", ["반도체", "배터리", "자동차", "로봇"])

# 업종 상세 설명
st.info(f"### 📖 {sector} 업종 정밀 분석\n- **호재**: 흑자전환 및 수주 확대\n- **계약**: 대규모 공급계약 완료 건 분석 중")

# 나의 포트폴리오
st.subheader("💰 나의 실시간 매매 장부")
df = load_data()

if not df.empty:
    # 데이터 정리 (콤마 제거 및 숫자 변환)
    for col in ['매수가', '현재가']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # 수익률 계산 및 가이드
    if '매수가' in df.columns and '현재가' in df.columns:
        df['수익률'] = (df['현재가'] - df['매수가']) / df['매수가']
        df['투자 가이드'] = df['수익률'].apply(lambda x: "💰 익절 검토" if x > 0.1 else ("⚠️ 추매/손절" if x < -0.05 else "✅ 보유"))

    # 표 출력
    st.dataframe(df.style.format({
        '매수가': '{:,.0f}원', 
        '현재가': '{:,.0f}원', 
        '수익률': '{:+.2%}'
    }), use_container_width=True)
else:
    st.warning("구글 시트에서 데이터를 불러올 수 없습니다. URL과 공유 설정을 확인하세요!")
