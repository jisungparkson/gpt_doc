"""
급식 식단표 탭
"""
import streamlit as st
import requests
from datetime import datetime, timedelta
import calendar
from utils import format_final_menu, format_calendar_entry, format_menu_for_display

def draw_meals_tab():
    """급식 식단표 탭 UI"""
    st.header("🍽️ 급식 식단표")
    st.markdown("전주화정초등학교의 급식 식단표를 월별 또는 주별로 확인하세요.")
    
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