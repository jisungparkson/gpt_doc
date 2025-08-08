import openai
import json
import streamlit as st
from typing import Dict, List, Any

def create_giamun_prompt_for_gpt(user_input: Dict[str, str]) -> str:
    """
    사용자 입력을 받아 GPT API에 전달할 기안문 생성 프롬프트를 생성합니다.
    
    Args:
        user_input (Dict[str, str]): 사용자 입력 데이터
            - type: 기안 종류
            - title: 제목
            - details: 주요 내용
            - attachments: 첨부 파일 (문자열로 입력받아 내부에서 리스트로 변환)
    
    Returns:
        str: GPT API에 전달할 완성된 프롬프트
    """
    
    # 첨부파일 문자열을 리스트로 변환 (줄바꿈 또는 콤마로 분리)
    attachments = user_input.get('attachments', '')
    if attachments.strip():
        # 줄바꿈으로 먼저 분리하고, 콤마로도 분리
        attachment_list = []
        for line in attachments.split('\n'):
            if ',' in line:
                attachment_list.extend([item.strip() for item in line.split(',') if item.strip()])
            else:
                if line.strip():
                    attachment_list.append(line.strip())
        attachments_text = ', '.join(attachment_list)
    else:
        attachments_text = "없음"
    
    prompt = f"""너는 대한민국 공문서(기안문)의 구조를 완벽하게 이해하고, 그 내용을 구조화된 JSON 데이터로 생성하는 전문가다.
너의 유일한 임무는 최종적으로 보이는 텍스트를 만드는 것이 아니라, Python 코드가 사용할 수 있도록 기안문의 내용을 정확한 JSON 형식으로만 출력하는 것이다.

[JSON 출력 구조 - 반드시 이 형식을 준수하라]
{{
    "related_basis": ["관련 근거 1", "관련 근거 2", ...],
    "introduction": "본문 시작 문장",
    "items": [
        {{
            "content": "주요 항목 내용",
            "sub_items": [
                {{
                    "content": "하위 항목 내용",
                    "sub_items": [...]
                }}
            ]
        }}
    ],
    "attachments": ["첨부파일1.pdf", "첨부파일2.hwp", ...]
}}

[중요한 규칙]
1. 반드시 유효한 JSON 형식으로만 응답하라. 다른 설명이나 텍스트는 일체 포함하지 마라.
2. related_basis는 해당 기안의 법적 근거나 관련 규정을 포함하라.
3. introduction은 기안의 목적과 배경을 간단히 설명하는 문장이어야 한다.
4. items는 기안의 핵심 내용을 구조화된 형태로 작성하라.
5. 하위 항목(sub_items)은 필요시에만 사용하고, 깊이는 최대 3단계까지만 허용한다.
6. attachments는 실제 첨부파일명을 포함하라.

[사용자 정보]
- 기안 종류: {user_input.get('type', '')}
- 제목: {user_input.get('title', '')}
- 주요 내용: {user_input.get('details', '')}
- 첨부 파일: {attachments_text}

위 정보를 바탕으로 기안문 내용을 JSON 객체로 생성하라. JSON 응답만 제공하고 다른 텍스트는 포함하지 마라."""

    return prompt


def render_giamun_from_json(data: Dict[str, Any]) -> str:
    """
    GPT로부터 받은 JSON 데이터를 완벽한 기안문 텍스트로 변환합니다.
    
    Args:
        data (Dict[str, Any]): GPT가 생성한 JSON 데이터
    
    Returns:
        str: 완성된 기안문 텍스트
    """
    
    def get_item_number(level: int, index: int) -> str:
        """레벨과 인덱스에 따른 항목 번호를 반환합니다."""
        numbering_systems = [
            lambda i: f"{i+1}.",      # Level 0: 1., 2., 3., ...
            lambda i: f"{chr(ord('가') + i)}.",  # Level 1: 가., 나., 다., ...
            lambda i: f"{i+1})",      # Level 2: 1), 2), 3), ...
            lambda i: f"{chr(ord('가') + i)})",  # Level 3: 가), 나), 다), ...
            lambda i: f"({i+1})",     # Level 4: (1), (2), (3), ...
            lambda i: f"({chr(ord('가') + i)})"  # Level 5: (가), (나), (다), ...
        ]
        
        if level < len(numbering_systems):
            return numbering_systems[level](index)
        else:
            # 레벨이 너무 깊으면 기본 번호 체계 사용
            return f"{index+1}."
    
    def render_items(items: List[Dict], level: int = 0, indent: str = "") -> str:
        """재귀적으로 항목들을 렌더링합니다."""
        result = []
        
        for i, item in enumerate(items):
            # 항목 번호 생성
            number = get_item_number(level, i)
            
            # 현재 항목의 내용
            content = item.get('content', '')
            
            # 첫 번째 줄: 들여쓰기 + 번호 + 내용
            first_line = f"{indent}{number} {content}"
            
            # 내용이 여러 줄인 경우 처리
            lines = first_line.split('\n')
            formatted_lines = [lines[0]]  # 첫 줄
            
            # 두 번째 줄부터는 번호 + 공백만큼 들여쓰기
            if len(lines) > 1:
                continuation_indent = indent + " " * (len(number) + 1)
                for line in lines[1:]:
                    formatted_lines.append(continuation_indent + line)
            
            result.append('\n'.join(formatted_lines))
            
            # 하위 항목이 있는 경우 재귀 호출
            sub_items = item.get('sub_items', [])
            if sub_items:
                sub_indent = indent + "  "  # 2칸 들여쓰기 추가
                sub_result = render_items(sub_items, level + 1, sub_indent)
                if sub_result:
                    result.append(sub_result)
        
        return '\n'.join(result)
    
    # 기안문 구성 요소들 추출
    related_basis = data.get('related_basis', [])
    introduction = data.get('introduction', '')
    items = data.get('items', [])
    attachments = data.get('attachments', [])
    
    # 최종 텍스트 구성
    result_parts = []
    
    # 관련 근거가 있는 경우
    if related_basis:
        for i, basis in enumerate(related_basis):
            result_parts.append(f"  {i+1}. {basis}")
        result_parts.append("")  # 빈 줄 추가
    
    # 서론 부분
    if introduction:
        result_parts.append(introduction)
        result_parts.append("")  # 빈 줄 추가
    
    # 본문 항목들
    if items:
        items_text = render_items(items)
        result_parts.append(items_text)
    
    # 첨부 파일 처리
    if attachments:
        result_parts.append("")  # 빈 줄 추가
        result_parts.append("붙임")
        
        # 첨부파일 개수에 따른 최대 자릿수 계산
        max_digits = len(str(len(attachments)))
        
        for i, attachment in enumerate(attachments):
            # 번호를 오른쪽 정렬하여 세로줄 맞춤
            number = str(i + 1).rjust(max_digits)
            result_parts.append(f"  {number}. {attachment}")
        
        # 마지막에 "끝." 추가 (첨부파일이 있는 경우)
        result_parts[-1] += "  끝."
    else:
        # 첨부파일이 없는 경우
        result_parts.append("")  # 빈 줄 추가
        result_parts.append("끝.")
    
    return '\n'.join(result_parts)


def call_openai_api(prompt: str, api_key: str) -> Dict[str, Any]:
    """
    OpenAI API를 호출하여 기안문 JSON을 생성합니다.
    
    Args:
        prompt (str): GPT에 전달할 프롬프트
        api_key (str): OpenAI API 키
    
    Returns:
        Dict[str, Any]: GPT가 생성한 JSON 데이터
    """
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 한국의 공문서 작성 전문가입니다. 요청받은 형식에 맞춰 정확한 JSON만 출력하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # JSON 파싱
        json_text = response.choices[0].message.content.strip()
        
        # JSON 텍스트에서 코드 블록 마커 제거 (```json ... ``` 형태로 올 수 있음)
        if json_text.startswith("```"):
            lines = json_text.split('\n')
            json_text = '\n'.join(lines[1:-1])
        
        return json.loads(json_text)
        
    except json.JSONDecodeError as e:
        st.error(f"GPT 응답을 JSON으로 파싱하는데 실패했습니다: {e}")
        st.write("GPT 응답:", response.choices[0].message.content)
        return None
    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return None


# Streamlit 앱 예시
def main():
    st.title("🏛️ 기안문 작성 도우미")
    st.markdown("GPT를 활용한 정확한 형식의 기안문 자동 생성")
    st.markdown("---")
    
    # OpenAI API 키 입력
    api_key = st.text_input("OpenAI API Key", type="password", 
                           help="OpenAI API 키를 입력하세요")
    
    if not api_key:
        st.warning("OpenAI API 키를 입력해주세요.")
        return
    
    # 사용자 입력 폼
    with st.form("giamun_form"):
        st.subheader("📝 기안 정보 입력")
        
        col1, col2 = st.columns(2)
        
        with col1:
            giamun_type = st.selectbox(
                "기안 종류",
                ["보고서", "건의서", "계획서", "승인요청서", "협조요청서", "기타"],
                help="작성할 기안문의 종류를 선택하세요"
            )
        
        with col2:
            title = st.text_input(
                "제목",
                placeholder="예: 2024년 하반기 업무계획 수립 건",
                help="기안문의 제목을 입력하세요"
            )
        
        details = st.text_area(
            "주요 내용",
            height=200,
            placeholder="기안하고자 하는 내용을 자세히 입력하세요.\n- 배경 및 목적\n- 주요 내용\n- 기대 효과 등",
            help="기안문에 포함될 주요 내용을 입력하세요"
        )
        
        attachments = st.text_area(
            "첨부 파일",
            height=100,
            placeholder="첨부파일명을 한 줄씩 또는 쉼표로 구분하여 입력하세요\n예:\n사업계획서.pdf\n예산안.xlsx\n또는: 사업계획서.pdf, 예산안.xlsx",
            help="첨부할 파일명을 입력하세요 (한 줄씩 또는 쉼표로 구분)"
        )
        
        submitted = st.form_submit_button("🚀 기안문 생성", use_container_width=True)
    
    if submitted:
        if not title or not details:
            st.error("제목과 주요 내용은 필수 입력 항목입니다.")
            return
        
        # 사용자 입력 데이터 구성
        user_input = {
            'type': giamun_type,
            'title': title,
            'details': details,
            'attachments': attachments
        }
        
        # 프로그레스 바
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1단계: 프롬프트 생성
            status_text.text("1/3 GPT 프롬프트 생성 중...")
            progress_bar.progress(33)
            
            prompt = create_giamun_prompt_for_gpt(user_input)
            
            # 2단계: GPT API 호출
            status_text.text("2/3 GPT API 호출 중...")
            progress_bar.progress(66)
            
            json_data = call_openai_api(prompt, api_key)
            
            if json_data is None:
                return
            
            # 3단계: 최종 텍스트 생성
            status_text.text("3/3 기안문 텍스트 생성 중...")
            progress_bar.progress(100)
            
            final_giamun = render_giamun_from_json(json_data)
            
            # 진행률 표시 제거
            progress_bar.empty()
            status_text.empty()
            
            # 결과 표시
            st.success("✅ 기안문이 성공적으로 생성되었습니다!")
            
            # 탭으로 결과 구성
            tab1, tab2, tab3 = st.tabs(["📋 최종 기안문", "🔧 JSON 구조", "💡 생성된 프롬프트"])
            
            with tab1:
                st.subheader("생성된 기안문")
                st.code(final_giamun, language="text")
                
                # 다운로드 버튼
                st.download_button(
                    label="📥 기안문 다운로드 (.txt)",
                    data=final_giamun,
                    file_name=f"기안문_{title[:20]}.txt",
                    mime="text/plain"
                )
            
            with tab2:
                st.subheader("GPT가 생성한 JSON 구조")
                st.json(json_data)
            
            with tab3:
                st.subheader("GPT에 전달된 프롬프트")
                st.code(prompt, language="text")
        
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()