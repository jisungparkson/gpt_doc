"""
기안문 작성 탭 - 단순하고 안정적인 버전
.env 파일에서 API 키를 직접 로드하고, giamun_helper.py 함수들을 순서대로 호출
JsonOutputParser나 복잡한 체인 없이 가장 검증된 방식 사용
"""
import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
from giamun_helper import create_giamun_prompt_for_gpt, call_openai_api_for_text


def draw_giamun_tab(prompts):
    st.header("✍️ 기안문 작성 도우미")

    # .env 파일에서 API 키 로드
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    with st.container(border=True):
        st.markdown("💡 **간단 입력 모드**: 핵심 정보만 입력하면 AI가 완전한 기안문을 자동으로 작성해드립니다!")

        giamun_type = st.selectbox(
            "작성할 기안문 유형을 선택하세요.",
            ("내부결재: 각종 계획 수립", "내부결재: 예산 집행(품의)", "결과 보고서", "대외발송: 자료 제출")
        )

        # 기안문 유형별 동적 플레이스홀더
        placeholders = {
            "내부결재: 각종 계획 수립": {
                "title": "예: 2025학년도 현장체험학습 계획",
                "details": "핵심 내용만 간단히 입력해주세요!\n예시:\n- 10월 15일 민속촌 견학\n- 5학년 대상\n- 예산: 120만원"
            },
            "내부결재: 예산 집행(품의)": {
                "title": "예: 교실용 전자칠판 구입 품의",
                "details": "품의할 내용을 간단히 입력해주세요.\n예시:\n- 품명 및 수량: 85인치 전자칠판 2대\n- 소요 예산: 금2,500,000원\n- 예산 과목: 교수-학습활동 지원"
            },
            "결과 보고서": {
                "title": "예: 2025학년도 1학기 독서토론 프로그램 운영 결과 보고",
                "details": "보고할 활동의 결과를 요약하여 입력해주세요.\n예시:\n- 활동 개요: 3~6학년 대상, 매주 수요일 진행\n- 주요 성과: 참여율 95%, 결과물 120건\n- 평가: 만족도 매우 높음"
            },
            "대외발송: 자료 제출": {
                "title": "예: 2025학년도 학교폭력 실태조사 결과 제출",
                "details": "제출할 자료의 핵심 내용을 입력해주세요.\n예시:\n- 관련: 교육지원청 OOO과-1234호\n- 제출 내용: 2025학년도 1차 실태조사 결과\n- 첨부: 결과 보고서 1부"
            }
        }

        current_placeholders = placeholders.get(giamun_type, placeholders["내부결재: 각종 계획 수립"])

        title = st.text_input(
            "제목 (간단히 입력하세요)",
            placeholder=current_placeholders["title"]
        )

        details = st.text_area(
            "주요 내용 (핵심만 간단히)",
            height=120,
            placeholder=current_placeholders["details"]
        )

        # [핵심] st.expander를 사용하여 선택사항들을 접어둠
        with st.expander("⚙️ 세부 설정 (선택사항)", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                related_basis = st.text_input(
                    "관련 근거",
                    placeholder="예: 2025학년도 학교교육계획"
                )
            with col2:
                attachments = st.text_input(
                    "첨부 파일",
                    placeholder="예: 세부계획서 1부"
                )

        if st.button("✨ 기안문 생성하기", use_container_width=True):
            if not api_key:
                st.error("❌ .env 파일에 OPENAI_API_KEY를 설정해주세요.")
            elif not title or not details:
                st.error("❌ 제목과 주요 내용을 입력해주세요.")
            else:
                with st.spinner("🤖 AI가 기안문을 작성하고 있습니다..."):
                    try:
                        # [가장 단순화된 2단계 로직]
                        # 1. 사용자 입력을 딕셔너리로 정리
                        user_input = {
                            'giamun_type': giamun_type,
                            'title': title,
                            'details': details,
                            'related_basis': related_basis if related_basis else "해당 없음",
                            'attachments': attachments if attachments else "해당 없음"
                        }

                        # 2. 프롬프트 생성
                        prompt = create_giamun_prompt_for_gpt(user_input)
                        
                        # 3. API 호출로 최종 텍스트 바로 받기
                        final_giamun_text = call_openai_api_for_text(prompt, api_key)
                        
                        if final_giamun_text:
                            st.session_state.giamun_result = final_giamun_text
                            st.success("✅ 기안문이 성공적으로 생성되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 기안문 생성에 실패했습니다. OpenAI API 응답을 확인해주세요.")
                            
                    except Exception as e:
                        st.error(f"❌ 기안문 생성 중 오류가 발생했습니다: {str(e)}")

    if 'giamun_result' in st.session_state and st.session_state.giamun_result:
        st.divider()
        st.subheader("📄 생성된 기안문")

        result_text = st.session_state.giamun_result
        
        # 결과를 표시할 텍스트 영역
        st.text_area(
            "생성 결과",
            value=result_text,
            height=400,
            key="giamun_final_output",
            label_visibility="collapsed"
        )

        # 글자/바이트 수 계산
        char_count = len(result_text)
        byte_count = sum(2 if ord(c) > 127 else 1 for c in result_text)
        st.caption(f"총 글자수: {char_count}자 | 나이스 바이트: {byte_count}바이트")

        # [핵심] JavaScript를 이용한 클립보드 복사
        st.components.v1.html(
            f"""
            <script>
            function copyToClipboard() {{
                const text = `{result_text.replace('`', '\\`')}`;
                navigator.clipboard.writeText(text).then(function() {{
                    alert('클립보드에 복사되었습니다!');
                }}).catch(function(err) {{
                    console.error('복사 실패: ', err);
                    alert('복사에 실패했습니다. 브라우저가 클립보드 접근을 허용하지 않을 수 있습니다.');
                }});
            }}
            </script>
            
            <button onclick="copyToClipboard()" style="
                width: 100%; 
                padding: 10px; 
                border-radius: 8px; 
                background-color: #6c5ce7; 
                color: white; 
                border: none; 
                font-weight: bold; 
                cursor: pointer;">
            📋 클립보드에 복사
            </button>
            """,
            height=50
        )