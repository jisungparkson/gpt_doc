import os
import streamlit as st
from supabase import create_client, Client

def init_supabase_client():
    """
    Supabase 클라이언트를 초기화하고 Streamlit 세션 상태에 저장합니다.
    """
    if 'supabase_client' not in st.session_state:
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        st.session_state.supabase_client = create_client(url, key)
    return st.session_state.supabase_client

def sign_up(supabase: Client, email, password):
    """
    Supabase를 이용한 회원가입 함수
    """
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        return "success", "회원가입이 완료되었습니다. 로그인해주세요."
    except Exception as e:
        # 오류 메시지를 파싱하여 사용자에게 친화적인 메시지 반환
        error_message = str(e)
        if "User already registered" in error_message:
            return "error", "이미 등록된 이메일입니다."
        elif "Password should be at least 6 characters" in error_message:
            return "error", "비밀번호는 6자 이상이어야 합니다."
        return "error", f"회원가입 중 오류가 발생했습니다: {e}"


def sign_in(supabase: Client, email, password):
    """
    Supabase를 이용한 로그인 함수
    """
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state['logged_in'] = True
        st.session_state['user'] = res.user
        return "success", "로그인에 성공했습니다."
    except Exception as e:
        return "error", "이메일 또는 비밀번호가 잘못되었습니다."

def sign_out(supabase: Client):
    """
    Supabase를 이용한 로그아웃 함수
    """
    supabase.auth.sign_out()
    st.session_state['logged_in'] = False
    st.session_state.pop('user', None)