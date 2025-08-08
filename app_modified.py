import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import streamlit.components.v1 as components
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
    """
    HTML과 <br> 태그가 포함된 메뉴 문자열을
    달력 표시에 적합한 여러 줄의 텍스트로 변환합니다.
    """
    if not isinstance(html_string, str) or not html_string.strip():
        return ""

    # 1. <br> 태그를 줄바꿈 문자(\n)로 먼저 변경합니다.
    # 대소문자 구분 없이 <br>, <BR>, <br /> 등을 모두 처리합니다.
    text_with_newlines = re.sub(r'<br\s*/?>', '\n', html_string, flags=re.IGNORECASE)

    # 2. 다른 HTML 태그들도 제거합니다.
    text_without_html = re.sub(r'<[^>]+>', '', text_with_newlines)

    # 3. 연속된 줄바꿈을 하나로 줄입니다.
    text_clean_newlines = re.sub(r'\n+', '\n', text_without_html)

    # 4. 앞뒤 공백을 제거합니다.
    return text_clean_newlines.strip()

def format_menu_for_calendar(menu_data: str) -> str:
    """
    DB에서 가져온 급식 메뉴 데이터를 달력 표시용으로 변환
    """
    if not menu_data or menu_data.strip() == "":
        return ""
    
    # <br> 태그를 줄바꿈으로 변환
    clean_text = menu_data.replace('<br/>', '\n').replace('<br>', '\n')
    
    # 알레르기 정보 괄호 제거 (예: (1.2.3))
    clean_text = re.sub(r'\([0-9.,\s]*\)', '', clean_text)
    
    # 앞뒤 공백 제거 및 빈 줄 제거
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    
    return '\n'.join(lines)

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
    # 메뉴 항목은 일반적으로 한글, 영문, 숫자와 괄호로 구성
    # 괄호 안의 숫자는 알레르기 정보를 나타냄 (예: (1.2.13))
    patterns = [
        # 패턴 1: "메뉴명 (알레르기정보) " 형태
        r'([가-힣\w\s]+(?:\([0-9.,\s]*\))?)\s*',
        # 패턴 2: 한글로 시작하는 메뉴명들을 공백으로 구분
        r'([가-힣][가-힣\w\s]*(?:\([0-9.,\s]*\))?)\s*',
        # 패턴 3: 띄어쓰기로 구분된 단어들 중 한글 포함
        r'(\S*[가-힣]\S*(?:\([0-9.,\s]*\))?)\s*'
    ]
    
    # 3. 각 패턴으로 메뉴 항목 추출 시도
    for pattern in patterns:
        matches = re.findall(pattern, cleaned_string)
        if matches:
            # 빈 문자열이나 의미없는 문자 제거
            valid_matches = [match.strip() for match in matches if match.strip() and len(match.strip()) > 1]
            if valid_matches:
                # 각 메뉴 앞에 "- " 추가하여 마크다운 리스트 형식으로 만들기
                return "\n".join([f"- {menu}" for menu in valid_matches])
    
    # 4. 정규식으로 분리가 안 되면 쉼표나 공백으로 단순 분리 시도
    separators = [',', '  ', ' ']
    for separator in separators:
        if separator in cleaned_string:
            parts = [part.strip() for part in cleaned_string.split(separator) if part.strip()]
            if len(parts) > 1:  # 실제로 분리가 되었다면
                return "\n".join([f"- {part}" for part in parts])
    
    # 5. 모든 방법이 실패하면 원본 문자열을 그대로 리스트 형식으로 반환
    return f"- {cleaned_string}"

# .env 파일 로드
load_dotenv()

# Streamlit 페이지 구성
st.set_page_config(
    page_title="📚 급식 메뉴와 함께하는 AI 교실",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 기본 스타일 설정
st.markdown("""
<style>
.main-title {
    text-align: center;
    color: #2E86C1;
    font-size: 2.5rem;
    margin-bottom: 1rem;
}
.sub-title {
    text-align: center;
    color: #5D6D7E;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}
.info-box {
    background-color: #EBF5FB;
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #2E86C1;
    margin: 1rem 0;
}
.menu-card {
    background-color: #FFFFFF;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
.stSelectbox > div > div > select {
    background-color: #F8F9FA;
}
</style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown('<h1 class="main-title">📚 급식 메뉴와 함께하는 AI 교실 🍽️</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">오늘의 급식 메뉴를 확인하고, AI와 함께 다양한 주제로 대화해보세요!</p>', unsafe_allow_html=True)

# 사이드바 구성
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    
    # 기능 선택
    main_function = st.selectbox(
        "📋 원하는 기능을 선택하세요",
        ["🍽️ 급식 메뉴 조회", "💬 AI 채팅"],
        help="급식 메뉴 조회 또는 AI와의 채팅 중 선택하세요"
    )

# 메인 콘텐츠
if main_function == "🍽️ 급식 메뉴 조회":
    st.header("🍽️ 급식 메뉴 조회")
    
    # 조회 방식 선택
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            view_mode = st.radio(
                "📊 조회 방식 선택",
                ["월별 조회", "주별 조회"],
                help="월별 달력으로 보거나 주별로 상세히 볼 수 있습니다"
            )

    # API 관련 함수들
    import requests
    from datetime import datetime, timedelta
    import json

    def get_meal_data_for_month(year_month: str):
        """특정 월의 급식 데이터를 가져오는 함수"""
        try:
            # NEIS Open API 설정
            api_key = "8ba8fbba74804bf28e44b77ab71ba5c4"
            base_url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
            
            params = {
                'KEY': api_key,
                'Type': 'json',
                'pIndex': 1,
                'pSize': 100,
                'ATPT_OFCDC_SC_CODE': 'G10',
                'SD_SCHUL_CODE': '7430310',
                'MLSV_YMD': year_month,
                'MMEAL_SC_CODE': '2'  # 중식
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # API 응답 구조 확인
                if 'mealServiceDietInfo' in data and len(data['mealServiceDietInfo']) > 1:
                    meal_info = data['mealServiceDietInfo'][1]['row']
                    return meal_info
                else:
                    # 데이터가 없는 경우
                    return []
            else:
                st.error(f"API 호출 실패: {response.status_code}")
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
            meal_dict = {item['MLSV_YMD']: item['DDISH_NM'] for item in meal_data}

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
            current_date = start_of_week
            while current_date <= end_of_week:
                year_month = f"{current_date.year}{current_date.month:02d}"
                months_to_fetch.add(year_month)
                current_date += timedelta(days=1)
            
            # 각 월의 데이터를 가져와서 합치기
            all_meal_data = []
            for year_month in months_to_fetch:
                month_data = get_meal_data_for_month(year_month)
                if month_data:
                    all_meal_data.extend(month_data)
        
        if all_meal_data:
            # 해당 주의 날짜들만 필터링
            week_meal_data = []
            current_date = start_of_week
            while current_date <= end_of_week:
                date_str = current_date.strftime('%Y%m%d')
                for meal in all_meal_data:
                    if meal['MLSV_YMD'] == date_str:
                        meal['weekday'] = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'][current_date.weekday()]
                        meal['display_date'] = current_date.strftime('%m월 %d일')
                        week_meal_data.append(meal)
                        break
                current_date += timedelta(days=1)
            
            if week_meal_data:
                st.success(f"📊 **{len(week_meal_data)}일간의 급식 정보**를 찾았습니다!")
                
                # 주간 급식 표시
                for meal in week_meal_data:
                    with st.expander(f"🗓️ {meal['display_date']} ({meal['weekday']})", expanded=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # 메뉴를 보기 좋게 포맷팅
                            formatted_menu = format_menu_for_display(meal['DDISH_NM'])
                            st.markdown(f"""
                            <div class="menu-card">
                                <h4>🍽️ 중식 메뉴</h4>
                                {formatted_menu}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # 칼로리 정보 (있는 경우)
                            if 'CAL_INFO' in meal and meal['CAL_INFO']:
                                st.metric("칼로리", f"{meal['CAL_INFO']}")
                            
                            # 영양 정보 (있는 경우)
                            if 'NTR_INFO' in meal and meal['NTR_INFO']:
                                st.info(f"**영양정보**\n{meal['NTR_INFO']}")
            else:
                st.warning("선택한 주간에 급식 정보가 없습니다.")
        else:
            st.error("급식 데이터를 가져오는데 실패했습니다.")

elif main_function == "💬 AI 채팅":
    st.header("💬 AI와 함께하는 교실 대화")
    
    # OpenAI API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.error("⚠️ OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        st.stop()
    
    # 대화 모드 선택
    with st.container():
        st.markdown("### 🎯 대화 주제 선택")
        chat_mode = st.selectbox(
            "어떤 주제로 대화하고 싶나요?",
            [
                "🍎 영양과 건강한 식습관",
                "🧑‍🍳 요리와 음식 문화", 
                "🌱 환경과 지속가능한 식단",
                "📚 일반 학습 도움",
                "🎨 창의적 글쓰기",
                "🔬 과학 실험과 탐구",
                "🗣️ 자유 대화"
            ]
        )
    
    # 채팅 모드별 시스템 프롬프트 설정
    system_prompts = {
        "🍎 영양과 건강한 식습관": """
        당신은 영양학과 건강한 식습관을 전문으로 하는 친근한 AI 선생님입니다.
        학생들이 올바른 식습관을 기를 수 있도록 도와주세요.
        - 각 영양소의 역할과 중요성을 쉽게 설명해주세요
        - 균형잡힌 식단의 중요성을 강조해주세요
        - 나쁜 식습관의 문제점을 부드럽게 알려주세요
        - 건강한 간식이나 요리법을 추천해주세요
        항상 격려하고 긍정적인 톤으로 대화해주세요.
        """,
        
        "🧑‍🍳 요리와 음식 문화": """
        당신은 요리와 다양한 음식 문화를 사랑하는 요리 선생님입니다.
        - 다양한 나라의 음식 문화를 소개해주세요
        - 간단하고 안전한 요리법을 알려주세요
        - 식재료의 특성과 활용법을 설명해주세요
        - 음식의 역사나 유래를 재미있게 들려주세요
        학생들이 요리에 흥미를 가질 수 있도록 도와주세요.
        """,
        
        "🌱 환경과 지속가능한 식단": """
        당신은 환경을 생각하는 친환경 식단 전문가입니다.
        - 음식과 환경의 관계를 쉽게 설명해주세요
        - 음식물 쓰레기를 줄이는 방법을 알려주세요
        - 지역 농산물과 제철 음식의 중요성을 강조해주세요
        - 친환경적인 식생활 습관을 제안해주세요
        환경보호의식을 기를 수 있도록 도와주세요.
        """,
        
        "📚 일반 학습 도움": """
        당신은 모든 과목을 도와주는 친근한 AI 학습 도우미입니다.
        - 어려운 개념을 쉽고 재미있게 설명해주세요
        - 학습자의 수준에 맞춰 단계적으로 설명해주세요
        - 실생활 예시를 들어 이해를 도와주세요
        - 학습 동기를 부여하고 격려해주세요
        학생이 스스로 답을 찾을 수 있도록 힌트를 제공해주세요.
        """,
        
        "🎨 창의적 글쓰기": """
        당신은 창의적 글쓰기를 도와주는 영감을 주는 선생님입니다.
        - 다양한 글쓰기 아이디어를 제공해주세요
        - 창의적인 표현 방법을 알려주세요
        - 학생의 상상력을 자극하는 질문을 해주세요
        - 글쓰기 기법과 팁을 공유해주세요
        학생들이 자유롭게 상상하고 표현할 수 있도록 도와주세요.
        """,
        
        "🔬 과학 실험과 탐구": """
        당신은 과학을 사랑하는 실험 선생님입니다.
        - 일상 속 과학 현상을 흥미롭게 설명해주세요
        - 안전한 간단한 실험을 제안해주세요
        - 과학적 호기심을 자극하는 질문을 해주세요
        - 과학자들의 이야기를 들려주세요
        학생들이 과학에 흥미를 가질 수 있도록 도와주세요.
        """,
        
        "🗣️ 자유 대화": """
        당신은 학생들과 자유롭게 대화하는 친근한 AI 친구입니다.
        - 학생의 관심사에 공감하며 대화해주세요
        - 긍정적이고 격려하는 톤을 유지해주세요
        - 적절한 질문으로 대화를 이어가주세요
        - 건전하고 교육적인 내용으로 대화를 유도해주세요
        학생이 편안하게 대화할 수 있는 분위기를 만들어주세요.
        """
    }
    
    # LLM 초기화
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        api_key=api_key
    )
    
    # 채팅 히스토리 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 모드 변경 시 히스토리 초기화
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = chat_mode
    elif st.session_state.current_mode != chat_mode:
        st.session_state.messages = []
        st.session_state.current_mode = chat_mode
    
    # 채팅 인터페이스
    st.markdown("### 💭 대화 시작")
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("궁금한 것을 물어보세요!"):
        # 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            try:
                # 프롬프트 템플릿 생성
                template = system_prompts[chat_mode] + """
                
                이전 대화 내용:
                {chat_history}
                
                사용자 질문: {user_input}
                
                답변:"""
                
                prompt_template = ChatPromptTemplate.from_template(template)
                
                # 채팅 히스토리 준비
                chat_history = ""
                for msg in st.session_state.messages[-6:]:  # 최근 6개 메시지만 사용
                    if msg["role"] == "user":
                        chat_history += f"사용자: {msg['content']}\n"
                    else:
                        chat_history += f"AI: {msg['content']}\n"
                
                # 체인 생성 및 실행
                chain = prompt_template | llm | StrOutputParser()
                
                # 스트리밍으로 응답 생성
                response = st.write_stream(
                    chain.stream({
                        "chat_history": chat_history,
                        "user_input": prompt
                    })
                )
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"죄송합니다. 오류가 발생했습니다: {str(e)}")
    
    # 사이드바에 채팅 관련 정보
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 채팅 도구")
        
        # 대화 초기화 버튼
        if st.button("🔄 대화 내용 초기화"):
            st.session_state.messages = []
            st.rerun()
        
        # 채팅 통계
        if st.session_state.messages:
            user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
            ai_messages = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
            st.markdown(f"**📊 대화 통계**")
            st.markdown(f"- 사용자 메시지: {user_messages}개")
            st.markdown(f"- AI 응답: {ai_messages}개")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #7F8C8D; font-size: 0.9rem;'>
        📚 급식 메뉴와 함께하는 AI 교실 | Made with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True
)