import streamlit as st
from dotenv import load_dotenv
from streamlit_option_menu import option_menu

# auth_utils의 모든 함수를 import
from auth_utils import (
    init_supabase_client, sign_up, sign_in, sign_out,
    sign_in_with_google, send_password_reset_email, update_user_password
)

# 탭 관련 함수들을 import
from giamun_tab import draw_giamun_tab
from saengibu_tab import draw_saengibu_tab
from info_search_tab import draw_info_search_tab

# .env 파일 로드
load_dotenv()

# CSS 파일 로드 함수 정의
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Supabase 클라이언트 초기화
supabase = init_supabase_client()

# 페이지 기본 설정
st.set_page_config(page_title="교실의 온도", page_icon="🌡️", layout="wide")
# CSS 파일 적용
load_css("style.css")

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI 렌더링 시작 ---

# 1. 로그인이 되지 않은 경우의 UI
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="login-title">교실의 온도 🌡️</h1>', unsafe_allow_html=True)

        login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

        with login_tab:
            with st.form("login_form"):
                st.text_input("이메일", placeholder="이메일 주소를 입력하세요", key="login_email")
                st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="login_password")
                if st.form_submit_button("로그인"):
                    email = st.session_state.login_email
                    password = st.session_state.login_password
                    status, message = sign_in(supabase, email, password)
                    if status == "success":
                        st.rerun()
                    else:
                        st.error(message)
            
            st.divider()
            st.markdown('<div class="google-login-button">', unsafe_allow_html=True)
            if st.button("Google로 로그인", use_container_width=True, key="google_login"):
                sign_in_with_google(supabase)
            st.markdown('</div>', unsafe_allow_html=True)

        with signup_tab:
            with st.form("signup_form"):
                st.text_input("사용할 이메일", key="signup_email")
                st.text_input("사용할 비밀번호", type="password", key="signup_password")
                st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
                if st.form_submit_button("회원가입"):
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
                if st.form_submit_button("재설정 링크 보내기"):
                    email = st.session_state.reset_email
                    status, message = send_password_reset_email(supabase, email)
                    if status == "success":
                        st.success(message)
                    else:
                        st.error(message)
        
        st.markdown('</div>', unsafe_allow_html=True)

# 2. 로그인이 된 경우의 UI
else:
    with st.sidebar:
        st.write(f"**{st.session_state['user'].email}**")
        st.write("환영합니다!")
        st.divider()
        selected = option_menu(
            menu_title=None,
            options=["기안문 작성", "생기부 기록", "정보 검색", "급식 식단표", "월중행사", "내 정보"],
            icons=['file-earmark-text', 'person-lines-fill', 'search', 'egg-fried', 'calendar-check', 'gear-fill'],
            menu_icon="cast", default_index=0
        )
        st.divider()
        if st.button("로그아웃", use_container_width=True):
            sign_out(supabase)
            st.rerun()

    st.title(f"AI 교사 업무 비서 🌡️ - {selected}")

    if selected == "기안문 작성":
        st.write("기안문 작성 탭 콘텐츠")
    elif selected == "생기부 기록":
        st.write("생기부 기록 탭 콘텐츠")
    elif selected == "정보 검색":
        draw_info_search_tab()
    elif selected == "내 정보":
        st.subheader("비밀번호 변경")
        with st.form("password_update_form"):
            st.text_input("새 비밀번호", type="password", key="new_password")
            st.text_input("새 비밀번호 확인", type="password", key="confirm_password")
            if st.form_submit_button("비밀번호 변경"):
                pw = st.session_state.new_password
                pw_confirm = st.session_state.confirm_password
                if not pw:
                    st.warning("새 비밀번호를 입력해주세요.")
                elif pw != pw_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    status, message = update_user_password(supabase, pw)
                    if status == "success":
                        st.success(message)
                    else:
                        st.error(message)