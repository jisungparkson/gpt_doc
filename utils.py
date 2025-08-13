"""
공통 유틸리티 함수들
"""
import streamlit as st
import streamlit.components.v1 as components
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import re

# --- 프로젝트 전체에서 사용할 AI 모델 정의 ---
PRIMARY_MODEL = "gpt-4o-mini"

# --- 만능 메뉴 정리 함수 (복원) ---
def format_meal_menu(menu_string: str) -> str:
    """
    어떤 형태의 메뉴 문자열이든 (HTML 태그, <br>, 숫자, 괄호 포함)
    깔끔하게 정리하여 줄바꿈된 메뉴 목록 텍스트를 반환합니다.
    """
    if not isinstance(menu_string, str) or not menu_string.strip():
        return ""  # 메뉴가 없으면 빈 문자열 반환

    # 1. <br> 태그를 표준 줄바꿈 문자(\n)로 변경
    text = re.sub(r'<br\s*/?>', '\n', menu_string, flags=re.IGNORECASE)

    # 2. <div></div> 같은 모든 HTML 태그를 제거
    text = re.sub(r'<[^>]+>', '', text)

    # 3. 괄호와 그 안의 내용(알레르기 정보 등)을 모두 제거
    text = re.sub(r'\s*\([^)]*\)', '', text)

    # 4. 숫자와 점(.)으로 된 알레르기 정보도 제거
    text = re.sub(r'\s*[\d\.]+\s*', ' ', text).strip()

    # 5. 여러 개의 공백을 하나의 공백으로 변경
    text = re.sub(r'\s+', ' ', text)

    # 6. 공백을 기준으로 메뉴들을 분리하고, 각 메뉴를 줄바꿈으로 합침
    items = [item.strip() for item in text.split(' ') if item.strip()]

    return "\n".join(items)

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
            llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
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

# --- RAG 시스템 초기화 함수 (최종 버전) ---
@st.cache_resource
def init_rag_system():
    """RAG 시스템 초기화 - MultiQuery RAG를 직접 구현"""
    try:
        import os
        import pandas as pd
        from langchain.docstore.document import Document
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        from langchain_community.vectorstores import FAISS
        from langchain.retrievers.multi_query import MultiQueryRetriever
        from langchain.chains import RetrievalQA
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "failed", None, None

        # 1. 데이터 로드 및 전처리 (오류 처리 기능이 강화된 버전)
        # on_bad_lines='warn' : 형식이 잘못된 줄은 경고만 하고 건너뜀
        # quotechar='"' : 큰따옴표로 감싸인 필드 내부의 콤마는 구분자로 인식하지 않음
        try:
            df = pd.read_csv(
                "data/school_info.csv", 
                on_bad_lines='warn', 
                quotechar='"'
            )
        except Exception as e:
            st.error(f"CSV 파일을 읽는 중 심각한 오류 발생: {e}")
            return "failed", None, None
            
        df.dropna(subset=['question', 'answer'], inplace=True)
        documents = [Document(page_content=f"질문: {row['question']} 답변: {row['answer']}") for _, row in df.iterrows()]

        # 2. 임베딩 및 Vector Store 생성
        embeddings = OpenAIEmbeddings(api_key=api_key)
        vectorstore = FAISS.from_documents(documents, embeddings)

        # 3. MultiQueryRetriever 설정
        llm = ChatOpenAI(temperature=0, api_key=api_key)
        retriever_from_llm = MultiQueryRetriever.from_llm(
            retriever=vectorstore.as_retriever(search_kwargs={'k': 3}), llm=llm
        )
        
        # 4. QA 체인 생성 (소스 문서 반환 옵션 활성화)
        qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever_from_llm, return_source_documents=True)

        # 5. 답변 생성 함수 정의
        def get_rag_answer(question):
            response = qa_chain.invoke(question)
            results = []
            
            # 소스 문서가 있는지 확인하고 처리
            if response.get('source_documents'):
                for doc in response['source_documents']:
                    # '답변: ' 이후의 내용만 추출
                    content = doc.page_content
                    if '답변: ' in content:
                        answer_part = content.split('답변: ', 1)[1]
                    else:
                        answer_part = content
                    results.append({'answer': answer_part, 'confidence': 0.85})
            
            # 만약 소스 문서가 없다면, 최종 결과(result)라도 사용
            if not results and response.get('result'):
                 results.append({'answer': response.get('result'), 'confidence': 0.3})
            
            # 그래도 결과가 없다면 최종 실패 메시지
            if not results:
                 results.append({'answer': "죄송합니다. 관련된 정보를 찾을 수 없습니다.", 'confidence': 0.1})

            return {'results': results}

        # 6. UI에서 호출할 초기화 함수
        def initialize_rag():
            pass # @st.cache_resource 덕분에 이미 로드됨

        return "success", get_rag_answer, initialize_rag

    except Exception as e:
        st.error(f"RAG 시스템 초기화 중 오류: {e}")
        return "failed", None, None