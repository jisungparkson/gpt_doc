import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import streamlit.components.v1 as components

# --- 초기 설정 ---

# .env 파일에서 환경 변수 로드 (파일이 있는 경우)
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(page_title="교실의 온도", page_icon="🌡️", layout="wide")

# 세션 상태 초기화
if 'generated_texts' not in st.session_state:
    st.session_state.generated_texts = {}


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
        
        **중요사항:**
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (**, *, #, -, ``` 등 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 반드시 '1. 관련:' 항목부터 시작하세요
        - 순수한 공문서 형식으로만 작성하세요

        [공문 작성 규칙]
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 항목 구분: 1., 가., 1), 가), (1), (가), ①, ㉮ 순으로 사용합니다.
        - 정렬: 첫째 항목(1., 2., ...)은 왼쪽 처음부터 시작하고, 둘째 항목(가., 나., ...)부터는 오른쪽으로 2타씩 옮겨 시작합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        - 결문: 본문 내용이 끝나면 한 글자(2타)를 띄우고 "끝."이라고 표시합니다. 첨부물이 있을 경우, 붙임 표시문 다음에 한 글자를 띄우고 "끝."을 표시합니다.
        - 붙임: 첨부 파일이 2개 이상이면 각 파일명에 번호를 붙여 나열하고, 각 파일명 끝에 수량을 표기합니다.

        [작성 규칙]
        1. 제목: 'OOOO 계획(안)' 형식으로 작성합니다.
        2. 관련: 제시된 관련 근거를 명시합니다.
        3. 목적: 기안의 목적을 명확하게 서술합니다.
        4. 세부 계획: '가, 나, 다' 항목을 사용하여 일시, 장소, 대상, 예산 등을 체계적으로 기술합니다.
        5. 붙임: 붙임 문서 목록을 정확히 기재하고, 목록 끝에 '1부.'와 같이 수량을 표기한 후, 전체 문서의 마지막은 '끝.'으로 마무리합니다.

        [예시]
        1. 관련: 2025학년도 학교교육계획
        2. 위 호와 관련하여 2025학년도 현장체험학습을 다음과 같이 실시하고자 합니다.
          가. 일시: 2025. 10. 15. (수) 09:00 ~ 15:00
          나. 장소: OO 민속촌
          다. 대상: 5학년 학생 전체 (120명) 및 인솔교사 6명
          라. 예산: 금1,200,000원 (금일백이십만원) - 수익자 부담 경비
        붙임  1. 현장체험학습 세부 일정 1부.
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
        
        **중요사항:**
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (**, *, #, -, ``` 등 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 반드시 '1. 관련:' 항목부터 시작하세요
        - 순수한 공문서 형식으로만 작성하세요

        [공문 작성 규칙]
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 항목 구분: 1., 가., 1), 가), (1), (가), ①, ㉮ 순으로 사용합니다.
        - 정렬: 첫째 항목(1., 2., ...)은 왼쪽 처음부터 시작하고, 둘째 항목(가., 나., ...)부터는 오른쪽으로 2타씩 옮겨 시작합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        - 결문: 본문 내용이 끝나면 한 글자(2타)를 띄우고 "끝."이라고 표시합니다. 첨부물이 있을 경우, 붙임 표시문 다음에 한 글자를 띄우고 "끝."을 표시합니다.
        - 붙임: 첨부 파일이 2개 이상이면 각 파일명에 번호를 붙여 나열하고, 각 파일명 끝에 수량을 표기합니다.

        [작성 규칙]
        1. 제목: 'OOOO을(를) 위한 물품 구입 품의' 또는 'OOOO 관련 경비 지출 품의' 형식으로 작성합니다.
        2. 관련: 예산 관련 근거를 명시합니다.
        3. 목적: 지출 목적을 명확히 서술합니다.
        4. 구입(지출) 내역: 항목화하여 상세히 기술합니다.
        5. 소요 예산: **가장 중요.** 입력된 숫자 예산을 '금OOO원(금OOO원정)' 형식으로 변환하여 기재합니다. 예) 150000 -> 금150,000원(금일십오만원정).
        6. 예산 과목: 제시된 예산 과목을 정확히 기재합니다.
        7. 붙임: 붙임 문서 목록을 정확히 기재하고, '끝.'으로 마무리합니다.
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
        
        **중요사항:**
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (**, *, #, -, ``` 등 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 반드시 '수신자:' 항목부터 시작하세요
        - 순수한 공문서 형식으로만 작성하세요

        [공문 작성 규칙]
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 항목 구분: 1., 가., 1), 가), (1), (가), ①, ㉮ 순으로 사용합니다.
        - 정렬: 첫째 항목(1., 2., ...)은 왼쪽 처음부터 시작하고, 둘째 항목(가., 나., ...)부터는 오른쪽으로 2타씩 옮겨 시작합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        - 결문: 본문 내용이 끝나면 한 글자(2타)를 띄우고 "끝."이라고 표시합니다. 첨부물이 있을 경우, 붙임 표시문 다음에 한 글자를 띄우고 "끝."을 표시합니다.
        - 붙임: 첨부 파일이 2개 이상이면 각 파일명에 번호를 붙여 나열하고, 각 파일명 끝에 수량을 표기합니다.

        [작성 규칙]
        1. 수신자: 명확히 기재합니다. 모를 경우 '수신자 미지정'으로 둡니다.
        2. 제목: '[기관명] OOO 자료 제출' 형식으로 작성합니다.
        3. 내용: 관련 공문을 'O번 항목'에서 언급하고, '아래와 같이' 또는 '붙임과 같이' 자료를 제출함을 명시합니다.
        4. 붙임: 제출하는 자료 목록을 정확히 기재하고 '끝.'으로 마무리합니다.

        [예시]
        수신자: OO교육지원청 교육장
        1. 관련: OO교육지원청 학교생활교육과-5678 (2025. 7. 10.)
        2. 위 호에 의거, 본교의 2025년 학교폭력 실태조사 결과를 붙임과 같이 제출합니다.
        붙임  1. 학교폭력 실태조사 결과 보고서 1부.
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
        
        **중요사항:**
        - 출력 시 마크다운 문법을 절대 사용하지 마세요 (**, *, #, -, ``` 등 금지)
        - 모든 강조는 일반 텍스트로만 표현하세요
        - 반드시 '1. 관련:' 항목부터 시작하세요
        - 순수한 공문서 형식으로만 작성하세요

        [공문 작성 규칙]
        - 관련 근거 (첫 번째 항목): 기안의 법적, 행정적 근거가 되는 상위 공문서나 법규를 명시합니다.
        - 본문 내용: "다음과 같이", "아래와 같이" 등의 표현을 사용하여 시작하며, 육하원칙에 따라 명확하게 작성합니다.
        - 항목 구분: 1., 가., 1), 가), (1), (가), ①, ㉮ 순으로 사용합니다.
        - 정렬: 첫째 항목(1., 2., ...)은 왼쪽 처음부터 시작하고, 둘째 항목(가., 나., ...)부터는 오른쪽으로 2타씩 옮겨 시작합니다.
        - 금액 표기: 금123,450원(금일십이만삼천사백오십원)과 같이 아라비아 숫자와 한글을 병기합니다.
        - 날짜 표기: 2025. 8. 1.(금) 14:00와 같이 표기합니다.
        - 결문: 본문 내용이 끝나면 한 글자(2타)를 띄우고 "끝."이라고 표시합니다. 첨부물이 있을 경우, 붙임 표시문 다음에 한 글자를 띄우고 "끝."을 표시합니다.
        - 붙임: 첨부 파일이 2개 이상이면 각 파일명에 번호를 붙여 나열하고, 각 파일명 끝에 수량을 표기합니다.

        [작성 규칙]
        1. 제목: '{activity_title} 결과 보고' 형식으로 작성합니다.
        2. 관련: 관련 계획 또는 승인 문서를 명시합니다.
        3. 보고 내용: '가, 나, 다, 라' 항목을 사용하여 다음을 체계적으로 기술합니다:
           - 가. 개요 (목적, 일시, 장소, 참가 인원)
           - 나. 세부 활동 내용 
           - 다. 예산 사용 결과 (표 형식 포함)
           - 라. 평가 및 제언
        4. 붙임: 관련 자료 목록을 기재하고 '끝.'으로 마무리합니다.

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
        붙임  1. 현장체험학습 사진자료 1부.
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
        당신은 학생의 성장과 잠재력을 꿰뚫어 보는 대한민국 초·중학교의 베테랑 교사입니다. 주어진 정보를 바탕으로 학생의 역량이 입체적으로 드러나는 교과세특(교과별 세부능력 및 특기사항) 예시문을 작성해야 합니다.

        [작성 규칙]
        1.  **관찰 기반의 구체성**: 학생의 실제 활동, 발언, 결과물을 근거로 구체적으로 서술합니다. ('~에 대해 발표함' (X) -> '~자료를 분석하여 ~라는 새로운 관점을 제시한 발표로 뛰어난 탐구 역량을 보여줌' (O))
        2.  **역량 중심의 의미 부얬**: 학생의 행동을 '학업 역량', '진로 역량', '공동체 역량'과 연결하여 깊이 있는 의미를 부여합니다.
        3.  **성장 과정 서술**: 학생이 어떤 노력을 통해 어떻게 성장했는지 과정을 보여줍니다.
        4.  **문체**: 간결하고 사실적인 평어체(~함, ~음, ~보여줌, ~역량이 돋보임)를 사용합니다. 부정적인 표현이나 미사여구는 지양합니다.
        ---
        [학생 정보]
        - 과목: {subject}
        - 핵심 역량 키워드: {competency}
        - 학생 관찰 내용 (활동, 질문, 결과물, 태도 등): {observation}
        ---
        위 정보를 바탕으로, 학생의 역량과 성장이 생생하게 드러나는 교과세특 예시문을 2~3가지 버전으로 작성해 주십시오."""),

    # 3-2. 행발 (행동발달상황)
    "behavior_record": ChatPromptTemplate.from_template("""
        당신은 학생의 인성과 성장을 면밀히 관찰하는 대한민국 초·중학교의 베테랑 담임교사입니다. 주어진 정보를 바탕으로 학생의 행동발달상황이 구체적이고 긍정적으로 드러나는 예시문을 작성해야 합니다.

        [작성 규칙]
        1.  **구체적 행동 관찰**: 학생의 실제 행동, 말, 태도를 구체적으로 서술합니다. ('친구들과 잘 지냄' (X) -> '어려운 친구를 먼저 도와주고, 갈등 상황에서 중재 역할을 하며 원만한 학급 분위기 조성에 기여함' (O))
        2.  **성장과 변화 강조**: 학기 초와 비교하여 학생이 어떻게 성장하고 변화했는지를 보여줍니다.
        3.  **긍정적 표현**: 부족한 부분도 성장 가능성과 노력하는 모습으로 긍정적으로 표현합니다.
        4.  **인성 역량 연결**: 관찰된 행동을 '소통역량', '공동체역량', '자기관리역량' 등과 연결하여 의미를 부여합니다.
        5.  **문체**: 따뜻하고 격려하는 평어체(~함, ~보여줌, ~노력함, ~성장함)를 사용합니다.
        ---
        [학생 관찰 정보]
        - 핵심 행동 특성: {behavior_trait}
        - 구체적 관찰 내용 (행동, 태도, 변화 과정 등): {observation}
        - 특별히 강조하고 싶은 성장 포인트: {growth_point}
        ---
        위 정보를 바탕으로, 학생의 인성과 행동발달이 생생하게 드러나는 행발 예시문을 2~3가지 버전으로 작성해 주십시오."""),

    # 4. 학부모 답장
    "parent_reply": ChatPromptTemplate.from_template("""
        당신은 학생을 깊이 아끼고 학부모와 원활하게 소통하는 대한민국 초·중학교의 현명하고 따뜻한 담임 교사입니다. 학부모님이 보내신 메시지에 대해, 공감과 전문성을 바탕으로 정중하고 신뢰를 주는 답장 초안을 작성해야 합니다.

        [작성 규칙]
        1.  **공감으로 시작**: 학부모님의 걱정이나 마음에 먼저 공감하는 표현으로 문을 엽니다. ('어머님의 염려하시는 마음, 충분히 이해됩니다.')
        2.  **긍정적 관찰 사실 전달**: 자녀에 대한 긍정적인 관찰 내용이나 칭찬할 점을 함께 전달하여 안심시킵니다.
        3.  **구체적인 해결 방안 제시**: 문제 상황에 대해 교사로서 할 수 있는 구체적인 노력과 해결 방안을 제시합니다.
        4.  **함께 노력하는 자세**: 가정과의 연계와 협력을 강조하며 함께 노력하겠다는 의지를 보여줍니다.
        5.  **정중한 마무리**: 감사 인사와 함께 다음 소통을 기약하며 마무리합니다.
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
        1.  **제목**: 내용을 한눈에 알 수 있는 제목을 작성합니다. (예: OOO 안내, OOO 신청 안내 등)
        2.  **인사말**: 계절이나 시기에 맞는 따뜻한 인사말로 시작합니다.
        3.  **본문**: '언제, 어디서, 누가, 무엇을, 왜, 어떻게' 육하원칙에 따라 핵심 정보를 명확하고 간결하게 전달합니다. 필요한 경우 '아래' 또는 '다음'을 사용하여 항목을 구분합니다.
        4.  **강조**: 중요한 날짜나 시간, 준비물 등은 굵은 글씨나 밑줄을 사용하여 강조합니다.
        5.  **맺음말**: 학교 교육에 대한 관심과 협조에 감사하는 말로 마무리합니다.
        6.  **날짜 및 발신 명의**: 문서 하단에 발송 날짜와 학교장 직인을 포함한 발신 명의를 기재합니다.
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
tab1, tab2, tab3, tab4 = st.tabs(["📝 기안문 작성", "📚 생기부 기록", "💌 학부모 답장", "📢 가정통신문 작성"])

# 공통 함수: 체인 실행 및 결과 표시
def run_chain_and_display(chain_key, inputs, container):
    # .env 파일에서 키를 자동으로 로드하므로, 키 확인 로직이 필요 없습니다.
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.5) # api_key 인자가 없어도 자동으로 환경변수에서 찾습니다.
        prompt = PROMPTS[chain_key]
        chain = prompt | llm | StrOutputParser()

        with st.spinner("초안을 작성하고 있습니다... 잠시만 기다려주세요."):
            result = chain.invoke(inputs)
            st.session_state.generated_texts[chain_key] = result

        result_text = st.text_area("✍️ 생성 결과", value=st.session_state.generated_texts[chain_key], height=400, key=f"result_{chain_key}")
        
        # JavaScript를 사용한 클립보드 복사
        text_to_copy = st.session_state.generated_texts[chain_key].replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
        
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
                    
                    run_chain_and_display("plan", {
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
                    
                    run_chain_and_display("budget", {
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
                    
                    run_chain_and_display("submission", {
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
                    
                    run_chain_and_display("activity_report", {
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
                subject = st.text_input("과목", placeholder="예: 확률과 통계", key="subject_table")
            with col2:
                competency = st.text_input("핵심 역량 키워드", placeholder="예: 논리적 사고력, 문제 해결 능력, 탐구 역량", key="competency_table")
        
        # 학생 수 설정
        with st.container(border=True):
            st.subheader("👥 학생 수 설정")
            num_students = st.number_input("학생 수", min_value=1, max_value=10, value=3, step=1)
        
        # 학생 정보 입력 표
        if subject and competency:
            with st.container(border=True):
                st.subheader(f"📄 {subject} 교과세특 생성")
                
                # 세션 상태에 학생 데이터 초기화
                if 'student_data' not in st.session_state or len(st.session_state.student_data) != num_students:
                    st.session_state.student_data = [{"name": f"학생{i+1}", "observation": ""} for i in range(num_students)]
                
                # 표 헤더
                header_cols = st.columns([1, 2, 4, 1])
                with header_cols[0]:
                    st.markdown("**번호**")
                with header_cols[1]:
                    st.markdown("**이름**")
                with header_cols[2]:
                    st.markdown("**학습 내용 (관찰 내용)**")
                with header_cols[3]:
                    st.markdown("**상세**")
                
                st.divider()
                
                # 학생 데이터 입력 행
                for i in range(num_students):
                    cols = st.columns([1, 2, 4, 1])
                    
                    with cols[0]:
                        st.markdown(f"**{i+1:02d}**")
                    
                    with cols[1]:
                        st.session_state.student_data[i]["name"] = st.text_input(
                            "이름", 
                            value=st.session_state.student_data[i]["name"],
                            placeholder=f"학생{i+1}",
                            key=f"name_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with cols[2]:
                        st.session_state.student_data[i]["observation"] = st.text_area(
                            "관찰 내용",
                            value=st.session_state.student_data[i]["observation"],
                            placeholder=f"{st.session_state.student_data[i]['name']}의 학습 활동, 발표, 성장 모습 등을 구체적으로 기록해주세요.",
                            height=100,
                            key=f"obs_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with cols[3]:
                        st.markdown("**600**")
                    
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
                                        llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
                                        prompt = PROMPTS["student_record"]
                                        chain = prompt | llm | StrOutputParser()
                                        
                                        result = chain.invoke({
                                            "subject": subject,
                                            "competency": competency,
                                            "observation": data["observation"]
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
                
                for i, result_data in enumerate(st.session_state.generated_table_results):
                    with st.expander(f"{i+1:02d}. {result_data['name']} 교과세특", expanded=True):
                        st.text_area(
                            f"{result_data['name']} 결과",
                            value=result_data['result'],
                            height=200,
                            key=f"result_display_{i}",
                            label_visibility="collapsed"
                        )
                
                # 전체 결과 복사 버튼
                all_results = "\n\n" + "="*50 + "\n\n".join([f"{data['name']} 교과세특:\n{data['result']}" for data in st.session_state.generated_table_results])
                all_text_to_copy = all_results.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
                
                all_copy_button_html = f"""
                <div style="margin: 20px 0; text-align: center;">
                    <button onclick="copyAllResults()" style="
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 16px;
                        font-weight: bold;
                    ">
                        📋 전체 결과 복사
                    </button>
                    <div id="copy-all-message" style="
                        display: none;
                        color: green;
                        font-weight: bold;
                        margin-top: 10px;
                    ">
                        ✅ 전체 결과가 복사되었습니다!
                    </div>
                </div>
                <script>
                    function copyAllResults() {{
                        const text = `{all_text_to_copy}`;
                        
                        if (navigator.clipboard && window.isSecureContext) {{
                            navigator.clipboard.writeText(text).then(function() {{
                                showAllCopyMessage();
                            }}).catch(function(err) {{
                                fallbackCopyAll(text);
                            }});
                        }} else {{
                            fallbackCopyAll(text);
                        }}
                    }}
                    
                    function fallbackCopyAll(text) {{
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
                            showAllCopyMessage();
                        }} catch (err) {{
                            console.error('복사 실패:', err);
                            alert('복사에 실패했습니다.');
                        }}
                        
                        document.body.removeChild(textArea);
                    }}
                    
                    function showAllCopyMessage() {{
                        const message = document.getElementById('copy-all-message');
                        message.style.display = 'block';
                        setTimeout(function() {{
                            message.style.display = 'none';
                        }}, 3000);
                    }}
                </script>
                """
                
                st.components.v1.html(all_copy_button_html, height=100)
        
        else:
            st.info("ℹ️ 과목과 핵심 역량을 먼저 입력해주세요.")
    
    # 행발 서브탭
    with record_tab2:
        st.markdown("학생의 행동 특성과 성장 과정을 입력하면, 따뜻하고 긍정적인 행동발달상황을 생성합니다.")
        with st.container(border=True):
            behavior_trait = st.text_input("핵심 행동 특성", placeholder="예: 배려심, 리더십, 소통능력, 자기관리역량")
            observation_behavior = st.text_area("구체적 관찰 내용", placeholder="학생의 실제 행동, 말, 태도, 변화 과정 등을 구체적으로 기록해주세요.\n(예시) 학기 초 소극적이었던 학생이 모둠 활동을 통해 점차 자신감을 획득하고, 친구들과 적극적으로 소통하며 학급 활동에 참여하는 모습을 보여줌. 어려운 친구를 먼저 도와주는 배려심도 돋보임.", height=180)
            growth_point = st.text_input("특별히 강조하고 싶은 성장 포인트", placeholder="예: 소통능력 향상, 리더십 발휘, 자신감 증진")

            if st.button("✨ 행발 예시 생성", use_container_width=True, key="behavior_record"):
                if all([behavior_trait, observation_behavior, growth_point]):
                    run_chain_and_display("behavior_record", {"behavior_trait": behavior_trait, "observation": observation_behavior, "growth_point": growth_point}, st)
                else: st.warning("모든 항목을 입력해주세요.")

# --- 탭 3: 학부모 답장 ---
with tab3:
    st.header("✉️ 학부모 답장 도우미")
    st.markdown("학부모님의 메시지와 답장의 핵심 방향을 입력하면, 따뜻하고 전문적인 답장 초안을 만들어 드립니다.")
    with st.container(border=True):
        parent_message = st.text_area("학부모님 메시지 원문", placeholder="이곳에 학부모님께 받은 메시지를 그대로 붙여넣어 주세요.", height=150)
        tone = st.text_input("답장 어조 및 핵심 방향", placeholder="예: 따뜻하고 공감적으로, 해결 방안 중심으로, 긍정적인 면을 부각하여")

        if st.button("✨ 답장 초안 생성", use_container_width=True, key="parent_reply"):
            if all([parent_message, tone]):
                run_chain_and_display("parent_reply", {"parent_message": parent_message, "tone": tone}, st)
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
                # 기본값으로 설정
                run_chain_and_display("newsletter", {
                    "title": "현장체험학습 안내", 
                    "grade": "해당 학년", 
                    "main_points": main_points, 
                    "school_name": "OO초등학교"
                }, st)
            else: 
                st.warning("핵심 내용을 입력해주세요.")

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