import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import streamlit.components.v1 as components
import re
from utils import PRIMARY_MODEL

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
    """
    HTML과 <br> 태그가 포함된 메뉴 문자열을
    달력 표시에 적합한 여러 줄의 텍스트로 변환합니다.
    """
    if not isinstance(html_string, str) or not html_string.strip():
        return ""

    # 1. <br> 태그를 줄바꿈 문자(\n)로 먼저 변경합니다.
    # 대소문자 구분 없이 <br>, <BR>, <br /> 등을 모두 처리합니다.
    text_with_newlines = re.sub(r'<br\s*/?>', '\n', html_string, flags=re.IGNORECASE)

    # 2. 나머지 모든 HTML 태그를 제거합니다.
    text_only = re.sub(r'<[^>]+>', '', text_with_newlines)

    # 3. 불필요한 앞뒤 공백을 최종적으로 제거합니다.
    cleaned_text = text_only.strip()

    return cleaned_text

def format_menu_for_calendar(menu_data: str) -> str:
    """
    HTML 태그가 포함된 긴 메뉴 문자열을 여러 줄의 깔끔한 텍스트로 변환합니다.
    달력의 각 셀에 표시하기에 적합한 형태로 만듭니다.
    """
    # 입력값이 문자열이 아니거나 비어있으면 빈 문자열 반환
    if not isinstance(menu_data, str) or not menu_data.strip():
        return ""

    # 1. HTML 태그를 모두 제거
    # 예: "<div style='...'>메뉴1<br>메뉴2</div>" -> "메뉴1 메뉴2"
    text_only = re.sub(r'<[^>]+>', ' ', menu_data)

    # 2. 문자열 앞뒤의 불필요한 공백이나 글머리 기호 제거
    cleaned_string = text_only.lstrip('•- ').strip()

    # 3. 여러 개의 공백을 하나의 공백으로 변경
    cleaned_string = re.sub(r'\s+', ' ', cleaned_string)

    # 4. 정규 표현식을 사용해 모든 메뉴 항목 찾기
    # 괄호와 그 안의 숫자를 메뉴의 끝으로 인식
    pattern = re.compile(r'.+?\s?\([\d\.]+\)?')
    matches = pattern.findall(cleaned_string)

    # 5. 그래도 찾아낸 항목이 없다면, 괄호를 기준으로 분리 시도
    if not matches and ')' in cleaned_string:
        matches = [m.strip() for m in cleaned_string.split(')') if m]
        matches = [m + ')' for m in matches]  # 다시 괄호 붙여주기

    # 6. 찾아낸 메뉴 항목들을 줄바꿈(\n)으로 연결
    if matches:
        # 각 메뉴가 한 줄씩 차지하도록 합침
        return "\n".join(matches)
    else:
        # 어떤 방법으로도 메뉴를 분리하지 못했다면, 정리된 원본 텍스트를 반환
        return cleaned_string

def format_menu_for_display(menu_string: str) -> str:
    """
    하나의 긴 문자열로 된 급식 메뉴를 마크다운 리스트 형식으로 변환합니다.
    예: "메뉴1 (1.2) 메뉴2 (3.4)" -> "- 메뉴1 (1.2)\n- 메뉴2 (3.4)"
    """
    # 입력값이 문자열이 아니거나 비어있으면 그대로 반환
    if not isinstance(menu_string, str) or not menu_string.strip():
        return ""

    # 1. 문자열 앞뒤의 불필요한 공백이나 글머리 기호 제거
    cleaned_string = menu_string.lstrip('•- ').strip()

    # 2. 정규 표현식 패턴 정의
    # (메뉴이름) (알레르기정보) 형태를 하나의 단위로 찾습니다.
    # 예: '친환경쌀밥 (1.2.3)' 또는 '제육볶음 (5.6)'
    pattern = re.compile(r'([\w\&\·\.]+\s?\([\d\.]*\))')
    
    # 2-1. 위 패턴으로 찾아지지 않을 경우를 대비한 2차 패턴
    # 메뉴 이름에 특수문자나 공백이 더 많은 경우를 대비
    pattern2 = re.compile(r'(.+?\s?\([\d\.]*\))')

    # 3. 정규 표현식을 사용해 모든 메뉴 항목 찾기
    matches = pattern.findall(cleaned_string)
    if not matches:
        matches = pattern2.findall(cleaned_string)

    # 4. 그래도 찾아낸 항목이 없다면, 공백을 기준으로 분리 (최후의 수단)
    if not matches:
        # 괄호와 다음 단어 사이의 공백을 기준으로 분리
        parts = re.split(r'\)\s+', cleaned_string)
        # 마지막 항목에 닫는 괄호가 없을 수 있으므로 추가
        matches = [part + ')' if not part.endswith(')') else part for part in parts]
        matches = [m.strip() for m in matches if m.strip()]

    # 5. 찾아낸 메뉴 항목들을 마크다운 리스트로 조합
    if matches:
        # 각 항목 앞뒤 공백을 제거하고 글머리 기호('- ')를 붙여서 한 줄씩 합침
        formatted_menu = "\n".join([f"- {match.strip()}" for match in matches])
        return formatted_menu
    else:
        # 어떤 방법으로도 메뉴를 분리하지 못했다면, 원본을 그대로 리스트 항목으로 반환
        return f"- {cleaned_string}"

RAG_SYSTEM_STATUS = "none"

try:
    from rag_system_v2 import get_rag_answer, initialize_rag
    RAG_SYSTEM_STATUS = "v2_advanced"
except ImportError as e:
    try:
        from rag_system import get_rag_answer, initialize_rag
        RAG_SYSTEM_STATUS = "v1_standard"
    except ImportError as e:
        try:
            from rag_system_lite import get_rag_answer, initialize_rag
            RAG_SYSTEM_STATUS = "lite"
        except ImportError as e:
            RAG_SYSTEM_STATUS = "failed"

# --- 초기 설정 ---

# .env 파일에서 환경 변수 로드 (파일이 있는 경우)
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(page_title="교실의 온도", page_icon="🌡️", layout="wide")

# 세션 상태 초기화
if 'generated_texts' not in st.session_state:
    st.session_state.generated_texts = {}

# RAG 시스템 초기화 (앱 시작 시 한 번만)
if 'rag_initialized' not in st.session_state:
    st.session_state.rag_initialized = False



# --- CSS 커스텀 스타일 ---
st.markdown("""
<style>
    /* 전체 앱의 폰트 */
    html, body, [class*="st-"] {
        font-family: 'Pretendard', sans-serif;
    }
    /* 페이지 제목 */
    h1 {
        font-weight: 800;
        color: #0068c9;
    }
    /* 탭 스타일 */
    button[data-baseweb="tab"] {
        font-size: 18px;
        font-weight: 700;
        padding: 12px 20px;
        border-radius: 8px 8px 0 0;
        border-bottom: 3px solid transparent;
        transition: all 0.3s ease;
    }
    button[data-baseweb="tab"]:not([aria-selected="true"]):hover {
        background-color: #f0f2f6;
        color: #0068c9;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF;
        color: #0068c9;
        border-bottom: 3px solid #0068c9;
    }
    /* 생성 버튼 */
    .stButton>button {
        font-weight: 700;
        border-radius: 8px;
    }
    /* 컨테이너 보더 */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > [data-testid="stExpander"] [data-testid="stHeader"] {
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- 엔진 설정 (프롬프트 템플릿) ---

PROMPTS = {
    # 1-1. 계획 수립
    "plan": ChatPromptTemplate.from_template("""
        당신은 대한민국 초·중학교의 행정 업무에 능숙한 교사입니다. '각종 계획 수립'을 위한 내부결재용 기안문 초안을 작성해야 합니다.
        아래 [공문 작성 규칙], [작성 규칙]과 [예시]를 참고하여, 사용자가 입력한 [기안 내용]을 바탕으로 완벽하고 간결한 기안문을 생성해 주세요.
        
        ★★★ 절대 준수 사항 ★★★
        - 반드시 본문 끝에 "끝." 표시: 본문 내용이 완료되면 한 글자(2타) 띄우고 "끝."을 표시하세요. 절대 생략 금지!
        - 첫 번째 항목: 반드시 "1. 관련:" 형식의 근거 항목으로 시작
        - 두 번째 항목: "다음과 같이" 또는 "아래와 같이"로 시작하는 본문
        - 항목 번호: 1., 가., 1), 가), (1), (가), ①, ㉮ 순서 엄수
        - 정렬: 첫째 항목은 왼쪽 끝, 둘째 항목은 2타 들여쓰기
        ★★★ 붙임 숫자 세로 완벽 정렬 필수 ★★★  
        - 붙임의 1, 2, 3... 숫자들이 한 치의 어긋남도 없이 정확히 세로 일직선으로 정렬되어야 함
        - 공백 개수를 정확히 계산하여 완벽한 정렬 구현
        
        중요사항:
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (굵은글씨, 기울임, 제목, 목록기호, 코드블록 등 모든 마크다운 문법 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 굵은글씨나 기울임체 등 어떤 형태의 마크다운 서식도 사용하지 마세요
        - 순수한 공문서 형식으로만 작성하세요
        ★★★ 붙임 정렬 규칙 (절대 준수) ★★★
        - 첫 번째: "붙임 1. 파일명 1부."
        - 두 번째: "     2. 파일명 1부."  
        - 세 번째: "     3. 파일명 1부."
        - 마지막에만: "끝." 추가
        - 숫자들이 완벽하게 세로로 일직선 정렬되어야 함 (공백 5개로 정확히 맞춤)

        [공문 작성 규칙] - 다음 규칙을 100% 준수하세요
        ★ 필수 "끝" 표시 규칙: 본문 내용이 끝나면 반드시 한 글자(2타)를 띄우고 "끝."을 표시하세요. 이는 절대 생략할 수 없습니다.
        ★ 항목 구조: 첫 번째 항목은 반드시 "1. 관련:" 형식의 근거 항목이어야 하고, 두 번째부터 "다음과 같이" 또는 "아래와 같이"로 시작하는 본문 내용이어야 합니다.
        ★ 항목 번호 순서: 1., 가., 1), 가), (1), (가), ①, ㉮ 순서를 엄격히 준수하세요. 다른 순서는 절대 사용하지 마세요.
        ★ 정렬 규칙: 
          - 첫째 항목(1., 2., ...): 왼쪽 끝에서 시작 (띄어쓰기 없음)
          - 둘째 항목(가., 나., ...): 상위 항목에서 오른쪽으로 정확히 2타 이동
          - 두 줄 이상일 때: 첫 글자에 맞춰 정렬
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        ★★★ 붙임 완벽 정렬 규칙 ★★★  
        - 붙임 1개: "붙임 1. 파일명 1부. 끝."
        - 붙임 2개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부. 끝."
        - 붙임 3개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부." + 개행 + "     3. 파일명 1부. 끝."
        - 핵심: 모든 숫자(1, 2, 3...)가 완벽하게 세로 일직선 정렬, 공백 정확히 5개 사용

        [작성 규칙]
        1. 제목: 'OOOO 계획(안)' 형식으로 작성합니다.
        2. 관련: 제시된 관련 근거를 명시합니다.
        3. 목적: 기안의 목적을 명확하게 서술합니다.
        4. 세부 계획: '가, 나, 다' 항목을 사용하여 일시, 장소, 대상, 예산 등을 체계적으로 기술합니다.
        5. 붙임: 붙임 문서 목록을 정확히 기재하고, 목록 끝에 '1부.'와 같이 수량을 표기한 후, 전체 문서의 마지막은 '끝.'으로 마무리합니다. 
           ★ 완벽한 세로 정렬 예시:
           붙임 1. 파일명 1부.
                2. 파일명 1부. 끝.
           (숫자 1, 2, 3... 이 정확히 세로 일직선, 공백 5개 사용)

        [표준 예시] - 이 형식을 정확히 따르세요
        1. 관련: 2025학년도 학교교육계획
        2. 위 호와 관련하여 2025학년도 현장체험학습을 다음과 같이 실시하고자 합니다.
          가. 일시: 2025. 10. 15. (수) 09:00 ~ 15:00
          나. 장소: OO 민속촌
          다. 대상: 5학년 학생 전체 (120명) 및 인솔교사 6명
          라. 예산: 금1,200,000원 (금일백이십만원) - 수익자 부담 경비  끝.
        
        ※ 붙임이 있는 경우 (완벽한 세로 정렬):
        붙임 1. 현장체험학습 세부 일정 1부.
             2. 현장체험학습 안전 관리 계획 1부. 끝.
        ---
        [기안 내용]
        - 계획명: {plan_name}
        - 관련 근거: {related_basis}
        - 목적: {purpose}
        - 세부 계획: {details}
        - 붙임 문서: {attachments}
        ---"""),

    # 1-2. 예산 집행(품의)
    "budget": ChatPromptTemplate.from_template("""
        당신은 대한민국 초·중학교의 행정 업무에 능숙한 교사입니다. '예산 집행(품의)'을 위한 내부결재용 기안문 초안을 작성해야 합니다.
        아래 [공문 작성 규칙], [작성 규칙]을 반드시 준수하여, 사용자가 입력한 [품의 내용]을 바탕으로 완벽한 품의서를 생성해 주세요.
        
        ★★★ 절대 준수 사항 ★★★
        - 반드시 본문 끝에 "끝." 표시: 본문 내용이 완료되면 한 글자(2타) 띄우고 "끝."을 표시하세요. 절대 생략 금지!
        - 첫 번째 항목: 반드시 "1. 관련:" 형식의 근거 항목으로 시작
        - 두 번째 항목: "다음과 같이" 또는 "아래와 같이"로 시작하는 본문
        - 항목 번호: 1., 가., 1), 가), (1), (가), ①, ㉮ 순서 엄수
        - 정렬: 첫째 항목은 왼쪽 끝, 둘째 항목은 2타 들여쓰기
        ★★★ 붙임 숫자 세로 완벽 정렬 필수 ★★★  
        - 붙임의 1, 2, 3... 숫자들이 한 치의 어긋남도 없이 정확히 세로 일직선으로 정렬되어야 함
        - 공백 개수를 정확히 계산하여 완벽한 정렬 구현
        
        중요사항:
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (굵은글씨, 기울임, 제목, 목록기호, 코드블록 등 모든 마크다운 문법 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 굵은글씨나 기울임체 등 어떤 형태의 마크다운 서식도 사용하지 마세요
        - 순수한 공문서 형식으로만 작성하세요
        ★★★ 붙임 정렬 규칙 (절대 준수) ★★★
        - 첫 번째: "붙임 1. 파일명 1부."
        - 두 번째: "     2. 파일명 1부."  
        - 세 번째: "     3. 파일명 1부."
        - 마지막에만: "끝." 추가
        - 숫자들이 완벽하게 세로로 일직선 정렬되어야 함 (공백 5개로 정확히 맞춤)

        [공문 작성 규칙] - 다음 규칙을 100% 준수하세요
        ★ 필수 "끝" 표시 규칙: 본문 내용이 끝나면 반드시 한 글자(2타)를 띄우고 "끝."을 표시하세요. 이는 절대 생략할 수 없습니다.
        ★ 항목 구조: 첫 번째 항목은 반드시 "1. 관련:" 형식의 근거 항목이어야 하고, 두 번째부터 "다음과 같이" 또는 "아래와 같이"로 시작하는 본문 내용이어야 합니다.
        ★ 항목 번호 순서: 1., 가., 1), 가), (1), (가), ①, ㉮ 순서를 엄격히 준수하세요. 다른 순서는 절대 사용하지 마세요.
        ★ 정렬 규칙: 
          - 첫째 항목(1., 2., ...): 왼쪽 끝에서 시작 (띄어쓰기 없음)
          - 둘째 항목(가., 나., ...): 상위 항목에서 오른쪽으로 정확히 2타 이동
          - 두 줄 이상일 때: 첫 글자에 맞춰 정렬
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        ★★★ 붙임 완벽 정렬 규칙 ★★★  
        - 붙임 1개: "붙임 1. 파일명 1부. 끝."
        - 붙임 2개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부. 끝."
        - 붙임 3개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부." + 개행 + "     3. 파일명 1부. 끝."
        - 핵심: 모든 숫자(1, 2, 3...)가 완벽하게 세로 일직선 정렬, 공백 정확히 5개 사용

        [작성 규칙]
        1. 제목: 'OOOO을(를) 위한 물품 구입 품의' 또는 'OOOO 관련 경비 지출 품의' 형식으로 작성합니다.
        2. 관련: 예산 관련 근거를 명시합니다.
        3. 목적: 지출 목적을 명확히 서술합니다.
        4. 구입(지출) 내역: 항목화하여 상세히 기술합니다.
        5. 소요 예산: (가장 중요) 입력된 숫자 예산을 '금OOO원(금OOO원정)' 형식으로 변환하여 기재합니다. 예) 150000 -> 금150,000원(금일십오만원정).
        6. 예산 과목: 제시된 예산 과목을 정확히 기재합니다.
        7. 붙임: 붙임 문서 목록을 정확히 기재하고, '끝.'으로 마무리합니다.
           ★ 완벽한 세로 정렬 예시:
           붙임 1. 파일명 1부.
                2. 파일명 1부. 끝.
           (숫자 1, 2, 3... 이 정확히 세로 일직선, 공백 5개 사용)
        ---
        [품의 내용]
        - 품의 제목: {purchase_title}
        - 관련 근거: {related_basis}
        - 목적: {purpose}
        - 상세 내역: {details}
        - 소요 예산 (숫자): {budget_amount}
        - 예산 과목: {budget_subject}
        - 붙임 문서: {attachments}
        ---"""),

    # (신규) 2-1. 자료 제출
    "submission": ChatPromptTemplate.from_template("""
        당신은 대한민국 초·중학교의 행정 전문가입니다. 상급 기관(교육청 등)에 '자료를 제출'하기 위한 대외발송용 시행문 초안을 작성해야 합니다.
        [공문 작성 규칙], [작성 규칙]과 [예시]를 참고하여, 사용자가 입력한 [제출 내용]으로 완벽한 시행문을 생성해주세요.
        
        중요사항:
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (굵은글씨, 기울임, 제목, 목록기호, 코드블록 등 모든 마크다운 문법 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 굵은글씨나 기울임체 등 어떤 형태의 마크다운 서식도 사용하지 마세요
        - 반드시 '수신자:' 항목부터 시작하세요
        - 순수한 공문서 형식으로만 작성하세요
        ★★★ 붙임 정렬 규칙 (절대 준수) ★★★
        - 첫 번째: "붙임 1. 파일명 1부."
        - 두 번째: "     2. 파일명 1부."  
        - 세 번째: "     3. 파일명 1부."
        - 마지막에만: "끝." 추가
        - 숫자들이 완벽하게 세로로 일직선 정렬되어야 함 (공백 5개로 정확히 맞춤)

        [공문 작성 규칙] - 다음 규칙을 100% 준수하세요
        ★ 필수 "끝" 표시 규칙: 본문 내용이 끝나면 반드시 한 글자(2타)를 띄우고 "끝."을 표시하세요. 이는 절대 생략할 수 없습니다.
        ★ 항목 구조: 첫 번째 항목은 반드시 "1. 관련:" 형식의 근거 항목이어야 하고, 두 번째부터 "다음과 같이" 또는 "아래와 같이"로 시작하는 본문 내용이어야 합니다.
        ★ 항목 번호 순서: 1., 가., 1), 가), (1), (가), ①, ㉮ 순서를 엄격히 준수하세요. 다른 순서는 절대 사용하지 마세요.
        ★ 정렬 규칙: 
          - 첫째 항목(1., 2., ...): 왼쪽 끝에서 시작 (띄어쓰기 없음)
          - 둘째 항목(가., 나., ...): 상위 항목에서 오른쪽으로 정확히 2타 이동
          - 두 줄 이상일 때: 첫 글자에 맞춰 정렬
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        ★★★ 붙임 완벽 정렬 규칙 ★★★  
        - 붙임 1개: "붙임 1. 파일명 1부. 끝."
        - 붙임 2개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부. 끝."
        - 붙임 3개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부." + 개행 + "     3. 파일명 1부. 끝."
        - 핵심: 모든 숫자(1, 2, 3...)가 완벽하게 세로 일직선 정렬, 공백 정확히 5개 사용

        [작성 규칙]
        1. 수신자: 명확히 기재합니다. 모를 경우 '수신자 미지정'으로 둡니다.
        2. 제목: '[기관명] OOO 자료 제출' 형식으로 작성합니다.
        3. 내용: 관련 공문을 'O번 항목'에서 언급하고, '아래와 같이' 또는 '붙임과 같이' 자료를 제출함을 명시합니다.
        4. 붙임: 제출하는 자료 목록을 정확히 기재하고 '끝.'으로 마무리합니다.
           ★ 완벽한 세로 정렬 예시:
           붙임 1. 파일명 1부.
                2. 파일명 1부. 끝.
           (숫자 1, 2, 3... 이 정확히 세로 일직선, 공백 5개 사용)

        [예시]
        수신자: OO교육지원청 교육장
        1. 관련: OO교육지원청 학교생활교육과-5678 (2025. 7. 10.)
        2. 위 호에 의거, 본교의 2025년 학교폭력 실태조사 결과를 붙임과 같이 제출합니다.
        붙임 1. 학교폭력 실태조사 결과 보고서 1부.
             2. 관련 설문지 및 통계 자료 1부. 끝.
        ---
        [제출 내용]
        - 수신자: {recipient}
        - 제출할 자료명: {submission_title}
        - 관련 공문: {related_document}
        - 학교명: {school_name}
        - 붙임 문서: {attachments}
        ---"""),

    # 2-2. 보고 기안문
    "activity_report": ChatPromptTemplate.from_template("""
        당신은 대한민국 초·중학교의 행정 업무에 능숙한 교사입니다. '활동 결과 보고'를 위한 내부결재용 기안문 초안을 작성해야 합니다.
        아래 [공문 작성 규칙], [작성 규칙]과 [예시]를 참고하여, 사용자가 입력한 [보고 내용]으로 완벽한 보고 기안문을 생성해주세요.
        
        ★★★ 절대 준수 사항 ★★★
        - 반드시 본문 끝에 "끝." 표시: 본문 내용이 완료되면 한 글자(2타) 띄우고 "끝."을 표시하세요. 절대 생략 금지!
        - 첫 번째 항목: 반드시 "1. 관련:" 형식의 근거 항목으로 시작
        - 두 번째 항목: "다음과 같이" 또는 "아래와 같이"로 시작하는 본문
        - 항목 번호: 1., 가., 1), 가), (1), (가), ①, ㉮ 순서 엄수
        - 정렬: 첫째 항목은 왼쪽 끝, 둘째 항목은 2타 들여쓰기
        ★★★ 붙임 숫자 세로 완벽 정렬 필수 ★★★  
        - 붙임의 1, 2, 3... 숫자들이 한 치의 어긋남도 없이 정확히 세로 일직선으로 정렬되어야 함
        - 공백 개수를 정확히 계산하여 완벽한 정렬 구현
        
        중요사항:
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (굵은글씨, 기울임, 제목, 목록기호, 코드블록 등 모든 마크다운 문법 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 굵은글씨나 기울임체 등 어떤 형태의 마크다운 서식도 사용하지 마세요
        - 순수한 공문서 형식으로만 작성하세요
        ★★★ 붙임 정렬 규칙 (절대 준수) ★★★
        - 첫 번째: "붙임 1. 파일명 1부."
        - 두 번째: "     2. 파일명 1부."  
        - 세 번째: "     3. 파일명 1부."
        - 마지막에만: "끝." 추가
        - 숫자들이 완벽하게 세로로 일직선 정렬되어야 함 (공백 5개로 정확히 맞춤)

        [공문 작성 규칙] - 다음 규칙을 100% 준수하세요
        ★ 필수 "끝" 표시 규칙: 본문 내용이 끝나면 반드시 한 글자(2타)를 띄우고 "끝."을 표시하세요. 이는 절대 생략할 수 없습니다.
        ★ 항목 구조: 첫 번째 항목은 반드시 "1. 관련:" 형식의 근거 항목이어야 하고, 두 번째부터 "다음과 같이" 또는 "아래와 같이"로 시작하는 본문 내용이어야 합니다.
        ★ 항목 번호 순서: 1., 가., 1), 가), (1), (가), ①, ㉮ 순서를 엄격히 준수하세요. 다른 순서는 절대 사용하지 마세요.
        ★ 정렬 규칙: 
          - 첫째 항목(1., 2., ...): 왼쪽 끝에서 시작 (띄어쓰기 없음)
          - 둘째 항목(가., 나., ...): 상위 항목에서 오른쪽으로 정확히 2타 이동
          - 두 줄 이상일 때: 첫 글자에 맞춰 정렬
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        ★★★ 붙임 완벽 정렬 규칙 ★★★  
        - 붙임 1개: "붙임 1. 파일명 1부. 끝."
        - 붙임 2개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부. 끝."
        - 붙임 3개: "붙임 1. 파일명 1부." + 개행 + "     2. 파일명 1부." + 개행 + "     3. 파일명 1부. 끝."
        - 핵심: 모든 숫자(1, 2, 3...)가 완벽하게 세로 일직선 정렬, 공백 정확히 5개 사용

        [작성 규칙]
        1. 제목: '{activity_title} 결과 보고' 형식으로 작성합니다.
        2. 관련: 관련 계획 또는 승인 문서를 명시합니다.
        3. 보고 내용: '가, 나, 다, 라' 항목을 사용하여 다음을 체계적으로 기술합니다:
           - 가. 개요 (목적, 일시, 장소, 참가 인원)
           - 나. 세부 활동 내용 
           - 다. 예산 사용 결과 (표 형식 포함)
           - 라. 평가 및 제언
        4. 붙임: 관련 자료 목록을 기재하고 '끝.'으로 마무리합니다.
           ★ 완벽한 세로 정렬 예시:
           붙임 1. 파일명 1부.
                2. 파일명 1부. 끝.
           (숫자 1, 2, 3... 이 정확히 세로 일직선, 공백 5개 사용)

        [예시]
        1. 관련: OO초등학교-1234 (2025. 4. 10.) "2025학년도 현장체험학습 계획(안)"
        2. 위 호와 관련하여 현장체험학습을 실시한 결과를 다음과 같이 보고합니다.
          가. 개요
              1) 목적: 역사 문화 체험을 통한 학습 효과 제고
              2) 일시: 2025. 5. 15. (수) 09:00~15:00
              3) 장소: 경주 불국사 및 석굴암
              4) 참가 인원: 학생 120명, 교사 8명
          나. 세부 활동 내용
              1) 불국사 탐방 및 문화재 해설 (10:00~12:00)
              2) 석굴암 견학 및 체험 활동 (13:00~15:00)
          다. 예산 사용 결과
              총 예산: 금3,600,000원
              지출 내역: 교통비 2,400,000원, 체험비 1,200,000원
              잔액: 금0원
          라. 평가 및 제언
              학생 만족도 95%, 교육적 효과 우수. 향후 사전 교육 강화 필요.
        붙임 1. 현장체험학습 사진자료 1부.
             2. 학생 소감문 모음 1부. 끝.
        ---
        [보고 내용]
        - 활동명: {activity_title}
        - 관련 근거: {related_basis}
        - 활동 개요: {activity_overview}
        - 세부 내용: {activity_details}
        - 예산 정보: {budget_info}
        - 평가 및 제언: {evaluation}
        - 붙임 문서: {attachments}
        ---"""),
    
    # 3-1. 교과평어 (교과세특)
    "student_record": ChatPromptTemplate.from_template("""
        당신은 학생의 성장과 잠재력을 꿰뚫어 보는 대한민국 초·중학교의 베테랑 교사입니다. 주어진 정보를 바탕으로 학생의 역량이 입체적으로 드러나는 교과세특(교과별 세부능력 및 특기사항)을 작성해야 합니다.

        중요사항:
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (굵은글씨, 기울임, 제목, 목록기호, 코드블록 등 모든 마크다운 문법 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 굵은글씨나 기울임체 등 어떤 형태의 마크다운 서식도 사용하지 마세요
        - 하나의 완성된 교과세특문으로만 작성하세요 (여러 버전이나 예시 번호 금지)
        - "또한", "그리고", "뿐만 아니라" 등의 연결어 사용을 금지합니다
        - 자연스럽고 매끄러운 하나의 완성문으로 작성하세요

        [작성 규칙]
        1. 관찰 기반의 구체성: 학생의 실제 활동, 발언, 결과물을 근거로 구체적으로 서술합니다.
        2. 역량 중심의 의미 부여: 학생의 행동을 '학업 역량', '진로 역량', '공동체 역량'과 연결하여 깊이 있는 의미를 부여합니다.
        3. 성장 과정 서술: 학생이 어떤 노력을 통해 어떻게 성장했는지 과정을 보여줍니다.
        4. 문체: 간결하고 사실적인 평어체(~함, ~음, ~보여줌, ~역량이 돋보임)를 사용합니다. 부정적인 표현이나 미사여구는 지양합니다.
        5. 연결어 제한: "또한", "그리고", "뿐만 아니라" 등의 연결어 대신 자연스러운 문장 연결을 사용합니다.
        6. 시작 방식 (중요): "학생은", "학생이름은" 등 학생 개인을 지칭하는 주어로 시작하지 않습니다. 활동이나 학습 내용, 과목의 특정 영역이나 단원, 수업 상황으로 시작합니다.
           예시) "함수의 개념을 학습하며...", "기하학적 도형을 탐구하는 과정에서...", "수학적 사고력 향상을 위한 활동에서..."
        ---
        [학생 정보]
        - 과목: {subject}
        - 핵심 역량 키워드: {competency}
        - 학생 관찰 내용 (활동, 질문, 결과물, 태도 등): {observation}
        - 성취기준: {achievement}
        ---
        위 정보를 바탕으로, 학생의 역량과 성장이 생생하게 드러나는 완성된 교과세특을 하나의 매끄러운 문단으로 작성해 주세요. 성취기준이 제공된 경우 이를 적절히 반영하여 작성해 주세요."""),

    # 3-2. 행발 (행동발달상황)
    "behavior_record": ChatPromptTemplate.from_template("""
        당신은 학생의 인성과 성장을 면밀히 관찰하는 대한민국 초·중학교의 베테랑 담임교사입니다. 주어진 정보를 바탕으로 학생의 행동발달상황이 구체적이고 긍정적으로 드러나는 행발을 작성해야 합니다.

        중요사항:
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (굵은글씨, 기울임, 제목, 목록기호, 코드블록 등 모든 마크다운 문법 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 굵은글씨나 기울임체 등 어떤 형태의 마크다운 서식도 사용하지 마세요
        - 하나의 완성된 행발문으로만 작성하세요 (여러 버전이나 예시 번호 금지)
        - "또한", "그리고", "뿐만 아니라" 등의 연결어 사용을 금지합니다
        - 자연스럽고 매끄러운 하나의 완성문으로 작성하세요

        [작성 규칙]
        1. 구체적 행동 관찰: 학생의 실제 행동, 말, 태도를 구체적으로 서술합니다.
        2. 성장과 변화 강조: 학기 초와 비교하여 학생이 어떻게 성장하고 변화했는지를 보여줍니다.
        3. 긍정적 표현: 부족한 부분도 성장 가능성과 노력하는 모습으로 긍정적으로 표현합니다.
        4. 인성 역량 연결: 관찰된 행동을 '소통역량', '공동체역량', '자기관리역량' 등과 연결하여 의미를 부여합니다.
        5. 문체: 따뜻하고 격려하는 평어체(~함, ~보여줌, ~노력함, ~성장함)를 사용합니다.
        6. 연결어 제한: "또한", "그리고", "뿐만 아니라" 등의 연결어 대신 자연스러운 문장 연결을 사용합니다.
        7. 시작 방식 (중요): "학생은", "학생이름은" 등 학생 개인을 지칭하는 주어로 시작하지 않습니다. 활동이나 상황, 학급 생활의 특정 장면으로 시작합니다.
           예시) "모둠 활동에서...", "학급 회의 시간에...", "친구들과의 협력 과정에서...", "어려운 상황이 발생했을 때..."
        ---
        [학생 관찰 정보]
        - 핵심 행동 특성: {behavior_trait}
        - 구체적 관찰 내용 (행동, 태도, 변화 과정 등): {observation}
        - 특별히 강조하고 싶은 성장 포인트: {growth_point}
        ---
        위 정보를 바탕으로, 학생의 인성과 행동발달이 생생하게 드러나는 완성된 행발을 하나의 매끄러운 문단으로 작성해 주세요."""),

    # 4. 학부모 답장
    "parent_reply": ChatPromptTemplate.from_template("""
        당신은 학생을 깊이 아끼고 학부모와 원활하게 소통하는 대한민국 초·중학교의 현명하고 따뜻한 담임 교사입니다. 학부모님이 보내신 메시지에 대해, 공감과 전문성을 바탕으로 정중하고 신뢰를 주는 답장 초안을 작성해야 합니다.

        [작성 규칙]
        1. 공감으로 시작: 학부모님의 걱정이나 마음에 먼저 공감하는 표현으로 문을 엽니다. ('어머님의 염려하시는 마음, 충분히 이해됩니다.')
        2. 긍정적 관찰 사실 전달: 자녀에 대한 긍정적인 관찰 내용이나 칭찬할 점을 함께 전달하여 안심시킵니다.
        3. 구체적인 해결 방안 제시: 문제 상황에 대해 교사로서 할 수 있는 구체적인 노력과 해결 방안을 제시합니다.
        4. 함께 노력하는 자세: 가정과의 연계와 협력을 강조하며 함께 노력하겠다는 의지를 보여줍니다.
        5. 정중한 마무리: 감사 인사와 함께 다음 소통을 기약하며 마무리합니다.
        ---
        [학부모님 메시지]
        {parent_message}

        [답장 어조 및 핵심 방향]
        {tone}
        ---
        위 내용을 바탕으로 학부모님께 보낼 답장 초안을 작성해 주십시오."""),

    # (신규) 5. 가정통신문
    "newsletter": ChatPromptTemplate.from_template("""
        당신은 교육 경험이 풍부하고 문장력이 뛰어난 대한민국 초·중학교 교사입니다. 학부모님들이 내용을 쉽게 이해하고 협조할 수 있도록, 핵심 내용을 바탕으로 가정통신문 초안을 작성해야 합니다.

        [작성 규칙]
        1. 제목: 내용을 한눈에 알 수 있는 제목을 작성합니다. (예: OOO 안내, OOO 신청 안내 등)
        2. 인사말: 계절이나 시기에 맞는 따뜻한 인사말로 시작합니다.
        3. 본문: '언제, 어디서, 누가, 무엇을, 왜, 어떻게' 육하원칙에 따라 핵심 정보를 명확하고 간결하게 전달합니다. 필요한 경우 '아래' 또는 '다음'을 사용하여 항목을 구분합니다.
        4. 강조: 중요한 날짜나 시간, 준비물 등은 일반 텍스트로 명확하게 표현합니다. (마크다운 문법 사용 금지)
        5. 맺음말: 학교 교육에 대한 관심과 협조에 감사하는 말로 마무리합니다.
        6. 날짜 및 발신 명의: 문서 하단에 발송 날짜와 학교장 직인을 포함한 발신 명의를 기재합니다.
        ---
        [가정통신문 핵심 내용]
        - 제목: {title}
        - 대상 학년: {grade}
        - 전달할 핵심 내용 (날짜, 장소, 준비물, 신청 방법 등): {main_points}
        - 학교명: {school_name}
        ---
        위 내용을 바탕으로, 학부모님들이 이해하기 쉬운 친절하고 격식 있는 가정통신문 초안을 작성해 주십시오.""")
}

# --- 메인 앱 구성 ---

st.title("🌡️ 교실의 온도")
st.markdown("""
<div style="
    background: linear-gradient(135deg, #e3f2fd 0%, #f8f9fa 100%);
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    border-left: 4px solid #2196F3;
">
    <p style="margin: 0; color: #424242; font-size: 16px; line-height: 1.6;">
        <strong>차가운 행정 업무를 덜어내고, 교실에 따뜻한 온기를 더한다는 뜻을 담았습니다.</strong><br>
        선생님의 하루를 가볍게 만들어 줄 스마트 동료입니다. 아래 탭에서 원하시는 작업을 선택해주세요.
    </p>
</div>
""", unsafe_allow_html=True)

# 기능 탭 생성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🗂️ 기안문 작성", "🏗️ 생기부 기록", "💝 학부모 답장", "🎯 가정통신문 작성", "📞 전주화정초 정보 검색", "🍽️ 급식 식단표"])

# 공통 함수: 체인 실행 및 결과 표시
def run_chain_and_display(session_key, prompt_key, inputs, container):
    # .env 파일에서 키를 자동으로 로드하므로, 키 확인 로직이 필요 없습니다.
    try:
        # 이미 생성된 결과가 있는지 확인
        if session_key not in st.session_state.generated_texts:
            # api_key 인자가 없어도 자동으로 환경변수에서 찾습니다.
            llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
            prompt = PROMPTS[prompt_key]
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
                const text = `{text_to_copy}`;
                
                if (navigator.clipboard && window.isSecureContext) {{
                    // 최신 브라우저 - Clipboard API 사용
                    navigator.clipboard.writeText(text).then(function() {{
                        showCopyMessage();
                    }}).catch(function(err) {{
                        fallbackCopy(text);
                    }});
                }} else {{
                    // 구형 브라우저 - Fallback 방법
                    fallbackCopy(text);
                }}
            }}
            
            function fallbackCopy(text) {{
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                try {{
                    document.execCommand('copy');
                    showCopyMessage();
                }} catch (err) {{
                    console.error('복사 실패:', err);
                    alert('복사에 실패했습니다. 텍스트를 수동으로 선택하여 복사해주세요.');
                }}
                
                document.body.removeChild(textArea);
            }}
            
            function showCopyMessage() {{
                const message = document.getElementById('copy-message');
                message.style.display = 'block';
                setTimeout(function() {{
                    message.style.display = 'none';
                }}, 2000);
            }}
        </script>
        """
        
        components.html(copy_button_html, height=100)
    except Exception as e:
        # OPENAI_API_KEY가 .env에 없거나 잘못된 경우 에러 메시지를 표시합니다.
        st.error(f"오류가 발생했습니다. .env 파일의 OPENAI_API_KEY 설정을 확인해주세요. (에러: {e})")




# --- 탭 1: 기안 작성 ---
with tab1:
    st.header("✍️ 기안문 작성 도우미")
    doc_type = st.selectbox(
        "작성할 기안문 유형을 선택하세요.",
        ("선택하세요", 
        "내부결재: 각종 계획 수립", "내부결재: 예산 집행(품의)", 
        "대외발송: 자료 제출", "보고: 활동 결과 보고")
    )

    if doc_type == "내부결재: 각종 계획 수립":
        with st.expander("🗓️ **각종 계획 수립** 정보 입력", expanded=True):
            st.markdown("💡 **간단 입력 모드**: 핵심 정보만 입력하면 자동으로 완성합니다!")
            plan_name = st.text_input("1. 계획명", placeholder="예: 현장체험학습")
            simple_content = st.text_area("2. 간단한 계획 내용", height=120, placeholder="간단히 입력해주세요! 예:\n• 10월 15일 민속촌 견학\n• 5학년 대상\n• 체험 활동과 역사 학습")
            
            # 고급 옵션 (선택사항)
            with st.expander("🔧 세부 설정 (선택사항)", expanded=False):
                related_basis = st.text_input("관련 근거", placeholder="자동 설정됨 (예: 학교교육계획)")
                custom_purpose = st.text_area("목적 (커스텀)", height=80, placeholder="비워두면 자동 생성")
                attachments = st.text_input("붙임 문서", placeholder="비워두면 기본 문서로 설정")
            
            if st.button("✨ 계획안 생성", use_container_width=True, key="plan"):
                if plan_name and simple_content:
                    # 기본값 설정
                    final_basis = related_basis if related_basis else "2025학년도 학교교육계획"
                    final_purpose = custom_purpose if custom_purpose else f"{plan_name}을 통해 학생들의 체험 학습 기회를 제공하고 교육과정과 연계된 다양한 경험을 통해 성장할 수 있도록 함"
                    final_attachments = attachments if attachments else f"{plan_name} 세부 일정 1부., 안전 관리 계획 1부."
                    
                    # 고유한 세션 키 생성
                    session_key = f"plan_{hash(plan_name + simple_content)}"
                    run_chain_and_display(session_key, "plan", {
                        "plan_name": plan_name, 
                        "related_basis": final_basis, 
                        "purpose": final_purpose, 
                        "details": simple_content, 
                        "attachments": final_attachments
                    }, st)
                else: st.warning("계획명과 계획 내용을 입력해주세요.")

    elif doc_type == "내부결재: 예산 집행(품의)":
        with st.expander("💰 **예산 집행(품의)** 정보 입력", expanded=True):
            st.markdown("💡 **간단 입력 모드**: 구입할 물품과 예산만 입력하세요!")
            purchase_simple = st.text_input("1. 구입할 물품/용도", placeholder="예: 교실용 프린터")
            budget_amount = st.number_input("2. 예산 (원)", min_value=0, step=10000, placeholder="예: 550000")
            simple_details = st.text_area("3. 간단한 내역", height=100, placeholder="예: HP 프린터 2대, A4용지 10박스")
            
            # 고급 옵션 (선택사항)
            with st.expander("🔧 세부 설정 (선택사항)", expanded=False):
                related_basis = st.text_input("관련 근거", placeholder="자동 설정됨 (예: 학교회계 예산서)")  
                budget_subject = st.text_input("예산 과목", placeholder="자동 설정됨 (예: 일반수용비)")
                attachments = st.text_input("붙임 문서", placeholder="자동 설정됨 (예: 견적서)")
            
            if st.button("✨ 품의서 생성", use_container_width=True, key="budget"):
                if purchase_simple and budget_amount > 0:
                    # 기본값 설정
                    final_title = f"{purchase_simple} 구입 품의" 
                    final_basis = related_basis if related_basis else "2025학년도 학교회계 예산서"
                    final_purpose = f"{purchase_simple} 구입을 통해 교육활동을 원활히 지원하고자 함"
                    final_details = simple_details if simple_details else f"{purchase_simple} - 수량 및 상세 내역은 붙임 견적서 참조"
                    final_subject = budget_subject if budget_subject else "일반수용비"
                    final_attachments = attachments if attachments else "물품 견적서 1부."
                    
                    # 고유한 세션 키 생성
                    session_key = f"budget_{hash(purchase_simple + str(budget_amount))}"
                    run_chain_and_display(session_key, "budget", {
                        "purchase_title": final_title,
                        "related_basis": final_basis, 
                        "purpose": final_purpose, 
                        "details": final_details, 
                        "budget_amount": budget_amount, 
                        "budget_subject": final_subject, 
                        "attachments": final_attachments
                    }, st)
                else: st.warning("구입할 물품과 예산을 입력해주세요.")

    elif doc_type == "대외발송: 자료 제출":
        with st.expander("📤 **자료 제출 (시행문)** 정보 입력", expanded=True):
            st.markdown("💡 **간단 입력 모드**: 제출할 자료명만 입력하세요!")
            submission_simple = st.text_input("1. 제출할 자료", placeholder="예: 학교폭력 실태조사 결과")
            
            # 고급 옵션 (선택사항)
            with st.expander("🔧 세부 설정 (선택사항)", expanded=False):
                recipient = st.text_input("수신자", placeholder="자동 설정됨 (예: 교육지원청)")
                school_name = st.text_input("학교명", placeholder="자동 설정됨 (예: OO중학교)")
                related_document = st.text_input("관련 공문", placeholder="자동 설정됨")
                attachments = st.text_input("붙임 문서", placeholder="자동 설정됨")
            
            if st.button("✨ 시행문 생성", use_container_width=True, key="submission"):
                if submission_simple:
                    # 기본값 설정
                    final_recipient = recipient if recipient else "교육지원청 교육장"
                    final_school = school_name if school_name else "OO중학교"
                    final_related = related_document if related_document else f"교육지원청 관련부서-0000 (2025년 공문)"
                    final_attachments = attachments if attachments else f"{submission_simple} 보고서 1부., 관련 자료 1부."
                    
                    # 고유한 세션 키 생성
                    session_key = f"submission_{hash(submission_simple)}"
                    run_chain_and_display(session_key, "submission", {
                        "recipient": final_recipient,
                        "school_name": final_school, 
                        "submission_title": submission_simple,
                        "related_document": final_related,
                        "attachments": final_attachments
                    }, st)
                else: st.warning("제출할 자료명을 입력해주세요.")

    elif doc_type == "보고: 활동 결과 보고":
        with st.expander("📋 **활동 결과 보고** 정보 입력", expanded=True):
            st.markdown("💡 **간단 입력 모드**: 활동명과 핵심 내용만 입력하면 완성!")
            activity_title = st.text_input("1. 활동명", placeholder="예: 현장체험학습")
            activity_simple_overview = st.text_area("2. 활동 간단 개요", height=100, placeholder="예:\n• 일시: 5월 15일(수)\n• 장소: 경주\n• 참가: 학생 120명, 교사 8명")
            
            # 고급 옵션 (선택사항)
            with st.expander("🔧 세부 설정 (선택사항)", expanded=False):
                related_basis = st.text_input("관련 근거", placeholder="자동 설정됨")
                detailed_activities = st.text_area("세부 활동 내용", height=80, placeholder="비워두면 자동 생성")
                budget_info = st.text_area("예산 정보", height=80, placeholder="비워두면 기본 형식으로 생성")
                evaluation = st.text_area("평가 및 제언", height=80, placeholder="비워두면 자동 생성")
                attachments = st.text_input("붙임 문서", placeholder="자동 설정됨")
            
            if st.button("✨ 결과 보고서 생성", use_container_width=True, key="activity_report"):
                if activity_title and activity_simple_overview:
                    # 기본값 설정
                    final_related = related_basis if related_basis else f"OO학교-0000 (2025년 계획서)"
                    final_details = detailed_activities if detailed_activities else "활동 일정에 따라 계획된 프로그램을 순차적으로 진행함"
                    final_budget = budget_info if budget_info else "총 예산 범위 내에서 적절히 집행됨"
                    final_evaluation = evaluation if evaluation else "학생 참여도 및 만족도 높음. 교육적 효과 우수함"
                    final_attachments = attachments if attachments else f"{activity_title} 사진자료 1부., 참가자 소감문 1부."
                    
                    # 고유한 세션 키 생성
                    session_key = f"activity_report_{hash(activity_title + activity_simple_overview)}"
                    run_chain_and_display(session_key, "activity_report", {
                        "activity_title": activity_title,
                        "related_basis": final_related,
                        "activity_overview": activity_simple_overview,
                        "activity_details": final_details,
                        "budget_info": final_budget,
                        "evaluation": final_evaluation,
                        "attachments": final_attachments
                    }, st)
                else: st.warning("활동명과 활동 개요를 입력해주세요.")

# --- 탭 2: 생기부 기록 ---
with tab2:
    st.header("📖 생기부 기록 도우미")
    st.markdown("학생의 활동을 구체적으로 입력할수록, 학생의 역량과 성장이 돋보이는 좋은 결과물이 나옵니다.")
    
    # 교과평어와 행발 서브탭 생성
    record_tab1, record_tab2 = st.tabs(["📚 교과평어 (교과세특)", "🌱 행발 (행동발달상황)"])
    
    # 교과평어 서브탭
    with record_tab1:
        st.markdown("여러 학생의 교과세특을 표 형태로 한 번에 생성할 수 있습니다.")
        
        # 과목 및 역량 설정
        with st.container(border=True):
            st.subheader("📚 과목 설정")
            col1, col2 = st.columns(2)
            with col1:
                subject = st.text_input("과목", placeholder="예: 수학", key="subject_table")
            with col2:
                competency_options = [
                    "창의적 사고역량",
                    "비판적 사고역량", 
                    "문제해결역량",
                    "의사소통역량",
                    "협업역량",
                    "정보활용역량",
                    "자기관리역량",
                    "시민의식",
                    "국제사회문화이해",
                    "융합적 사고력",
                    "탐구역량",
                    "추론역량",
                    "정보처리역량",
                    "의사결정역량"
                ]
                competency_selected = st.multiselect("핵심 역량 키워드 (선택사항)", competency_options, key="competency_multiselect")
                
                # 선택된 키워드들을 결합
                competency = ", ".join(competency_selected) if competency_selected else ""
        
        # 학생 수 설정
        with st.container(border=True):
            st.subheader("👥 학생 수 설정")
            num_students = st.number_input("학생 수", min_value=1, max_value=10, value=3, step=1)
        
        # 학생 정보 입력 표
        if subject:
            with st.container(border=True):
                st.subheader(f"📄 {subject} 교과세특 생성")
                
                # 세션 상태에 학생 데이터 초기화
                if 'student_data' not in st.session_state or len(st.session_state.student_data) != num_students:
                    st.session_state.student_data = [{"name": f"학생{i+1}", "observation": "", "achievement": ""} for i in range(num_students)]
                
                # 표 헤더
                header_cols = st.columns([1, 2, 4, 3])
                with header_cols[0]:
                    st.markdown("**번호**")
                with header_cols[1]:
                    st.markdown("**이름**")
                with header_cols[2]:
                    st.markdown("**학습 내용 (관찰 내용)**")
                with header_cols[3]:
                    st.markdown("**성취기준(선택)**")
                
                st.divider()
                
                # 학생 데이터 입력 행
                for i in range(num_students):
                    cols = st.columns([1, 2, 4, 3])
                    
                    with cols[0]:
                        st.markdown(f"**{i+1:02d}**")
                    
                    with cols[1]:
                        st.session_state.student_data[i]["name"] = st.text_input(
                            "이름", 
                            value=st.session_state.student_data[i]["name"],
                            placeholder=f"학생{i+1}",
                            key=f"name_{i}"
                        )
                    
                    with cols[2]:
                        st.session_state.student_data[i]["observation"] = st.text_area(
                            "관찰 내용",
                            value=st.session_state.student_data[i]["observation"],
                            placeholder=f"{st.session_state.student_data[i]['name']}의 학습 활동, 발표, 성장 모습 등을 구체적으로 기록해주세요.",
                            height=100,
                            key=f"obs_{i}"
                        )
                    
                    with cols[3]:
                        st.session_state.student_data[i]["achievement"] = st.text_area(
                            "성취기준",
                            value=st.session_state.student_data[i]["achievement"],
                            placeholder=f"성취기준을 입력해주세요. (선택사항)",
                            height=100,
                            key=f"ach_{i}"
                        )
                    
                    if i < num_students - 1:
                        st.markdown("---")
                
                st.divider()
                
                # 전체 생성 버튼
                col_generate = st.columns([3, 1])
                with col_generate[1]:
                    if st.button("✨ 전체 생성", use_container_width=True, key="generate_all"):
                        # 비어있는 관찰 내용 확인
                        empty_observations = [i+1 for i, data in enumerate(st.session_state.student_data) if not data["observation"].strip()]
                        
                        if empty_observations:
                            st.warning(f"{', '.join(map(str, empty_observations))}번 학생의 관찰 내용을 입력해주세요.")
                        else:
                            # 전체 학생 교과세특 생성
                            st.session_state.generated_table_results = []
                            
                            for i, data in enumerate(st.session_state.student_data):
                                with st.spinner(f"{data['name']} 교과세특 생성 중..."):
                                    try:
                                        llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
                                        prompt = PROMPTS["student_record"]
                                        chain = prompt | llm | StrOutputParser()
                                        
                                        result = chain.invoke({
                                            "subject": subject,
                                            "competency": competency,
                                            "observation": data["observation"],
                                            "achievement": data["achievement"]
                                        })
                                        
                                        st.session_state.generated_table_results.append({
                                            "name": data["name"],
                                            "result": result
                                        })
                                    except Exception as e:
                                        st.error(f"{data['name']} 교과세특 생성 실패: {e}")
                                        st.session_state.generated_table_results.append({
                                            "name": data["name"],
                                            "result": f"생성 실패: {e}"
                                        })
                            
                            st.success("전체 학생 교과세특 생성 완료!")
        
        # 결과 표시
        if 'generated_table_results' in st.session_state and st.session_state.generated_table_results:
            with st.container(border=True):
                st.subheader("📄 생성 결과")
                
                # NEIS 스타일 CSS
                st.markdown("""
                <style>
                .neis-container {
                    position: relative;
                    margin: 20px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                }
                .neis-header {
                    background-color: #e8f4f8;
                    padding: 8px 12px;
                    border-bottom: 1px solid #ddd;
                    font-weight: bold;
                    color: #333;
                    position: relative;
                }
                .subject-title {
                    color: #0066cc;
                    font-size: 14px;
                }
                .byte-info {
                    position: absolute;
                    right: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    font-size: 12px;
                    color: #666;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .neis-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: 'Pretendard', sans-serif;
                }
                .neis-table th {
                    background-color: #f5f5f5;
                    color: #333;
                    font-weight: bold;
                    padding: 10px;
                    text-align: center;
                    border: 1px solid #ddd;
                    font-size: 13px;
                }
                .neis-table td {
                    padding: 10px;
                    border: 1px solid #ddd;
                    vertical-align: top;
                    position: relative;
                }
                .student-number {
                    text-align: center;
                    font-weight: normal;
                    width: 50px;
                    background-color: #fafafa;
                }
                .student-name {
                    text-align: center;
                    font-weight: normal;
                    width: 80px;
                    background-color: #fafafa;
                }
                .student-record {
                    line-height: 1.5;
                    text-align: left;
                    font-size: 13px;
                    color: #333;
                    position: relative;
                    padding-right: 40px;
                }
                .copy-icon {
                    position: absolute;
                    bottom: 8px;
                    right: 8px;
                    width: 16px;
                    height: 16px;
                    cursor: pointer;
                    opacity: 0.6;
                    transition: opacity 0.2s;
                }
                .copy-icon:hover {
                    opacity: 1;
                }
                .char-count-small {
                    font-size: 11px;
                    color: #999;
                    position: absolute;
                    bottom: 25px;
                    right: 8px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # NEIS 스타일 헤더 표시
                st.markdown(f"""
                <div style="
                    background-color: #e8f4f8;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-bottom: none;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 14px;
                ">
                    <span style="color: #0066cc; font-weight: bold;">{subject}</span>
                    <span style="color: #666; font-size: 12px;">NEIS로 입력 적용 {len(st.session_state.generated_table_results)} ▲</span>
                </div>
                """, unsafe_allow_html=True)
                
                
                # 완전히 새로운 모던 커스텀 테이블 HTML 생성
                custom_table_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        * {{
                            margin: 0;
                            padding: 0;
                            box-sizing: border-box;
                        }}
                        
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            background: #f8fafc;
                            padding: 20px;
                        }}
                        
                        .custom-table-container {{
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                            overflow: hidden;
                            border: 1px solid #e2e8f0;
                        }}
                        
                        .custom-table {{
                            width: 100%;
                            border-collapse: collapse;
                        }}
                        
                        .custom-table th {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 16px;
                            text-align: center;
                            font-weight: 600;
                            font-size: 14px;
                            letter-spacing: 0.5px;
                            border: none;
                        }}
                        
                        .custom-table th:first-child {{
                            width: 80px;
                        }}
                        
                        .custom-table th:nth-child(2) {{
                            width: 120px;
                        }}
                        
                        .custom-table td {{
                            padding: 0;
                            border-bottom: 1px solid #e2e8f0;
                            vertical-align: top;
                        }}
                        
                        .number-cell {{
                            text-align: center;
                            padding: 20px 16px;
                            background: #f8fafc;
                            font-weight: 700;
                            font-size: 16px;
                            color: #4a5568;
                        }}
                        
                        .name-cell {{
                            text-align: center;
                            padding: 20px 16px;
                            background: #f8fafc;
                            font-weight: 600;
                            font-size: 14px;
                            color: #2d3748;
                            border-right: 1px solid #e2e8f0;
                        }}
                        
                        .record-cell {{
                            padding: 20px;
                            position: relative;
                            background: white;
                        }}
                        
                        .record-content {{
                            position: relative;
                        }}
                        
                        .record-text {{
                            line-height: 1.6;
                            font-size: 13px;
                            color: #2d3748;
                            min-height: 60px;
                            margin-bottom: 10px;
                            padding-right: 100px;
                            position: relative;
                        }}
                        
                        .record-footer {{
                            display: flex;
                            justify-content: flex-end;
                            align-items: center;
                            margin-top: 12px;
                        }}
                        
                        .char-info {{
                            position: absolute;
                            top: 5px;
                            right: 20px;
                            font-size: 10px;
                            color: #ff6b35;
                            font-weight: 500;
                            background: #fff5f0;
                            border: 1px solid #ff6b35;
                            padding: 2px 6px;
                            border-radius: 3px;
                            white-space: nowrap;
                            box-shadow: 0 1px 3px rgba(255, 107, 53, 0.1);
                        }}
                        
                        .action-buttons {{
                            display: flex;
                            gap: 8px;
                            align-items: center;
                        }}
                        
                        .char-count {{
                            font-size: 10px;
                            color: #999;
                            margin-right: 12px;
                        }}
                        
                        .action-btn {{
                            background: none;
                            border: none;
                            padding: 6px 8px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                            transition: all 0.2s ease;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }}
                        
                        .copy-btn {{
                            color: #4299e1;
                            background: rgba(66, 153, 225, 0.1);
                        }}
                        
                        .copy-btn:hover {{
                            background: rgba(66, 153, 225, 0.2);
                            transform: translateY(-1px);
                        }}
                        
                        .edit-btn {{
                            color: #48bb78;
                            background: rgba(72, 187, 120, 0.1);
                        }}
                        
                        .edit-btn:hover {{
                            background: rgba(72, 187, 120, 0.2);
                            transform: translateY(-1px);
                        }}
                        
                        .edit-textarea {{
                            width: 100%;
                            min-height: 100px;
                            padding: 12px;
                            border: 2px solid #e2e8f0;
                            border-radius: 8px;
                            font-size: 13px;
                            font-family: inherit;
                            line-height: 1.6;
                            resize: vertical;
                            transition: border-color 0.2s ease;
                        }}
                        
                        .edit-textarea:focus {{
                            outline: none;
                            border-color: #667eea;
                            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                        }}
                        
                        .save-btn, .cancel-btn {{
                            padding: 6px 12px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 12px;
                            transition: background-color 0.2s ease;
                        }}
                        
                        .save-btn {{
                            background: #48bb78;
                            color: white;
                        }}
                        
                        .save-btn:hover {{
                            background: #38a169;
                        }}
                        
                        .cancel-btn {{
                            background: #e2e8f0;
                            color: #4a5568;
                        }}
                        
                        .cancel-btn:hover {{
                            background: #cbd5e0;
                        }}
                        
                        .message {
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
                        }
                        
                        .message.success {
                            background: #48bb78;
                            color: white;
                        }
                        
                        .message.error {
                            background: #f56565;
                            color: white;
                        }
                        
                        .message.show {
                            transform: translateX(0);
                        }
                    </style>
                </head>
                <body>
                    <div class="custom-table-container">
                        <table class="custom-table">
                            <thead>
                                <tr>
                                    <th>번호</th>
                                    <th>이름</th>
                                    <th>평어</th>
                                </tr>
                            </thead>
                            <tbody>
                """
                
                # 테이블 행 데이터 생성
                for i, result_data in enumerate(st.session_state.generated_table_results):
                    custom_table_html += f"""
                                <tr>
                                    <td>{i + 1}</td>
                                    <td>{result_data['name']}</td>
                                    <td class="text-cell" id="text_{i}">
                                        <div class="text-content">
                                            {result_data['result'].replace(chr(10), '<br>')}
                                        </div>
                                        <div class="button-group">
                                            <button class="copy-btn" onclick="copyText({i})">복사</button>
                                            <button class="edit-btn" onclick="editText({i})">수정</button>
                                        </div>
                                    </td>
                                </tr>
                    """
                
                custom_table_html += """
                            </tbody>
                        </table>
                    </div>
                    <script>
                        const originalTexts = [
                """
                
                # JavaScript 배열에 원본 텍스트 추가
                for i, result_data in enumerate(st.session_state.generated_table_results):
                    escaped_for_js = result_data['result'].replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
                    custom_table_html += f"            '{escaped_for_js}'"
                    if i < len(st.session_state.generated_table_results) - 1:
                        custom_table_html += ","
                    custom_table_html += "\n"
                
                custom_table_html += f"""
                        ];
                        
                        function copyText(index) {{
                            const text = originalTexts[index];
                            if (navigator.clipboard && window.isSecureContext) {{
                                navigator.clipboard.writeText(text).then(function() {{
                                    showMessage('복사되었습니다!', 'success');
                                }}).catch(function(err) {{
                                    fallbackCopy(text);
                                }});
                            }} else {{
                                fallbackCopy(text);
                            }}
                        }}
                        
                        function fallbackCopy(text) {{
                            const textArea = document.createElement('textarea');
                            textArea.value = text;
                            textArea.style.position = 'fixed';
                            textArea.style.left = '-999999px';
                            document.body.appendChild(textArea);
                            textArea.focus();
                            textArea.select();
                            
                            try {{
                                document.execCommand('copy');
                                showMessage('복사되었습니다!', 'success');
                            }} catch (err) {{
                                showMessage('복사에 실패했습니다.', 'error');
                            }}
                            
                            document.body.removeChild(textArea);
                        }}
                        
                        function editText(index) {{
                            const textDiv = document.getElementById('text_' + index);
                            const originalText = originalTexts[index];
                            
                            const textarea = document.createElement('textarea');
                            textarea.className = 'edit-textarea';
                            textarea.value = originalText;
                            
                            const controls = document.createElement('div');
                            controls.className = 'edit-controls';
                            
                            const saveBtn = document.createElement('button');
                            saveBtn.className = 'save-btn';
                            saveBtn.textContent = '저장';
                            saveBtn.onclick = function() {{
                                const newText = textarea.value;
                                const newHtml = newText.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\n/g, '<br>');
                                
                                // 글자수와 바이트수 계산
                                const totalChars = newText.length;
                                let niceBytes = 0;
                                for (let char of newText) {{
                                    if (char.charCodeAt(0) > 127) {{
                                        niceBytes += 3;
                                    }} else {{
                                        niceBytes += 1;
                                    }}
                                }}
                                
                                // HTML에 글자수 박스 포함하여 업데이트
                                const charInfoHtml = '<span class="char-info">' + totalChars + '자 / ' + niceBytes + 'bytes</span>';
                                textDiv.innerHTML = newHtml + charInfoHtml;
                                
                                originalTexts[index] = newText;
                                showMessage('수정되었습니다!', 'success');
                            }};
                            
                            const cancelBtn = document.createElement('button');
                            cancelBtn.className = 'cancel-btn';
                            cancelBtn.textContent = '취소';
                            cancelBtn.onclick = function() {{
                                const originalHtml = originalText.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\n/g, '<br>');
                                
                                // 원래 글자수 계산
                                const totalChars = originalText.length;
                                let niceBytes = 0;
                                for (let char of originalText) {{
                                    if (char.charCodeAt(0) > 127) {{
                                        niceBytes += 3;
                                    }} else {{
                                        niceBytes += 1;
                                    }}
                                }}
                                
                                // 글자수 박스 포함하여 원래 상태로 복원
                                const charInfoHtml = '<span class="char-info">' + totalChars + '자 / ' + niceBytes + 'bytes</span>';
                                textDiv.innerHTML = originalHtml + charInfoHtml;
                            }};
                            
                            controls.appendChild(saveBtn);
                            controls.appendChild(cancelBtn);
                            
                            textDiv.innerHTML = '';
                            textDiv.appendChild(textarea);
                            textDiv.appendChild(controls);
                            
                            textarea.focus();
                        }}
                        
                        function showMessage(message, type) {{
                            const messageDiv = document.createElement('div');
                            messageDiv.className = 'message ' + type;
                            messageDiv.textContent = message;
                            document.body.appendChild(messageDiv);
                            
                            setTimeout(() => {{
                                messageDiv.classList.add('show');
                            }}, 100);
                            
                            setTimeout(() => {{
                                messageDiv.classList.remove('show');
                                setTimeout(() => {{
                                    if (messageDiv.parentNode) {{
                                        messageDiv.parentNode.removeChild(messageDiv);
                                    }}
                                }}, 300);
                            }}, 2500);
                        }}
                    </script>
                </body>
                </html>
                """
                
                # HTML 컴포넌트로 표시
                st.components.v1.html(custom_table_html, height=600, scrolling=True)
        
        else:
            st.info("ℹ️ 과목을 먼저 입력해주세요.")
    
    # 행발 서브탭
    with record_tab2:
        st.markdown("여러 학생의 행발을 표 형태로 한 번에 생성할 수 있습니다.")
        
        # 학생 수 설정
        with st.container(border=True):
            st.subheader("👥 학생 수 설정")
            num_behavior_students = st.number_input("학생 수", min_value=1, max_value=10, value=3, step=1, key="num_behavior_students")
        
        # 학생 정보 입력 표
        with st.container(border=True):
            st.subheader(f"📄 행발 생성")
            
            # 세션 상태에 학생 데이터 초기화
            if 'behavior_student_data' not in st.session_state or len(st.session_state.behavior_student_data) != num_behavior_students:
                st.session_state.behavior_student_data = [{"name": f"학생{i+1}", "behavior_content": ""} for i in range(num_behavior_students)]
            
            # 표 헤더
            header_cols = st.columns([1, 2, 6])
            with header_cols[0]:
                st.markdown("**번호**")
            with header_cols[1]:
                st.markdown("**이름**")
            with header_cols[2]:
                st.markdown("**행동 내용 (관찰된 행동 특성)**")
            
            st.divider()
            
            # 학생 데이터 입력 행
            for i in range(num_behavior_students):
                cols = st.columns([1, 2, 6])
                
                with cols[0]:
                    st.markdown(f"**{i+1:02d}**")
                
                with cols[1]:
                    st.session_state.behavior_student_data[i]["name"] = st.text_input(
                        "이름", 
                        value=st.session_state.behavior_student_data[i]["name"],
                        placeholder=f"학생{i+1}",
                        key=f"behavior_name_{i}"
                    )
                
                with cols[2]:
                    st.session_state.behavior_student_data[i]["behavior_content"] = st.text_area(
                        "행동 내용",
                        value=st.session_state.behavior_student_data[i]["behavior_content"],
                        placeholder=f"{st.session_state.behavior_student_data[i]['name']}의 행동 특성, 성장 모습, 인성 발달 등을 구체적으로 기록해주세요.",
                        height=100,
                        key=f"behavior_content_{i}"
                    )
                
                if i < num_behavior_students - 1:
                    st.markdown("---")
            
            st.divider()
            
            # 전체 생성 버튼
            col_generate = st.columns([3, 1])
            with col_generate[1]:
                if st.button("✨ 전체 생성", use_container_width=True, key="generate_all_behavior"):
                    # 비어있는 행동 내용 확인
                    empty_behavior_contents = [i+1 for i, data in enumerate(st.session_state.behavior_student_data) if not data["behavior_content"].strip()]
                    
                    if empty_behavior_contents:
                        st.warning(f"{', '.join(map(str, empty_behavior_contents))}번 학생의 행동 내용을 입력해주세요.")
                    else:
                        # 전체 학생 행발 생성
                        st.session_state.generated_behavior_table_results = []
                        
                        for i, data in enumerate(st.session_state.behavior_student_data):
                            with st.spinner(f"{data['name']} 행발 생성 중..."):
                                try:
                                    llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
                                    prompt = PROMPTS["behavior_record"]
                                    chain = prompt | llm | StrOutputParser()
                                    
                                    result = chain.invoke({
                                        "behavior_trait": "학생의 행동 특성 및 성장 모습",
                                        "observation": data["behavior_content"],
                                        "growth_point": "학생의 개인적 성장과 발달 과정"
                                    })
                                    
                                    st.session_state.generated_behavior_table_results.append({
                                        "name": data["name"],
                                        "result": result
                                    })
                                except Exception as e:
                                    st.error(f"{data['name']} 행발 생성 실패: {e}")
                                    st.session_state.generated_behavior_table_results.append({
                                        "name": data["name"],
                                        "result": f"생성 실패: {e}"
                                    })
                        
                        st.success("전체 학생 행발 생성 완료!")
        
        
        # 결과 표시 - 교과세특과 동일한 스타일
        if 'generated_behavior_table_results' in st.session_state and st.session_state.generated_behavior_table_results:
            with st.container(border=True):
                st.subheader("📄 생성 결과")
                
                # NEIS 스타일 헤더 표시
                st.markdown(f"""
                <div style="
                    background-color: #e8f4f8;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-bottom: none;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 14px;
                ">
                    <span style="color: #0066cc; font-weight: bold;">행동발달상황</span>
                    <span style="color: #666; font-size: 12px;">NEIS로 입력 적용 {len(st.session_state.generated_behavior_table_results)} ▲</span>
                </div>
                """, unsafe_allow_html=True)
                
                
                # 완전히 새로운 모던 커스텀 테이블 HTML 생성
                custom_table_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        * {{
                            margin: 0;
                            padding: 0;
                            box-sizing: border-box;
                        }}
                        
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            background: #f8fafc;
                            padding: 20px;
                        }}
                        
                        .custom-table-container {{
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                            overflow: hidden;
                            border: 1px solid #e2e8f0;
                        }}
                        
                        .custom-table {{
                            width: 100%;
                            border-collapse: collapse;
                        }}
                        
                        .custom-table th {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 16px;
                            text-align: center;
                            font-weight: 600;
                            font-size: 14px;
                            letter-spacing: 0.5px;
                            border: none;
                        }}
                        
                        .custom-table th:first-child {{
                            width: 80px;
                        }}
                        
                        .custom-table th:nth-child(2) {{
                            width: 120px;
                        }}
                        
                        .custom-table td {{
                            padding: 0;
                            border-bottom: 1px solid #e2e8f0;
                            vertical-align: top;
                        }}
                        
                        .number-cell {{
                            text-align: center;
                            padding: 20px 16px;
                            background: #f8fafc;
                            font-weight: 700;
                            font-size: 16px;
                            color: #4a5568;
                        }}
                        
                        .name-cell {{
                            text-align: center;
                            padding: 20px 16px;
                            background: #f8fafc;
                            font-weight: 600;
                            font-size: 14px;
                            color: #2d3748;
                            border-right: 1px solid #e2e8f0;
                        }}
                        
                        .record-cell {{
                            padding: 20px;
                            position: relative;
                            background: white;
                        }}
                        
                        .record-content {{
                            position: relative;
                        }}
                        
                        .record-text {{
                            line-height: 1.6;
                            font-size: 13px;
                            color: #2d3748;
                            min-height: 60px;
                            margin-bottom: 10px;
                            padding-right: 100px;
                            position: relative;
                        }}
                        
                        .record-footer {{
                            display: flex;
                            justify-content: flex-end;
                            align-items: center;
                            margin-top: 12px;
                        }}
                        
                        .char-info {{
                            position: absolute;
                            top: 5px;
                            right: 20px;
                            font-size: 10px;
                            color: #ff6b35;
                            font-weight: 500;
                            background: #fff5f0;
                            border: 1px solid #ff6b35;
                            padding: 2px 6px;
                            border-radius: 3px;
                            white-space: nowrap;
                            box-shadow: 0 1px 3px rgba(255, 107, 53, 0.1);
                        }}
                        
                        .action-buttons {{
                            display: flex;
                            gap: 8px;
                            align-items: center;
                        }}
                        
                        .char-count {{
                            font-size: 10px;
                            color: #999;
                            margin-right: 12px;
                        }}
                        
                        .action-btn {{
                            background: none;
                            border: none;
                            padding: 6px 8px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 14px;
                            transition: all 0.2s ease;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }}
                        
                        .copy-btn {{
                            color: #4299e1;
                            background: rgba(66, 153, 225, 0.1);
                        }}
                        
                        .copy-btn:hover {{
                            background: rgba(66, 153, 225, 0.2);
                            transform: translateY(-1px);
                        }}
                        
                        .edit-btn {{
                            color: #48bb78;
                            background: rgba(72, 187, 120, 0.1);
                        }}
                        
                        .edit-btn:hover {{
                            background: rgba(72, 187, 120, 0.2);
                            transform: translateY(-1px);
                        }}
                        
                        .edit-textarea {{
                            width: 100%;
                            min-height: 100px;
                            padding: 12px;
                            border: 2px solid #e2e8f0;
                            border-radius: 8px;
                            font-size: 13px;
                            font-family: inherit;
                            line-height: 1.6;
                            resize: vertical;
                            transition: border-color 0.2s ease;
                        }}
                        
                        .edit-textarea:focus {{
                            outline: none;
                            border-color: #667eea;
                            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                        }}
                        
                        .save-btn, .cancel-btn {{
                            padding: 6px 12px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 12px;
                            transition: background-color 0.2s ease;
                        }}
                        
                        .save-btn {{
                            background: #48bb78;
                            color: white;
                        }}
                        
                        .save-btn:hover {{
                            background: #38a169;
                        }}
                        
                        .cancel-btn {{
                            background: #e2e8f0;
                            color: #4a5568;
                        }}
                        
                        .cancel-btn:hover {{
                            background: #cbd5e0;
                        }}
                        
                        .message {
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
                        }
                        
                        .message.success {
                            background: #48bb78;
                            color: white;
                        }
                        
                        .message.error {
                            background: #f56565;
                            color: white;
                        }
                        
                        .message.show {
                            transform: translateX(0);
                        }
                    </style>
                </head>
                <body>
                    <div class="custom-table-container">
                        <table class="custom-table">
                            <thead>
                                <tr>
                                    <th>번호</th>
                                    <th>이름</th>
                                    <th>행발 내용</th>
                                </tr>
                            </thead>
                            <tbody>
                """
                
                # 행발 전용 원본 텍스트 배열 생성
                behavior_texts = []
                for result in st.session_state.generated_behavior_table_results:
                    escaped_for_js = result["result"].replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
                    behavior_texts.append(escaped_for_js)
                
                # 이 for 루프 전체가 올바른 들여쓰기로 수정되었습니다.
                for i, result in enumerate(st.session_state.generated_behavior_table_results):
                    char_count = len(result["result"])
                    byte_count = sum(2 if ord(char) > 127 else 1 for char in result["result"])
                    
                    # custom_table_html에 더하는 f-string의 시작 부분을 for 루프와 같은 레벨로 맞춥니다.
                    custom_table_html += f"""
                        <tr>
                            <td class="number-cell">{i+1:02d}</td>
                            <td class="name-cell">{result["name"]}</td>
                            <td class="record-cell">
                                <div class="record-content">
                                    <div class="record-text" id="behavior_text_{i}">{result["result"]}</div>
                                    <div class="record-footer">
                                        <span class="char-count" id="behavior_count_{i}">{char_count}자/{byte_count}byte</span>
                                        <div class="action-buttons">
                                            <button class="action-btn copy-btn" onclick="copyBehaviorText({i})" title="복사">📋</button>
                                            <button class="action-btn edit-btn" onclick="editBehaviorText({i})" title="수정">✏️</button>
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>
            """
                
                custom_table_html += """
                            </tbody>
                        </table>
                    </div>
                    
                    <script>
                        // 행발 전용 원본 텍스트 배열
                        const behaviorOriginalTexts = ["""
                
                # 행발 전용 텍스트 배열을 JavaScript에 추가
                for i, text in enumerate(behavior_texts):
                    custom_table_html += f"            '{text}'"
                    if i < len(behavior_texts) - 1:
                        custom_table_html += ","
                    custom_table_html += "\n"
                
                custom_table_html += """
                        ];
                        
                        // 행발 전용 복사 함수
                        function copyBehaviorText(index) {
                            const text = behaviorOriginalTexts[index];
                            if (navigator.clipboard && window.isSecureContext) {
                                navigator.clipboard.writeText(text).then(function() {
                                    showBehaviorMessage('복사되었습니다!', 'success');
                                }).catch(function(err) {
                                    fallbackBehaviorCopy(text);
                                });
                            } else {
                                fallbackBehaviorCopy(text);
                            }
                        }
                        
                        // 행발 전용 fallback 복사 함수
                        function fallbackBehaviorCopy(text) {
                            const textArea = document.createElement('textarea');
                            textArea.value = text;
                            textArea.style.position = 'fixed';
                            textArea.style.left = '-999999px';
                            document.body.appendChild(textArea);
                            textArea.focus();
                            textArea.select();
                            try {
                                document.execCommand('copy');
                                showBehaviorMessage('복사되었습니다!', 'success');
                            } catch (err) {
                                showBehaviorMessage('복사에 실패했습니다.', 'error');
                            }
                            document.body.removeChild(textArea);
                        }
                        
                        // 행발 전용 편집 함수
                        function editBehaviorText(index) {
                            const textDiv = document.getElementById('behavior_text_' + index);
                            const originalText = behaviorOriginalTexts[index];
                            
                            const textarea = document.createElement('textarea');
                            textarea.className = 'behavior-edit-textarea';
                            textarea.value = originalText;
                            
                            const controls = document.createElement('div');
                            controls.className = 'behavior-edit-controls';
                            
                            const saveBtn = document.createElement('button');
                            saveBtn.textContent = '저장';
                            saveBtn.className = 'behavior-save-btn';
                            saveBtn.onclick = function() { saveBehaviorEdit(index, textarea.value); };
                            
                            const cancelBtn = document.createElement('button');
                            cancelBtn.textContent = '취소';
                            cancelBtn.className = 'behavior-cancel-btn';
                            cancelBtn.onclick = function() { cancelBehaviorEdit(index); };
                            
                            controls.appendChild(saveBtn);
                            controls.appendChild(cancelBtn);
                            
                            textDiv.innerHTML = '';
                            textDiv.appendChild(textarea);
                            textDiv.appendChild(controls);
                            
                            textarea.focus();
                            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
                        }
                        
                        // 행발 전용 저장 함수
                        function saveBehaviorEdit(index, newText) {
                            const textDiv = document.getElementById('behavior_text_' + index);
                            textDiv.textContent = newText;
                            
                            // 글자수/바이트수 업데이트
                            const charCount = newText.length;
                            const byteCount = new Blob([newText]).size;
                            const charCountSpan = document.getElementById('behavior_count_' + index);
                            charCountSpan.textContent = `${charCount}자/${byteCount}byte`;
                            
                            // 원본 텍스트 배열도 업데이트
                            behaviorOriginalTexts[index] = newText;
                            
                            showBehaviorMessage('수정되었습니다!', 'success');
                        }
                        
                        // 행발 전용 취소 함수
                        function cancelBehaviorEdit(index) {
                            const textDiv = document.getElementById('behavior_text_' + index);
                            textDiv.textContent = behaviorOriginalTexts[index];
                        }
                        
                        // 행발 전용 메시지 표시 함수
                        function showBehaviorMessage(message, type) {
                            // 기존 메시지가 있으면 제거
                            const existingMsg = document.querySelector('.behavior-copy-message');
                            if (existingMsg) {
                                existingMsg.remove();
                            }
                            
                            // 새 메시지 생성
                            const msgDiv = document.createElement('div');
                            msgDiv.className = 'behavior-copy-message';
                            msgDiv.textContent = message;
                            document.body.appendChild(msgDiv);
                            
                            setTimeout(() => {
                                msgDiv.classList.add('show');
                            }, 100);
                            
                            setTimeout(() => {
                                msgDiv.classList.remove('show');
                                setTimeout(() => {
                                    if (msgDiv.parentNode) {
                                        msgDiv.parentNode.removeChild(msgDiv);
                                    }
                                }, 300);
                            }, 2500);
                        }
                        
                        // 행발 전용 CSS 스타일 추가
                        const behaviorStyle = document.createElement('style');
                        behaviorStyle.textContent = `
                            @keyframes behaviorSlideIn {
                                from { transform: translateX(100%); opacity: 0; }
                                to { transform: translateX(0); opacity: 1; }
                            }
                            @keyframes behaviorSlideOut {
                                from { transform: translateX(0); opacity: 1; }
                                to { transform: translateX(100%); opacity: 0; }
                            }
                            
                            .behavior-edit-textarea {
                                width: 100%;
                                min-height: 100px;
                                padding: 12px;
                                border: 2px solid #e2e8f0;
                                border-radius: 8px;
                                font-size: 13px;
                                font-family: inherit;
                                line-height: 1.6;
                                resize: vertical;
                                transition: border-color 0.2s ease;
                            }
                            
                            .behavior-edit-textarea:focus {
                                outline: none;
                                border-color: #667eea;
                                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                            }
                            
                            .behavior-edit-controls {
                                margin-top: 8px;
                                display: flex;
                                gap: 8px;
                            }
                            
                            .behavior-save-btn, .behavior-cancel-btn {
                                padding: 6px 12px;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                font-size: 12px;
                                transition: background-color 0.2s ease;
                            }
                            
                            .behavior-save-btn {
                                background: #48bb78;
                                color: white;
                            }
                            
                            .behavior-save-btn:hover {
                                background: #38a169;
                            }
                            
                            .behavior-cancel-btn {
                                background: #e2e8f0;
                                color: #4a5568;
                            }
                            
                            .behavior-cancel-btn:hover {
                                background: #cbd5e0;
                            }
                        `;
                        document.head.appendChild(behaviorStyle);
                    </script>
                </body>
                </html>
                """
                
                # Streamlit에서 HTML 렌더링
                st.components.v1.html(custom_table_html, height=600, scrolling=True)
        

# --- 탭 3: 학부모 답장 ---
with tab3:
    st.header("✉️ 학부모 답장 도우미")
    st.markdown("학부모님의 메시지와 답장의 핵심 방향을 입력하면, 따뜻하고 전문적인 답장 초안을 만들어 드립니다.")
    with st.container(border=True):
        parent_message = st.text_area("학부모님 메시지 원문", placeholder="이곳에 학부모님께 받은 메시지를 그대로 붙여넣어 주세요.", height=150)
        tone = st.text_input("답장 어조 및 핵심 방향", placeholder="예: 따뜻하고 공감적으로, 해결 방안 중심으로, 긍정적인 면을 부각하여")

        if st.button("✨ 답장 초안 생성", use_container_width=True, key="parent_reply"):
            if all([parent_message, tone]):
                # 고유한 세션 키 생성
                session_key = f"parent_reply_{hash(parent_message + tone)}"
                run_chain_and_display(session_key, "parent_reply", {"parent_message": parent_message, "tone": tone}, st)
            else: st.warning("모든 항목을 입력해주세요.")

# --- 탭 4: 가정통신문 작성 ---
with tab4:
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
                }, st)
            else: 
                st.warning("핵심 내용을 입력해주세요.")

# --- 탭 5: 전주화정초 정보 검색 ---
with tab5:
    st.header("📞 전주화정초 정보 검색")
    st.markdown("**선생님 연락처 및 학교 정보를 빠르게 찾아보세요!**")
    
    # RAG 시스템 상태 표시
    if RAG_SYSTEM_STATUS == "failed":
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

# --- 탭 6: 급식 식단표 ---
with tab6:
    st.header("🍽️ 급식 식단표")
    st.markdown("전주화정초등학교의 급식 식단표를 월별 또는 주별로 확인하세요.")
    
    # 필요한 라이브러리 import (상단에 이미 있으면 중복이지만 안전을 위해)
    import requests
    from datetime import datetime, timedelta
    
    # API 설정
    API_KEY = "2d74e530f4334ab9906e6171f031560a"
    OFFICE_CODE = "P10"  # 전북
    SCHOOL_CODE = "8332156"  # 전주화정초
    BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    
    # 조회 방식 선택
    view_mode = st.radio("조회 방식 선택", ["주별 조회", "월별 조회"], horizontal=True)
    
    def get_meal_data_for_month(year_month: str):
        """특정 월의 급식 데이터를 API를 통해 가져옵니다."""
        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'pIndex': 1,
            'pSize': 100,
            'ATPT_OFCDC_SC_CODE': OFFICE_CODE,
            'SD_SCHUL_CODE': SCHOOL_CODE,
            'MLSV_YMD': year_month
        }
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'mealServiceDietInfo' in data:
                return data['mealServiceDietInfo'][1]['row']
            elif 'RESULT' in data and data['RESULT']['CODE'] == 'INFO-200':
                return []
            else:
                error_message = data.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류가 발생했습니다.')
                st.error(f"API 오류: {error_message}")
                return None

        except requests.exceptions.RequestException as e:
            st.error(f"네트워크 오류가 발생했습니다: {e}")
            return None

    def format_menu(menu_text: str):
        """메뉴 문자열의 <br/>을 줄바꿈으로 바꾸고, 알레르기 정보를 정리합니다."""
        menu_items = menu_text.replace('<br/>', '\n- ')
        return '- ' + menu_items
    
    if view_mode == "월별 조회":
        st.subheader("📅 월별 급식 조회")
        
        # 연도, 월 선택
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            current_year = datetime.now().year
            selected_year = st.selectbox("연도 선택", range(current_year-1, current_year+2), index=1)
        
        with col2:
            current_month = datetime.now().month
            selected_month = st.selectbox("월 선택", range(1, 13), index=current_month-1)
        
        with col3:
            st.info(f"📅 {selected_year}년 {selected_month}월 급식 달력")
        
        # 월간 급식 데이터 가져오기
        year_month = f"{selected_year}{selected_month:02d}"
        
        with st.spinner("급식 데이터를 가져오는 중..."):
            meal_data = get_meal_data_for_month(year_month)
        
        if meal_data:
            # 급식 데이터를 날짜별 딕셔너리로 정리
            # .get()을 사용해 키가 없어도 오류가 발생하지 않도록 수정
            # 'MLSV_YMD' 키가 있는 항목만 처리하도록 if 조건 추가
            meal_dict = {item.get('MLSV_YMD'): item.get('DDISH_NM', '') for item in meal_data if item.get('MLSV_YMD')}

            # 달력 헤더 (월~금)
            days_of_week = ["월", "화", "수", "목", "금"]
            cols = st.columns(5)
            for col, day in zip(cols, days_of_week):
                with col:
                    st.markdown(f"<p style='text-align: center;'><b>{day}</b></p>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)

            # 달력 내용 생성
            import calendar
            cal = calendar.Calendar()
            month_days = cal.monthdatescalendar(selected_year, selected_month)

            for week in month_days:
                # 5열 (평일) 생성
                cols = st.columns(5)
                # 평일(월요일=0, ..., 금요일=4)만 처리
                for i in range(5):
                    day = week[i]
                    with cols[i]:
                        if day.month == selected_month:
                            date_str = day.strftime("%Y%m%d")
                            menu = meal_dict.get(date_str, "")
                            
                            # 새로 추가한 함수로 메뉴 텍스트 완벽하게 정리
                            final_menu_text = format_final_menu(menu)
                            
                            # CSS로 최소 높이만 지정하고, 내용은 HTML <br>로 줄바꿈
                            st.markdown(f"""
                            <div style='border: 1px solid #eee; border-radius: 5px; padding: 8px; min-height: 140px;'>
                                <b style='color: #333;'>{day.day}</b>
                                <div style='font-size: 0.85em; margin-top: 5px; line-height: 1.5;'>
                                    {final_menu_text.replace('\n', '<br>')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # 다른 달의 날짜는 회색으로 표시하고 칸만 유지
                            st.markdown(f"""
                            <div style='border: 1px solid #f8f9fa; border-radius: 5px; padding: 8px; min-height: 140px; color: #ccc;'>
                                {day.day}
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.warning("해당 월의 급식 정보를 가져올 수 없습니다.")
    
    else:  # 주별 조회
        st.subheader("📅 주별 급식 조회")
        
        # 날짜 선택
        selected_date = st.date_input("조회할 주를 선택하세요 (해당 주의 아무 날짜나 선택)", datetime.now())
    
        # 선택된 날짜를 기준으로 해당 주의 시작(월요일)과 끝(일요일) 날짜 계산
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        st.info(f"**조회 기간:** {start_of_week.strftime('%Y년 %m월 %d일')} ~ {end_of_week.strftime('%Y년 %m월 %d일')}")
        
        # 자동으로 해당 주 데이터 조회
        with st.spinner("주간 급식 데이터를 가져오는 중..."):
            # 필요한 월(들)의 데이터를 가져오기
            months_to_fetch = set()
            months_to_fetch.add(start_of_week.strftime('%Y%m'))
            months_to_fetch.add(end_of_week.strftime('%Y%m'))

            all_meals_data = []
            for month in months_to_fetch:
                monthly_data = get_meal_data_for_month(month)
                if monthly_data:
                    all_meals_data.extend(monthly_data)

        # 가져온 전체 데이터에서 해당 주에 해당하는 데이터만 필터링
        if all_meals_data:
            # 날짜 범위를 YYYYMMDD 형식의 문자열 리스트로 생성 (평일만)
            date_range_str = [(start_of_week + timedelta(days=i)).strftime('%Y%m%d') for i in range(5)]
            
            # 해당 주에 속하는 식단만 필터링
            weekly_meals = [meal for meal in all_meals_data if meal['MLSV_YMD'] in date_range_str]

            if not weekly_meals:
                st.warning("해당 주에는 등록된 급식 정보가 없습니다.")
            else:
                # 날짜별로 데이터 그룹화
                meals_by_date = {}
                for meal in weekly_meals:
                    date_key = meal['MLSV_YMD']
                    if date_key not in meals_by_date:
                        meals_by_date[date_key] = []
                    meals_by_date[date_key].append(meal)
                    
                # 주간 급식표 - 순수 Streamlit 방식
                st.markdown("### 📅 주간 급식표")
                st.write("")  # 간격 추가
                
                # 5개 컬럼 생성 (월~금)
                col1, col2, col3, col4, col5 = st.columns(5)
                cols = [col1, col2, col3, col4, col5]
                weekdays_short = ['월', '화', '수', '목', '금']
                
                for i in range(5):
                    current_day = start_of_week + timedelta(days=i)
                    day_str = current_day.strftime('%Y%m%d')
                    
                    with cols[i]:
                        # 요일 헤더
                        st.subheader(f"{weekdays_short[i]} {current_day.strftime('%m/%d')}")
                        
                        # 메뉴 표시
                        if day_str in meals_by_date:
                            day_meals = sorted(meals_by_date[day_str], key=lambda x: x['MMEAL_SC_NM'])
                            
                            for meal in day_meals:
                                # HTML 코드가 포함된 '더러운' 데이터를 가져옴
                                dirty_menu_data = meal['DDISH_NM']
                                
                                # --- 여기에 함수 호출을 반드시 추가! ---
                                cleaned_menu_for_display = format_calendar_entry(dirty_menu_data)
                                
                                # 메뉴 항목들을 분리하여 표시
                                formatted_menu = format_menu_for_display(cleaned_menu_for_display)
                                
                                if formatted_menu:
                                    st.markdown(formatted_menu)
                                
                                # 칼로리 정보
                                if meal['CAL_INFO']:
                                    st.caption(meal['CAL_INFO'])
                        else:
                            st.write("급식 없음")
                            st.write("")  # 빈 공간 추가
        else:
            st.warning("해당 주에는 등록된 급식 정보가 없습니다.")

# --- 하단 제작자 정보 ---
st.markdown("---")
st.markdown("""
<div style="
    text-align: center; 
    padding: 15px; 
    margin-top: 30px;
    color: #888888;
    font-size: 14px;
">
    Made by <strong>전주화정초 박성광</strong>
</div>
""", unsafe_allow_html=True)