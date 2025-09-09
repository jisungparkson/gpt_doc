import streamlit as st
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
from auth_utils import *

load_dotenv()

# --- 페이지 설정 및 초기화 ---
st.set_page_config(page_title="교실의 온도", page_icon="🌡️", layout="wide")
with open("style.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'view' not in st.session_state:
    st.session_state['view'] = 'dashboard'

# Supabase 클라이언트 초기화
supabase = init_supabase_client()

# --- UI 컴포넌트 ---
def render_login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        # 이 container가 제목과 폼을 모두 포함하는 최종 카드임
        with st.container():
            # 제목
            st.markdown('<h1 class="login-title-in-card">교실의 온도 🌡️</h1>', unsafe_allow_html=True)
            
            # 탭 메뉴와 폼
            login_tab, signup_tab = st.tabs(["로그인", "회원가입"])
            
            with login_tab:
                with st.form("login_form"):
                    st.text_input("이메일", placeholder="이메일 주소를 입력하세요", key="login_email")
                    st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="login_password")
                    if st.form_submit_button("로그인", use_container_width=True):
                        email = st.session_state.login_email
                        password = st.session_state.login_password
                        status, message = sign_in(supabase, email, password)
                        if status == "success":
                            st.session_state['view'] = 'dashboard'
                            st.rerun()
                        else:
                            st.error(message)
                
                st.divider()
                
                if st.button("Google로 로그인", use_container_width=True, key="google_login"):
                    sign_in_with_google(supabase)
            
            with signup_tab:
                with st.form("signup_form"):
                    st.text_input("사용할 이메일", key="signup_email")
                    st.text_input("사용할 비밀번호", type="password", key="signup_password")
                    st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
                    if st.form_submit_button("회원가입", use_container_width=True):
                        email = st.session_state.signup_email
                        pw = st.session_state.signup_password
                        pw_confirm = st.session_state.signup_password_confirm
                        if pw != pw_confirm:
                            st.error("비밀번호가 일치하지 않습니다.")
                        else:
                            status, message = sign_up(supabase, email, pw)
                            if status == "success":
                                st.success(message)
                            else:
                                st.error(message)

            with st.expander("비밀번호를 잊으셨나요?"):
                with st.form("password_reset_form"):
                    st.text_input("가입한 이메일 주소", key="reset_email")
                    if st.form_submit_button("재설정 링크 보내기", use_container_width=True):
                        email = st.session_state.reset_email
                        status, message = send_password_reset_email(supabase, email)
                        if status == "success":
                            st.success(message)
                        else:
                            st.error(message)

def render_dashboard():
    # 1. 상단 메뉴 및 사용자 정보
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = option_menu(
            menu_title=None,
            options=["홈", "기안문 작성", "생기부 기록", "정보 검색", "내 정보"],
            icons=['house-door', 'pencil-square', 'person-lines-fill', 'search', 'gear'],
            orientation="horizontal",
            styles={
                "container": {"padding": "0 !important", "background-color": "transparent"},
                "nav-link": {"font-weight": "600"},
                "nav-link-selected": {"background-color": "#4F46E5", "color": "white"},
            }
        )
    with col2:
        st.markdown('<div class="user-menu-container">', unsafe_allow_html=True)
        user_email = st.session_state.get('user', {}).email
        st.markdown(f'<span class="user-email">{user_email}</span>', unsafe_allow_html=True)
        if st.button("로그아웃", key="main_logout_btn"):
            sign_out(supabase)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()

    # 2. 선택된 메뉴에 따른 콘텐츠 표시
    if selected == "홈":
        # 환영 메시지 카드
        with st.container(border=True):
            user_email = st.session_state.get('user', {}).email
            st.header(f"안녕하세요, {user_email.split('@')[0]}님! 👋")
            st.write("AI 교사 업무 비서가 선생님의 하루를 도와드립니다.")
        
        st.subheader("🎯 주요 기능 요약")
        
        # 주요 기능 카드를 3열로 배치
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True):
                st.markdown("#### ✍️ 기안문")
                st.markdown("- 공문서 양식에 맞는 기안문 자동 생성")
                st.markdown("- 학생별 생활기록부 작성 지원")
                if st.button("기안문 작성하기", key="card_btn_1", use_container_width=True):
                    st.rerun()
        
        with cols[1]:
            with st.container(border=True):
                st.markdown("#### 📚 생기부")
                st.markdown("- 개별 맞춤 학생 관리")
                st.markdown("- 개별 맞춤 생기부 작성")
                if st.button("생기부 기록하기", key="card_btn_2", use_container_width=True):
                    st.rerun()
        
        with cols[2]:
            with st.container(border=True):
                st.markdown("#### 🔍 실시간 정보 검색")
                st.markdown("- 학교 정보 검색: 교육 관련 정보 검색")
                st.markdown("- 급식 식단표: 학교별 급식 메뉴 조회")
                if st.button("정보 검색하기", key="card_btn_3", use_container_width=True):
                    st.rerun()
    
    elif selected == "기안문 작성":
        st.title("기안문 작성")
        from giamun_tab import draw_giamun_tab
        draw_giamun_tab()
    
    elif selected == "생기부 기록":
        st.title("생기부 기록")
        from saengibu_tab import draw_saengibu_tab
        draw_saengibu_tab()
    
    elif selected == "정보 검색":
        st.title("정보 검색")
        from info_search_tab import draw_info_search_tab
        draw_info_search_tab()
    
    elif selected == "내 정보":
        st.title("내 정보")
        with st.container(border=True):
            user_email = st.session_state.get('user', {}).email
            st.subheader("사용자 정보")
            st.write(f"**이메일:** {user_email}")
            created_at = st.session_state.get('user', {}).created_at if hasattr(st.session_state.get('user', {}), 'created_at') else '정보 없음'
            st.write(f"**가입일:** {created_at}")

# --- 메인 실행 로직 ---
if st.session_state.logged_in:
    render_dashboard()
else:
    render_login_page()