"""
학부모 답장 및 가정통신문 탭
"""
import streamlit as st
from utils import run_chain_and_display

def draw_parent_reply_tab(prompts):
    """학부모 답장 탭 UI"""
    st.header("✉️ 학부모 답장 도우미")
    st.markdown("학부모님의 메시지와 답장의 핵심 방향을 입력하면, 따뜻하고 전문적인 답장 초안을 만들어 드립니다.")
    with st.container(border=True):
        parent_message = st.text_area("학부모님 메시지 원문", placeholder="이곳에 학부모님께 받은 메시지를 그대로 붙여넣어 주세요.", height=150)
        tone = st.text_input("답장 어조 및 핵심 방향", placeholder="예: 따뜻하고 공감적으로, 해결 방안 중심으로, 긍정적인 면을 부각하여")

        if st.button("✨ 답장 초안 생성", use_container_width=True, key="parent_reply"):
            if all([parent_message, tone]):
                # 고유한 세션 키 생성
                session_key = f"parent_reply_{hash(parent_message + tone)}"
                run_chain_and_display(session_key, "parent_reply", {"parent_message": parent_message, "tone": tone}, st, prompts)
            else: st.warning("모든 항목을 입력해주세요.")

def draw_newsletter_tab(prompts):
    """가정통신문 탭 UI"""
    st.header("📢 가정통신문 작성 도우미")
    st.markdown("현장체험학습 등의 핵심 내용만 입력하면 완성된 가정통신문을 생성합니다.")
    
    with st.container(border=True):
        main_points = st.text_area(
            "전달할 핵심 내용", 
            placeholder="현장체험학습 관련 핵심 내용을 간단히 입력해주세요.\n\n예시:\n• 10월 15일(수) 민속촌 견학\n• 5학년 대상, 참가비 3만원\n• 9월 30일까지 신청",
            height=150
        )

        if st.button("✨ 가정통신문 생성", use_container_width=True, key="newsletter"):
            if main_points.strip():
                # 고유한 세션 키 생성
                session_key = f"newsletter_{hash(main_points)}"
                run_chain_and_display(session_key, "newsletter", {
                    "title": "현장체험학습 안내", 
                    "grade": "해당 학년", 
                    "main_points": main_points, 
                    "school_name": "OO초등학교"
                }, st, prompts)
            else: 
                st.warning("핵심 내용을 입력해주세요.")