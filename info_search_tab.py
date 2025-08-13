"""
전주화정초 정보 검색 탭 - 최종 완성본 (MultiQuery RAG)
"""
import streamlit as st
from utils import init_rag_system

def draw_info_search_tab():
    """전주화정초 정보 검색 탭 UI (최종 버전)"""
    st.header("📞 전주화정초 정보 검색")
    st.markdown("**선생님 연락처 및 학교 정보를 빠르게 찾아보세요!**")
    
    # RAG 시스템 초기화
    rag_system_status, get_rag_answer, initialize_rag = init_rag_system()
    
    if rag_system_status == "failed":
        st.error("❌ RAG 시스템을 로드할 수 없습니다. API 키 또는 필요 라이브러리를 확인해주세요.")
        return

    st.markdown("**찾을 수 있는 정보:** 선생님 내선번호, 팩스번호, 와이파이 정보, 부서별 연락처 등")
    
    # 시스템 초기화 상태 관리
    if 'rag_initialized' not in st.session_state:
        st.session_state.rag_initialized = False

    if not st.session_state.rag_initialized:
        with st.spinner("정보 검색 시스템을 준비하고 있습니다..."):
            try:
                initialize_rag()
                st.session_state.rag_initialized = True
            except Exception as e:
                st.error(f"시스템 초기화 실패: {e}")
                return

    # 검색 입력 UI
    with st.container(border=True):
        user_question = st.text_input(
            "찾고 싶은 정보를 입력하세요:", 
            placeholder="예: 선생님 내선전화번호, 학년업무, 와이파이 비밀번호", 
            key="rag_question"
        )
        ask_button = st.button("🔍 검색하기", use_container_width=True)
    
    # 검색 실행
    if ask_button and user_question.strip():
        with st.spinner("전주화정초 정보를 검색하고 있습니다..."):
            try:
                result = get_rag_answer(user_question)
                st.markdown(f"**🔍 검색 질문:** {user_question}")
                
                results_list = result.get('results', [])
                
                if results_list and results_list[0]['answer'].strip():
                    # 메인 답변 표시
                    main_result = results_list[0]
                    confidence = main_result.get('confidence', 0)
                    
                    # 신뢰도에 따른 스타일링
                    if confidence >= 0.8:
                        color = "#28a745"  # 초록색
                        confidence_text = "높은 정확도"
                        icon = "✅"
                    elif confidence >= 0.5:
                        color = "#ffc107"  # 노란색
                        confidence_text = "보통 정확도"
                        icon = "⚠️"
                    else:
                        color = "#dc3545"  # 빨간색
                        confidence_text = "낮은 정확도"
                        icon = "❓"
                    
                    st.markdown(f"""
                    <div style="
                        border: 2px solid {color}; 
                        border-radius: 10px; 
                        padding: 20px; 
                        margin: 10px 0; 
                        background-color: rgba({color[1:]}10);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 style="color: {color}; margin: 0;">{icon} 검색 결과</h4>
                            <span style="color: {color}; font-size: 12px; font-weight: bold;">{confidence_text}</span>
                        </div>
                        <div style="font-size: 16px; line-height: 1.6; color: #333;">
                            {main_result['answer'].replace(chr(10), '<br>')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 추가 결과 표시
                    if len(results_list) > 1:
                        st.markdown("### 🔍 다른 관련 정보")
                        for i, additional_result in enumerate(results_list[1:], 1):
                            if additional_result['answer'].strip():
                                additional_confidence = additional_result.get('confidence', 0)
                                
                                # 추가 결과 스타일링
                                if additional_confidence >= 0.7:
                                    add_color = "#6c757d"
                                    add_icon = "📋"
                                else:
                                    add_color = "#adb5bd"
                                    add_icon = "📄"
                                
                                st.markdown(f"""
                                <div style="
                                    border: 1px solid {add_color}; 
                                    border-radius: 8px; 
                                    padding: 15px; 
                                    margin: 8px 0; 
                                    background-color: #f8f9fa;
                                ">
                                    <div style="margin-bottom: 8px;">
                                        <strong style="color: {add_color};">{add_icon} 추가 정보 {i}:</strong>
                                    </div>
                                    <div style="font-size: 14px; line-height: 1.5; color: #495057;">
                                        {additional_result['answer'].replace(chr(10), '<br>')}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.warning("🔍 검색 결과가 없습니다. 다른 키워드로 다시 검색해보세요.")
                    st.info("💡 **검색 팁:** 선생님 성함, 부서명, 또는 찾고자 하는 서비스명을 입력해보세요.")

            except Exception as e:
                st.error(f"❌ 검색 중 오류가 발생했습니다: {e}")
                st.info("잠시 후 다시 시도해주세요.")

    # 사용 가이드
    with st.expander("📖 사용 가이드"):
        st.markdown("""
        **🎯 효과적인 검색 방법:**
        - **선생님 찾기**: "김철수 선생님" 또는 "김철수" 
        - **부서별 연락처**: "행정실", "교무실", "보건실"
        - **학급 정보**: "3학년 1반", "6-2"
        - **시설 정보**: "와이파이", "팩스번호", "대표번호"
        
        **💡 검색 팁:**
        - 정확한 이름이나 부서명을 입력하면 더 정확한 결과를 얻을 수 있습니다
        - 여러 키워드를 조합해서 검색해보세요 (예: "3학년 담임", "음악실 연락처")
        - 결과가 없으면 비슷한 단어나 줄임말로 다시 검색해보세요
             
        """)
        
       