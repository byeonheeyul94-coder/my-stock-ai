import streamlit as st
import pandas as pd
from shillelagh.backends.apsw.db import connect

# 1. 설정: 희열님의 구글 시트 URL (공유 설정: 링크가 있는 모든 사용자)
SHEET_URL = "https://docs.google.com/spreadsheets/d/본인의_시트_아이디/edit#gid=0"

@st.cache_data(ttl=60) # 1분마다 데이터 갱신
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

# 앱 레이아웃 설정
st.set_page_config(page_title="희열의 템플턴 v3.0", layout="wide")
st.title("🚀 희열의 템플턴 실전 투자 시스템 v3.0")

# --- [섹션 1] 업종별 주도주 및 상세 브리핑 ---
st.header("📂 업종별 주도주 및 상세 브리핑")
col1, col2 = st.columns([1, 1])

# 업종 데이터 (기존 PyQt 버튼 기능 대체)
sector_data = {
    '반도체': ['한미반도체', 'SK하이닉스', '에스앤에스텍'],
    '배터리': ['에코프로', 'LG에너지솔루션', '포스코홀딩스'],
    '자동차': ['현대로템', '현대차', '기아'],
    '로봇': ['로보티즈', '레인보우로보틱스', '엔젤로보틱스']
}

with col1:
    st.write("#### 📂 업종 선택")
    # PyQt의 가로 버튼 배열을 라디오 버튼으로 구현
    selected_sector = st.radio("업종을 선택하세요", list(sector_data.keys()), horizontal=True)
    
    # 선택된 업종의 종목 리스트 (PyQt의 QTableWidget 역할)
    st.write(f"**[{selected_sector}] 주도주 리스트**")
    selected_stock = st.selectbox("분석할 종목을 선택하세요", sector_data[selected_sector])

with col2:
    st.write("#### 📖 템플턴의 종목 정밀 분석")
    # PyQt의 QTextEdit(상세 설명) 기능 구현
    st.info(f"""
    **★ {selected_stock} 상세 분석 결과**
    - **협업**: 해당 분야 1위 기업과 전략적 기술 제휴 중
    - **호재**: 템플턴 매수 신호 포착 및 흑자 전환 성공
    - **계약**: 최근 300억 규모 공급계약 완료 및 추가 수주 대기
    """)

st.divider()

# --- [섹션 2] 나만의 매수 종목 관리 (포트폴리오) ---
st.header("💰 나의 포트폴리오 (매도/추매 가이드)")

# 데이터 로드
df = load_data()

if not df.empty:
    # 데이터 전처리 (콤마 제거 및 숫자 변환)
    for col in ['매수가', '현재가']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # 수익률 및 가이드 계산
    df['수익률'] = (df['현재가'] - df['매수가']) / df['매수가']
    
    def get_guide(x):
        if x > 0.1: return "💰 수익 매도 검토"
        elif x < -0.05: return "⚠️ 추가매수/관리"
        else: return "✅ 보유(신호 유지)"
    
    df['투자 가이드'] = df['수익률'].apply(get_guide)

    # 표 출력 (PyQt의 QTableWidget)
    st.dataframe(df.style.format({
        '매수가': '{:,.0f}원', 
        '현재가': '{:,.0f}원', 
        '수익률': '{:+.2%}'
    }), use_container_width=True)
else:
    st.warning("구글 시트 데이터를 불러올 수 없습니다. URL과 공유 설정을 확인하세요.")

# --- [섹션 3] 내 종목 등록 (입력창 기능) ---
st.divider()
st.sidebar.header("➕ 내 종목 등록")
# Streamlit 배포 시 입력창은 구글 시트로 바로 연결하는 것이 가장 오류가 적습니다.
st.sidebar.write("새 종목은 구글 시트에서 직접 입력하세요.")
st.sidebar.link_button("나의 구글 시트 열기", SHEET_URL)
st.sidebar.caption("시트에 입력 후 1분 뒤 앱에 반영됩니다.")
