import re
import streamlit as st

def format_menu(menu_string: str) -> str:
    """
    주간 급식표 메뉴 문자열을 각 메뉴별로 줄바꿈하여 포맷팅합니다.
    
    Args:
        menu_string (str): 원본 메뉴 문자열
        
    Returns:
        str: 포맷팅된 메뉴 문자열 (각 메뉴가 새 줄에 표시)
        
    Examples:
        >>> menu = "• 친환경쌀차조밥 들깨옹심이국 (5.6) 제육볶음 (5.6.10.13) 부추김무침 (5.6.13)"
        >>> print(format_menu(menu))
        • 친환경쌀차조밥 들깨옹심이국 (5.6)
        • 제육볶음 (5.6.10.13)
        • 부추김무침 (5.6.13)
    """
    
    if not menu_string or not menu_string.strip():
        return ""
    
    # 문자열 정리 (앞뒤 공백 제거, 여러 공백을 하나로 통합)
    cleaned_menu = re.sub(r'\s+', ' ', menu_string.strip())
    
    # 기존 글머리 기호 제거 (맨 앞의 • 제거)
    if cleaned_menu.startswith('• '):
        cleaned_menu = cleaned_menu[2:]
    
    # 정규 표현식 패턴 설명:
    # ([가-힣a-zA-Z0-9\s]+) - 메뉴명 (한글, 영문, 숫자, 공백 포함)
    # \s* - 선택적 공백
    # \(([0-9.]+)\) - 괄호 안의 알레르기 정보 (숫자와 점만)
    # 이 패턴이 메뉴명 + 알레르기정보 하나의 완전한 메뉴 항목을 매칭
    
    pattern = r'([가-힣a-zA-Z0-9\s]+?)\s*\(([0-9.]+)\)'
    
    # findall로 모든 메뉴 항목 찾기
    matches = re.findall(pattern, cleaned_menu)
    
    if not matches:
        # 패턴이 매칭되지 않으면 원본 문자열 반환 (글머리 기호만 추가)
        return f"• {cleaned_menu}"
    
    # 각 매칭된 항목을 글머리 기호와 함께 포맷팅
    formatted_items = []
    for menu_name, allergy_info in matches:
        # 메뉴명의 앞뒤 공백 제거
        menu_name = menu_name.strip()
        formatted_item = f"• {menu_name} ({allergy_info})"
        formatted_items.append(formatted_item)
    
    # 줄바꿈으로 연결하여 반환
    return '\n'.join(formatted_items)


def format_menu_advanced(menu_string: str) -> str:
    """
    더 복잡한 패턴을 처리할 수 있는 고급 메뉴 포맷터
    
    Args:
        menu_string (str): 원본 메뉴 문자열
        
    Returns:
        str: 포맷팅된 메뉴 문자열
    """
    
    if not menu_string or not menu_string.strip():
        return ""
    
    # 문자열 정리
    cleaned_menu = re.sub(r'\s+', ' ', menu_string.strip())
    
    # 기존 글머리 기호 제거
    if cleaned_menu.startswith('• '):
        cleaned_menu = cleaned_menu[2:]
    
    # 여러 패턴을 시도해서 가장 잘 매칭되는 것 사용
    patterns = [
        # 패턴 1: 기본 패턴 (메뉴명 + 알레르기 정보)
        r'([가-힣a-zA-Z0-9\s]+?)\s*\(([0-9.,\s]+)\)',
        
        # 패턴 2: 더 유연한 패턴 (특수문자 포함)
        r'([가-힣a-zA-Z0-9\s·]+?)\s*\(([0-9.,\s]+)\)',
        
        # 패턴 3: 알레르기 정보가 없는 경우도 고려
        r'([가-힣a-zA-Z0-9\s·]+?)(?=\s[가-힣]|\s*$)'
    ]
    
    best_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, cleaned_menu)
        if matches and len(matches) > len(best_matches):
            best_matches = matches
    
    if not best_matches:
        return f"• {cleaned_menu}"
    
    # 포맷팅
    formatted_items = []
    for match in best_matches:
        if isinstance(match, tuple) and len(match) == 2:
            menu_name, allergy_info = match
            menu_name = menu_name.strip()
            allergy_info = allergy_info.strip()
            formatted_item = f"• {menu_name} ({allergy_info})"
        else:
            # 알레르기 정보가 없는 경우
            menu_name = match if isinstance(match, str) else match[0]
            menu_name = menu_name.strip()
            formatted_item = f"• {menu_name}"
        
        formatted_items.append(formatted_item)
    
    return '\n'.join(formatted_items)


# 테스트 함수
def test_format_menu():
    """format_menu 함수 테스트"""
    
    test_cases = [
        "• 친환경쌀차조밥 들깨옹심이국 (5.6) 제육볶음 (5.6.10.13) 부추김무침 (5.6.13) 배추김치 (9) 미니슈크림파이 (1.2.5.6)",
        "친환경쌀밥 (5.6) 미소된장국 (5.6) 돈가스 (1.2.5.6.10.12.13.15.16.18) 무생채 (13) 배추김치 (9)",
        "• 흑미밥 콩나물국 (5) 닭볶음탕 (15) 시금치나물 (5.6) 깍두기 (9.13)"
    ]
    
    print("=== format_menu 함수 테스트 ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"테스트 케이스 {i}:")
        print(f"입력: {test_case}")
        print(f"출력:")
        print(format_menu(test_case))
        print("-" * 50)


# Streamlit 앱에서 사용하는 예시
def streamlit_example():
    """Streamlit에서 format_menu 함수 사용 예시"""
    
    st.title("📅 주간 급식표 (개선된 버전)")
    
    # 예시 데이터
    sample_menu_data = {
        "2024-01-15": "• 친환경쌀차조밥 들깨옹심이국 (5.6) 제육볶음 (5.6.10.13) 부추김무침 (5.6.13) 배추김치 (9) 미니슈크림파이 (1.2.5.6)",
        "2024-01-16": "친환경쌀밥 (5.6) 미소된장국 (5.6) 돈가스 (1.2.5.6.10.12.13.15.16.18) 무생채 (13) 배추김치 (9)",
        "2024-01-17": "• 흑미밥 콩나물국 (5) 닭볶음탕 (15) 시금치나물 (5.6) 깍두기 (9.13)"
    }
    
    # 컬럼 생성
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    days = ["월요일", "화요일", "수요일"]
    
    for i, (day, col) in enumerate(zip(days, cols)):
        with col:
            st.subheader(f"{day} (01/{15+i})")
            
            # 날짜에 해당하는 메뉴 데이터 가져오기
            date_key = f"2024-01-{15+i}"
            if date_key in sample_menu_data:
                original_menu = sample_menu_data[date_key]
                
                # format_menu 함수 적용
                formatted_menu = format_menu(original_menu)
                
                # Streamlit에 표시
                st.markdown(formatted_menu)
                
                # 구분선
                st.markdown("---")
                
                # 원본과 비교를 위한 expander (선택사항)
                with st.expander("원본 데이터 보기"):
                    st.text(original_menu)
            else:
                st.write("급식 없음")


# 기존 Streamlit 코드 수정 방법 예시
def integration_example():
    """기존 Streamlit 코드에 format_menu 함수를 적용하는 방법"""
    
    # 기존 코드 (수정 전)
    """
    # 기존 방식
    for line in menu_lines[:6]:  # 최대 6줄
        if line.strip():
            st.write(f"• {line.strip()}")
    """
    
    # 새로운 코드 (수정 후)
    """
    # 개선된 방식
    original_menu_text = meal['DDISH_NM']  # 원본 메뉴 데이터
    
    # HTML 태그 제거 및 기본 정리
    menu_text = re.sub(r'<br\s*/?>', '\n', original_menu_text)
    menu_text = re.sub(r'<[^>]+>', '', menu_text)
    menu_text = re.sub(r'\s+', ' ', menu_text).strip()
    
    # format_menu 함수 적용
    formatted_menu = format_menu(menu_text)
    
    # Streamlit에 출력
    st.markdown(formatted_menu)
    """


if __name__ == "__main__":
    # 테스트 실행
    test_format_menu()
    
    print("\n" + "="*50)
    print("Streamlit 앱을 실행하려면:")
    print("streamlit run menu_formatter.py")