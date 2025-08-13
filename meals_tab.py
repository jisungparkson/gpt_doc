"""
급식 식단표 탭 - 최종 복원 버전 (월별 5열, 자동 높이, 만능 정리)
"""
import streamlit as st
import requests
import calendar
from datetime import datetime, timedelta
from utils import format_meal_menu


API_KEY = "2d74e530f4334ab9906e6171f031560a"
OFFICE_CODE = "P10"      # 전북
SCHOOL_CODE = "8332156"  # 전주화정초
BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


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
        elif 'RESULT' in data and data['RESULT'].get('CODE') == 'INFO-200':
            return []
        else:
            error_message = data.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류가 발생했습니다.')
            st.error(f"API 오류: {error_message}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"네트워크 오류가 발생했습니다: {e}")
        return None


def get_weekly_meal_data(start_date: str):
    """특정 주의 급식 데이터를 API를 통해 가져옵니다."""
    # 주간 종료일 계산 (시작일 + 4일)
    start_dt = datetime.strptime(start_date, "%Y%m%d")
    end_dt = start_dt + timedelta(days=4)
    end_date = end_dt.strftime("%Y%m%d")
    
    params = {
        'KEY': API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 100,
        'ATPT_OFCDC_SC_CODE': OFFICE_CODE,
        'SD_SCHUL_CODE': SCHOOL_CODE,
        'MLSV_FROM_YMD': start_date,
        'MLSV_TO_YMD': end_date
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'mealServiceDietInfo' in data:
            return data['mealServiceDietInfo'][1]['row']
        elif 'RESULT' in data and data['RESULT'].get('CODE') == 'INFO-200':
            return []
        else:
            error_message = data.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류가 발생했습니다.')
            st.error(f"API 오류: {error_message}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"네트워크 오류가 발생했습니다: {e}")
        return None


def draw_meals_tab():
    """급식 식단표 탭 UI (월별/주별 조회 복원)"""
    st.header("🍽️ 급식 식단표")
    st.markdown("전주화정초등학교의 급식 식단을 월별 또는 주별로 확인하세요.")

    # 조회 방식 선택
    view_mode = st.radio("조회 방식 선택", ["월별 조회", "주별 조회"], horizontal=True)

    if view_mode == "월별 조회":
        # 월별 조회 UI
        st.subheader("📅 월별 급식 조회")

        today = datetime.now()
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            selected_year = st.selectbox("연도 선택", range(today.year - 1, today.year + 2), index=1)

        with col2:
            selected_month = st.selectbox("월 선택", range(1, 13), index=today.month - 1)

        with col3:
            st.info(f"📅 {selected_year}년 {selected_month}월 급식 달력")

        # 데이터 조회
        year_month = f"{selected_year}{selected_month:02d}"
        with st.spinner("급식 데이터를 가져오는 중..."):
            meal_data = get_meal_data_for_month(year_month)

        if meal_data is None:
            st.warning("해당 월의 급식 정보를 가져올 수 없습니다.")
            return

        # 날짜별 메뉴 정리 (키 존재 여부 안전 처리)
        meal_dict = {item.get('MLSV_YMD'): item.get('DDISH_NM', '') for item in meal_data if item.get('MLSV_YMD')}

        # 달력 헤더 (월~금, 5열)
        days_of_week = ["월", "화", "수", "목", "금"]
        cols = st.columns(5)
        for col, day in zip(cols, days_of_week):
            with col:
                st.markdown(f"<p style='text-align: center;'><b>{day}</b></p>", unsafe_allow_html=True)

        st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)

        # 월별 달력 생성 (월~금만 출력)
        cal = calendar.Calendar()
        month_days = cal.monthdatescalendar(selected_year, selected_month)

        for week in month_days:
            cols = st.columns(5)  # 월~금 5열
            for i in range(5):
                day = week[i]
                with cols[i]:
                    if day.month == selected_month:
                        date_key = day.strftime("%Y%m%d")
                        raw_menu = meal_dict.get(date_key, "")

                        if raw_menu:
                            cleaned_menu = format_meal_menu(raw_menu)
                            # 자동 높이: min-height만 지정, 내용은 줄바꿈 처리
                            st.markdown(
                                f"""
                                <div style='border: 1px solid #eee; border-radius: 5px; padding: 8px; min-height: 120px;'>
                                    <b style='color: #333; display: block; margin-bottom: 6px;'>{day.day}</b>
                                    <div style='font-size: 0.9em; line-height: 1.6;'>
                                        {cleaned_menu.replace('\n', '<br>')}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            # 메뉴가 없는 날: 깔끔한 빈 칸
                            st.markdown(
                                f"""
                                <div style='border: 1px solid #f1f3f5; border-radius: 5px; padding: 8px; min-height: 120px;'>
                                    <b style='color: #333;'>{day.day}</b>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        # 다른 달 날짜: 흐리게 비활성 표시
                        st.markdown(
                            f"<div style='border: 1px solid #f8f9fa; border-radius: 5px; padding: 8px; min-height: 120px; color: #adb5bd;'>{day.day}</div>",
                            unsafe_allow_html=True,
                        )

    elif view_mode == "주별 조회":
        st.subheader("📅 주별 급식 조회")
        
        today = datetime.now().date()
        selected_date = st.date_input("조회할 주를 선택하세요 (해당 주의 아무 날짜나 선택)", today, key="weekly_date_input")

        if selected_date:
            with st.spinner("주간 급식 데이터를 가져오는 중..."):
                # 해당 주의 시작일(월요일)과 종료일(금요일) 계산
                start_of_week = selected_date - timedelta(days=selected_date.weekday())
                end_of_week = start_of_week + timedelta(days=4)
                
                st.info(f"조회 기간: {start_of_week.strftime('%Y년 %m월 %d일')} ~ {end_of_week.strftime('%Y년 %m월 %d일')}")
                
                # 주간 급식 데이터 가져오기 (시작일 기준)
                meal_data = get_weekly_meal_data(start_of_week.strftime("%Y%m%d"))

                if meal_data:
                    # 올바른 키 사용 (DDISH_NM)
                    weekly_menu = {item['MLSV_YMD']: item.get('DDISH_NM', '') for item in meal_data}
                    
                    days = [(start_of_week + timedelta(days=i)) for i in range(5)] # 월~금
                    day_names = ["월", "화", "수", "목", "금"]
                    
                    # 주별 조회 결과를 깔끔하게 표시
                    cols = st.columns(5)
                    for i, day in enumerate(days):
                        with cols[i]:
                            st.markdown(f"**{day.strftime('%m/%d')} ({day_names[i]})**")
                            raw_menu = weekly_menu.get(day.strftime("%Y%m%d"), "")
                            
                            if raw_menu:
                                # utils.py의 만능 메뉴 정리 함수 사용
                                cleaned_menu = format_meal_menu(raw_menu)
                                st.markdown(
                                    f"<div style='font-size: 0.9em; line-height: 1.7; padding: 10px; border: 1px solid #eee; border-radius: 5px; min-height: 120px;'>{cleaned_menu.replace(chr(10), '<br>')}</div>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    "<div style='font-size: 0.9em; padding: 10px; border: 1px solid #f1f3f5; border-radius: 5px; min-height: 120px; color: #aaa; text-align: center;'>급식 없음</div>", 
                                    unsafe_allow_html=True
                                )

                else:
                    st.warning("해당 주에는 등록된 급식 정보가 없습니다.")