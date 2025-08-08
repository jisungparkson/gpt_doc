"""
전주화정초 정보 검색 탭
"""
import streamlit as st
from utils import init_rag_system

def draw_info_search_tab():
    """전주화정초 정보 검색 탭 UI"""
    st.header("📞 전주화정초 정보 검색")
    st.markdown("**선생님 연락처 및 학교 정보를 빠르게 찾아보세요!**")
    
    # RAG 시스템 초기화
    rag_system_status, get_rag_answer, initialize_rag = init_rag_system()
    
    # RAG 시스템 상태 표시
    if rag_system_status == "failed":
        st.error("❌ RAG 시스템을 로드할 수 없습니다. 필요한 라이브러리를 설치해주세요.")
        st.code("pip install scikit-learn pandas numpy", language="bash")
        st.stop()
    
    st.markdown("**찾을 수 있는 정보:** 선생님 내선번호, 팩스번호, 와이파이 정보, 부서별 연락처 등")
    
    # RAG 시스템 초기화
    if not st.session_state.rag_initialized:
        with st.spinner("시스템을 준비하고 있습니다..."):
            try:
                initialize_rag()
                st.session_state.rag_initialized = True
            except Exception as e:
                st.error(f"시스템 초기화 실패: {e}")
                st.stop()
    
    # 질문 입력
    with st.container(border=True):
        user_question = st.text_input(
            "찾고 싶은 정보를 입력하세요:",
            placeholder="학교 교무실 내선번호 알려줘",
            key="rag_question"
        )
        
        ask_button = st.button("🔍 검색하기", use_container_width=True)
    
    # 질문 처리 및 결과 표시
    if ask_button and user_question.strip():
        with st.spinner("전주화정초 정보를 검색하고 있습니다..."):
            try:
                result = get_rag_answer(user_question)
                
                # 검색 결과 바로 표시
                st.markdown(f"**🔍 검색:** {user_question}")
                
                # 결과가 새로운 형식인지 확인 (하위 호환성)
                if 'results' in result and isinstance(result['results'], list):
                    results_list = result['results']
                else:
                    # 기존 형식 지원
                    results_list = [{
                        'answer': result.get('answer', ''),
                        'confidence': result.get('confidence', 0)
                    }]
                
                # 첫 번째 결과 (메인 답변) 표시
                if results_list:
                    main_result = results_list[0]
                    confidence = main_result.get('confidence', 0)
                    
                    # 신뢰도에 따른 답변 스타일
                    if confidence > 0.7:
                        confidence_color = "#28a745"  # 녹색
                        confidence_text = "높음"
                    elif confidence > 0.3:
                        confidence_color = "#ffc107"  # 노란색
                        confidence_text = "보통"
                    else:
                        confidence_color = "#dc3545"  # 빨간색
                        confidence_text = "낮음"
                    
                    st.markdown(f"""
                    <div style="
                        background-color: #f8f9fa; 
                        padding: 15px; 
                        border-radius: 8px; 
                        border-left: 4px solid {confidence_color};
                        margin: 10px 0;
                    ">
                        <strong>📞 결과:</strong><br>
                        {main_result['answer']}
                        <br><br>
                        <small style="color: {confidence_color};">
                            <strong>신뢰도: {confidence_text}</strong>
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 추가 결과들 (2번째, 3번째) 표시
                    if len(results_list) > 1:
                        st.markdown("### 🔍 다른 관련 정보")
                        st.markdown("*혹시 이런 정보를 찾으셨나요?*")
                        
                        for i, additional_result in enumerate(results_list[1:], 2):
                            additional_confidence = additional_result.get('confidence', 0)
                            
                            # 추가 결과 신뢰도 색상 (더 연한 색상 사용)
                            if additional_confidence > 0.7:
                                additional_color = "#d4edda"  # 연한 녹색
                                border_color = "#28a745"
                            elif additional_confidence > 0.3:
                                additional_color = "#fff3cd"  # 연한 노란색
                                border_color = "#ffc107"
                            else:
                                additional_color = "#f8d7da"  # 연한 빨간색
                                border_color = "#dc3545"
                            
                            confidence_text_additional = "높음" if additional_confidence > 0.7 else "보통" if additional_confidence > 0.3 else "낮음"
                            
                            st.markdown(f"""
                            <div style="
                                background-color: {additional_color}; 
                                padding: 12px; 
                                border-radius: 6px; 
                                border-left: 3px solid {border_color};
                                margin: 8px 0;
                                font-size: 0.95em;
                            ">
                                <strong>📋 추가 정보 {i-1}:</strong><br>
                                {additional_result['answer']}
                                <br><br>
                                <small style="color: {border_color};">
                                    <strong>신뢰도: {confidence_text_additional}</strong>
                                </small>
                            </div>
                            """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {e}")
    
    # 사용 가이드
    with st.expander("💡 사용 가이드"):
        st.markdown("""
        ### 📞 전주화정초 정보 검색 사용법
        
        1. **검색 입력**: 찾고 싶은 선생님 이름이나 부서명을 입력하세요
        2. **자동 검색**: 시스템이 관련 연락처와 정보를 찾아 제공합니다
        3. **신뢰도 확인**: 검색 결과의 정확도를 색깔로 구분해서 표시합니다
        4. **상세 정보**: 더 자세한 정보는 참고 자료에서 확인할 수 있습니다
        
        ### 🔍 검색 예시
        - "교장선생님"
        - "교무실 팩스"
        - "교감선생님"
        - "와이파이"
        
        ### 💡 도움말
        - ✅ **검색 결과의 정확도**를 색깔로 표시합니다
        - ✅ **참고 자료**에서 원본 정보를 확인할 수 있습니다
        """)