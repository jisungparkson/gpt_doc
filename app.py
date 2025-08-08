"""
교실의 온도 - 메인 애플리케이션
"""
import streamlit as st
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(page_title="교실의 온도", page_icon="🌡️", layout="wide")

# 세션 상태 초기화
if 'generated_texts' not in st.session_state:
    st.session_state.generated_texts = {}

# RAG 시스템 초기화 (앱 시작 시 한 번만)
if 'rag_initialized' not in st.session_state:
    st.session_state.rag_initialized = False

# CSS 커스텀 스타일
st.markdown("""
<style>
    html, body, [class*="st-"] { font-family: 'Pretendard', sans-serif; }
    .stButton > button { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem;
        font-weight: 600; transition: all 0.3s ease;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
</style>
""", unsafe_allow_html=True)

# 프롬프트 템플릿 import
from prompts import PROMPTS

# 탭별 모듈 import
from giamun_tab import draw_giamun_tab
from saengibu_tab import draw_saengibu_tab
from communication_tabs import draw_parent_reply_tab, draw_newsletter_tab
from info_search_tab import draw_info_search_tab
from meals_tab import draw_meals_tab

# 메인 앱 구성
st.title("🌡️ 교실의 온도")
st.markdown("""
<div style="background: linear-gradient(135deg, #e3f2fd 0%, #f8f9fa 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
    <h3 style="color: #1565c0; margin: 0; font-weight: 600;">차가운 행정 업무를 덜어내고, 교실에 따뜻한 온기를 더하다</h3>
    <p style="margin: 0; color: #424242; font-size: 16px; line-height: 1.6;">
        선생님의 하루를 가볍게 만들어 줄 스마트 동료입니다. 아래 탭에서 원하시는 작업을 선택해주세요.
    </p>
</div>
""", unsafe_allow_html=True)

# 기능 탭 생성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🗂️ 기안문 작성", "🏗️ 생기부 기록", "💝 학부모 답장", "🎯 가정통신문 작성", "📞 전주화정초 정보 검색", "🍽️ 급식 식단표"])

# 탭별 기능 실행
with tab1:
    draw_giamun_tab(PROMPTS)

with tab2:
    draw_saengibu_tab(PROMPTS)

with tab3:
    draw_parent_reply_tab(PROMPTS)

with tab4:
    draw_newsletter_tab(PROMPTS)

with tab5:
    draw_info_search_tab()

with tab6:
    draw_meals_tab()

# 하단 제작자 정보
st.markdown("---")
st.markdown('<div style="text-align: center; padding: 15px; color: #888;">Made by <strong>전주화정초 박성광</strong></div>', unsafe_allow_html=True)