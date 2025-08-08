"""
공통 유틸리티 함수들
"""
import streamlit as st
import streamlit.components.v1 as components
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import re

def format_final_menu(menu_string: str) -> str:
    """
    HTML, <br>, 숫자, 괄호 등 모든 불필요한 요소를 제거하고
    깔끔한 메뉴 목록 텍스트를 반환하는 최종 함수.
    """
    if not isinstance(menu_string, str) or not menu_string.strip():
        return ""

    # 1. <br> 태그를 표준 줄바꿈 문자로 변경
    text = menu_string.replace('<br>', '\n')
    
    # 2. 괄호와 그 안의 내용(알레르기 정보)을 모두 제거
    text = re.sub(r'\s*\([^)]*\)', '', text)
    
    # 3. 모든 숫자와 점(.)을 제거
    text = re.sub(r'[\d\.]', '', text)
    
    # 4. 남아있는 HTML 태그가 있다면 제거
    text = re.sub(r'<[^>]+>', '', text)

    # 5. 각 메뉴 라인의 앞뒤 공백을 제거하고 빈 줄은 삭제
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # 6. 깨끗해진 메뉴 목록을 다시 줄바꿈으로 합쳐서 반환
    return "\n".join(lines)

def format_calendar_entry(html_string: str) -> str:
    """HTML과 <br> 태그를 제거하여 깔끔한 텍스트로 변환"""
    if not isinstance(html_string, str) or not html_string.strip():
        return ""
    text_with_newlines = re.sub(r'<br\s*/?>', '\n', html_string, flags=re.IGNORECASE)
    text_only = re.sub(r'<[^>]+>', '', text_with_newlines)
    return text_only.strip()

def format_menu_for_calendar(menu_data: str) -> str:
    """HTML 태그가 포함된 메뉴 문자열을 깔끔한 텍스트로 변환"""
    if not isinstance(menu_data, str) or not menu_data.strip():
        return ""
    text_only = re.sub(r'<[^>]+>', ' ', menu_data)
    cleaned_string = re.sub(r'\s+', ' ', text_only.lstrip('•- ').strip())
    pattern = re.compile(r'.+?\s?\([\d\.]+\)?')
    matches = pattern.findall(cleaned_string)
    if not matches and ')' in cleaned_string:
        matches = [m.strip() + ')' for m in cleaned_string.split(')') if m.strip()]
    return "\n".join(matches) if matches else cleaned_string

def format_menu_for_display(menu_string: str) -> str:
    """급식 메뉴를 마크다운 리스트 형식으로 변환"""
    if not isinstance(menu_string, str) or not menu_string.strip():
        return ""
    cleaned_string = menu_string.lstrip('•- ').strip()
    pattern = re.compile(r'([\w\&\·\.]+\s?\([\d\.]*\))')
    matches = pattern.findall(cleaned_string)
    if not matches:
        matches = re.compile(r'(.+?\s?\([\d\.]*\))').findall(cleaned_string)
    if not matches:
        parts = re.split(r'\)\s+', cleaned_string)
        matches = [part + ')' if not part.endswith(')') else part for part in parts if part.strip()]
    return "\n".join([f"- {match.strip()}" for match in matches]) if matches else f"- {cleaned_string}"

def run_chain_and_display(session_key, prompt_key, inputs, container, prompts):
    """
    공통 체인 실행 및 결과 표시 함수
    """
    try:
        # 이미 생성된 결과가 있는지 확인
        if session_key not in st.session_state.generated_texts:
            # api_key 인자가 없어도 자동으로 환경변수에서 찾습니다.
            llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
            prompt = prompts[prompt_key]
            chain = prompt | llm | StrOutputParser()

            with st.spinner("초안을 작성하고 있습니다... 잠시만 기다려주세요."):
                result = chain.invoke(inputs)
                st.session_state.generated_texts[session_key] = result

        result_text = st.text_area("✍️ 생성 결과", value=st.session_state.generated_texts[session_key], height=400, key=f"result_{session_key}")
        
        # 글자수 및 바이트수 계산
        text = st.session_state.generated_texts[session_key]
        total_chars = len(text)  # 공백 포함 총 글자수
        
        # 나이스 바이트수 계산 (한글 3바이트, 영문/숫자/기호 1바이트)
        nice_bytes = 0
        for char in text:
            if ord(char) > 127:  # 한글 및 기타 유니코드 문자
                nice_bytes += 3
            else:  # 영문, 숫자, 기호
                nice_bytes += 1
        
        st.caption(f"총 글자수: {total_chars}자 | 나이스 바이트: {nice_bytes}바이트")
        
        # JavaScript를 사용한 클립보드 복사
        text_to_copy = st.session_state.generated_texts[session_key].replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
        
        copy_button_html = f"""
        <div style="margin: 10px 0;">
            <button onclick="copyToClipboard()" style="
                background-color: #ff6b6b;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
                font-weight: bold;
            ">
                📋 클립보드에 복사
            </button>
            <div id="copy-message" style="
                display: none;
                color: green;
                font-weight: bold;
                margin-top: 10px;
                text-align: center;
            ">
                ✅ 클립보드에 복사되었습니다!
            </div>
        </div>
        <script>
            function copyToClipboard() {{
                const text = '{text_to_copy}';
                
                // 임시 textarea 요소를 만들어서 텍스트를 복사
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                try {{
                    document.execCommand('copy');
                    document.getElementById('copy-message').style.display = 'block';
                    setTimeout(function() {{
                        document.getElementById('copy-message').style.display = 'none';
                    }}, 3000);
                    
                    // 버튼 색상 변경 (성공 표시)
                    const button = document.querySelector('button');
                    const originalColor = button.style.backgroundColor;
                    button.style.backgroundColor = '#28a745';
                    button.innerHTML = '✅ 복사 완료!';
                    
                    setTimeout(function() {{
                        button.style.backgroundColor = originalColor;
                        button.innerHTML = '📋 클립보드에 복사';
                    }}, 2000);
                }} catch (err) {{
                    console.error('복사 실패:', err);
                    alert('복사에 실패했습니다. 브라우저에서 수동으로 복사해주세요.');
                }}
                
                document.body.removeChild(textArea);
            }}
            
            // 메시지를 자동으로 사라지게 하는 함수
            function showMessage(text, type) {{
                const message = document.createElement('div');
                message.textContent = text;
                message.className = 'message ' + type;
                message.style.cssText = `
                    top: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 13px;
                    z-index: 1000;
                    transform: translateX(100%);
                    transition: transform 0.3s ease;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                `;
                
                if (type === 'success') {{
                    message.style.background = '#48bb78';
                    message.style.color = 'white';
                }} else if (type === 'error') {{
                    message.style.background = '#f56565';
                    message.style.color = 'white';
                }}
                
                document.body.appendChild(message);
                
                setTimeout(function() {{
                    message.style.transform = 'translateX(0)';
                }}, 100);
                
                setTimeout(function() {{
                    message.style.transform = 'translateX(100%)';
                    setTimeout(function() {{
                        if (message.parentNode) {{
                            message.parentNode.removeChild(message);
                        }}
                    }}, 300);
                }}, 2500);
            }}
        </script>
        """
        
        components.html(copy_button_html, height=100)
    except Exception as e:
        # OPENAI_API_KEY가 .env에 없거나 잘못된 경우 에러 메시지를 표시합니다.
        st.error(f"오류가 발생했습니다. .env 파일의 OPENAI_API_KEY 설정을 확인해주세요. (에러: {e})")

def init_rag_system():
    """RAG 시스템 초기화 - MultiQuery RAG 우선"""
    rag_system_status = "none"
    
    try:
        # MultiQuery RAG 시스템 (최고 성능)
        from rag_system_multiquery import get_rag_answer, initialize_rag
        rag_system_status = "multiquery_advanced"
        print("MultiQuery RAG 시스템 로드 성공")
        return rag_system_status, get_rag_answer, initialize_rag
    except Exception as e:
        print(f"MultiQuery RAG 시스템 로드 실패: {e}")
        try:
            from rag_system_v2 import get_rag_answer, initialize_rag
            rag_system_status = "v2_advanced"
            return rag_system_status, get_rag_answer, initialize_rag
        except ImportError:
            try:
                from rag_system import get_rag_answer, initialize_rag
                rag_system_status = "v1_standard"
                return rag_system_status, get_rag_answer, initialize_rag
            except ImportError:
                try:
                    from rag_system_lite import get_rag_answer, initialize_rag
                    rag_system_status = "lite"
                    return rag_system_status, get_rag_answer, initialize_rag
                except ImportError:
                    rag_system_status = "failed"
                    return rag_system_status, None, None