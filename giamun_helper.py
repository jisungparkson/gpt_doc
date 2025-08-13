"""
기안문 작성 헬퍼 함수들 - 사용자 제공 JSON 예시 기반 전면 재설계 버전
완벽한 JSON 구조화와 스마트 렌더링으로 모든 기안문 유형 지원
"""
import openai
import json
from typing import Dict, List, Any
from utils import PRIMARY_MODEL

# 1. 사용자가 제공한 JSON 데이터를 Python 딕셔너리로 내장
EXAMPLES_DATA = {
    "gianmunExamples": [
        {
            "id": 1,
            "type": "내부결재: 각종 계획 수립",
            "description": "현장체험학습, 운동회 등 어떤 활동을 시작하기 전, 그 개요와 예산 등을 명시하여 학교장(내부)의 승인을 받을 때 사용합니다.",
            "example": {
                "title": "2025학년도 5학년 현장체험학습 실시 계획(안)",
                "body": "1. 관련: 2025학년도 학교교육계획\n2. 학생들의 과학적 사고 및 탐구 능력을 기르고자 현장체험학습을 다음과 같이 실시하고자 합니다.\n    가. 일시: 2025. 10. 15.(수) 09:00~16:00\n    나. 장소: 국립광주과학관\n    다. 대상: 5학년 학생 120명\n    라. 소요예산: 금1,200,000원(교통비, 입장료)",
                "attachments": [
                    "1. 세부계획서 1부.  끝."
                ]
            }
        },
        {
            "id": 2,
            "type": "내부결재: 예산 집행(품의)",
            "description": "물품 구입, 공사비, 용역비 등 학교 예산을 집행(지출)하기 전에 결재자의 승인을 받는 문서입니다.",
            "example": {
                "title": "2025학년도 교실용 프린터 구입 품의",
                "body": "1. 관련: 2025학년도 학교회계 예산서\n2. 노후 프린터 교체를 통해 원활한 교육활동을 지원하고자, 다음과 같이 교실용 프린터를 구입하고자 품의합니다.\n    가. 품명 및 수량: 컬러 레이저 프린터 5대\n    나. 소요 예산: 금1,000,000원(금일백만원)\n    다. 예산 과목: 자산취득비, 비품구매",
                "attachments": [
                    "1. 비교 견적서(3개 업체) 각 1부.  끝."
                ]
            }
        },
        {
            "id": 3,
            "type": "결과 보고서",
            "description": "계획했던 활동이 모두 끝난 후, 그 결과를 정리하여 보고할 때 사용합니다.",
            "example": {
                "title": "2025학년도 5학년 현장체험학습 결과 보고",
                "body": "1. 관련: 2025학년도 5학년 현장체험학습 실시 계획(안)\n2. 위 호와 관련하여 현장체험학습 실시 결과를 다음과 같이 보고합니다.\n    가. 활동 개요\n        1) 일시: 2025. 10. 15.(수) 09:00~16:00\n        2) 장소: 국립광주과학관\n        3) 참여: 5학년 학생 120명, 교사 8명\n    나. 예산 정산 결과\n        1) 총 예산액: 1,200,000원\n        2) 지출액: 1,185,000원\n        3) 잔액: 15,000원\n    다. 종합 평가: 참여 학생 만족도 95%, 교육목표 달성도 우수",
                "attachments": [
                    "1. 예산 집행 증빙서류 1부.",
                    "2. 활동 사진 자료 1부.  끝."
                ]
            }
        },
        {
            "id": 4,
            "type": "대외발송: 자료 제출",
            "description": "교육지원청, 교육청, 교육부 등 외부 기관에서 요청한 자료를 제출할 때 사용합니다.",
            "example": {
                "receiver": "OO교육지원청교육장(참조: 민주시민교육과장)",
                "title": "2025학년도 학교폭력 실태조사 결과 제출",
                "body": "1. 관련: 민주시민교육과-5678(2025.XX.XX.)\n2. 위 호와 관련하여, 2025학년도 학교폭력 실태조사 결과를 붙임과 같이 제출합니다.",
                "attachments": [
                    "1. 2025학년도 학교폭력 실태조사 결과서 1부.  끝."
                ],
                "sender": "OO중학교장"
            }
        }
    ]
}


def create_giamun_prompt_for_gpt(user_input: Dict[str, str]) -> str:
    """
    사용자가 선택한 기안 유형에 맞는 '완벽한 예시'를 프롬프트에 동적으로 포함시켜
    GPT가 따라 하도록 만드는 마스터 프롬프트 생성 함수.
    """
    giamun_type = user_input.get('giamun_type', '')
    title = user_input.get('title', '')
    details = user_input.get('details', '')
    related_basis = user_input.get('related_basis', '')
    attachments = user_input.get('attachments', '')
    
    # 선택된 유형에 맞는 예시를 찾음
    selected_example = None
    for ex in EXAMPLES_DATA["gianmunExamples"]:
        if ex["type"] == giamun_type:
            selected_example = ex
            break
    
    # 기본값 설정
    if not selected_example:
        selected_example = EXAMPLES_DATA["gianmunExamples"][0]
    
    # 예시를 문자열로 변환하여 프롬프트에 삽입
    example_json = json.dumps(selected_example['example'], ensure_ascii=False, indent=2)
    
    prompt = f"""
# MISSION
당신은 대한민국 교육행정 공문서 작성 규정을 완벽하게 마스터한 AI 사무관입니다. 당신의 유일한 임무는 사용자의 요청을 바탕으로, **아래에 제시된 완벽한 예시와 동일한 구조**를 가진 **JSON 데이터**를 생성하는 것입니다.

# PERFECT EXAMPLE FOR "{giamun_type}"
**설명:** {selected_example['description']}

**완벽한 JSON 구조 예시:**
```json
{example_json}
```

# FORMATTING RULES
1. **JSON 필드 구조**: 위 예시와 동일한 필드명과 구조를 정확히 사용하세요.
2. **body 필드**: 본문 내용은 "1. 관련:" 으로 시작하고, "2. 위 호와 관련하여..." 로 이어지는 형식을 반드시 지켜주세요.
3. **들여쓰기**: 가., 나., 다. 항목은 4칸 공백으로 들여쓰기하고, 하위 항목은 8칸 공백을 사용하세요.
4. **대외발송**: 수신자가 있는 경우 "receiver"와 "sender" 필드를 포함하세요.

# CRITICAL ATTACHMENT RULES
- **첨부파일 있음**: "attachments" 배열에 파일명을 넣고, 마지막 항목에 "  끝." 추가
- **첨부파일 없음**: "attachments" 키를 빈 배열 []로 설정 (Python 렌더링에서 "붙임" 헤더를 아예 출력하지 않음)
- **긴 파일명**: 한 줄에 너무 길어도 하나의 항목으로 유지 (Python에서 내어쓰기 처리)

# USER'S CURRENT REQUEST
- **기안 종류:** {giamun_type}
- **제목:** {title}
- **주요 내용:** {details}
- **관련 근거:** {related_basis}
- **첨부 파일:** {attachments}

# OUTPUT FORMAT
위의 완벽한 예시를 참고하여, 사용자 요청에 맞는 JSON 데이터만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.
"""
    
    return prompt


def call_openai_api_for_json(prompt: str, api_key: str) -> Dict[str, Any]:
    """
    OpenAI API를 호출하여 기안문 JSON 데이터를 생성합니다.
    """
    import traceback
    import sys
    
    print(f"[DEBUG] API 호출 시작...")
    print(f"[DEBUG] API 키 길이: {len(api_key) if api_key else 0}")
    print(f"[DEBUG] 프롬프트 길이: {len(prompt)}")
    
    try:
        # OpenAI 클라이언트 초기화
        print(f"[DEBUG] OpenAI 클라이언트 초기화 중...")
        client = openai.OpenAI(api_key=api_key)
        
        print(f"[DEBUG] API 요청 전송 중...")
        # PRIMARY_MODEL을 사용하여 프로젝트 전체 모델 통일
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "당신은 한국의 공문서 작성 전문가입니다. 요청받은 형식에 맞춰 정확한 JSON만 출력하세요."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"}  # JSON 형식 강제
        )
        
        print(f"[DEBUG] API 응답 수신 완료")
        
        # 응답 텍스트 추출 및 정리
        response_text = response.choices[0].message.content.strip()
        print(f"[DEBUG] 응답 텍스트 길이: {len(response_text)}")
        print(f"[DEBUG] 응답 텍스트 앞 100자: {response_text[:100]}...")
        
        # JSON 파싱
        print(f"[DEBUG] JSON 파싱 시도 중...")
        json_data = json.loads(response_text)
        print(f"[DEBUG] JSON 파싱 성공! 키 개수: {len(json_data.keys()) if isinstance(json_data, dict) else 'N/A'}")
        
        return json_data
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 파싱 오류: {e}")
        print(f"[ERROR] 응답 텍스트: {response_text if 'response_text' in locals() else '응답 텍스트 없음'}")
        return None
        
    except openai.AuthenticationError as e:
        print(f"[ERROR] 인증 오류 - API 키가 잘못되었거나 유효하지 않습니다: {e}")
        return None
        
    except openai.PermissionDeniedError as e:
        print(f"[ERROR] 권한 거부 오류 - API 키가 해당 모델에 접근 권한이 없습니다: {e}")
        return None
        
    except openai.RateLimitError as e:
        print(f"[ERROR] 요청 한도 초과 오류: {e}")
        return None
        
    except openai.APIConnectionError as e:
        print(f"[ERROR] API 연결 오류 - 네트워크 문제일 수 있습니다: {e}")
        return None
        
    except openai.APITimeoutError as e:
        print(f"[ERROR] API 시간 초과 오류: {e}")
        return None
        
    except Exception as e:
        print(f"[ERROR] 예기치 않은 오류가 발생했습니다: {e}")
        print(f"[ERROR] 오류 타입: {type(e).__name__}")
        print(f"[ERROR] 상세 스택 트레이스:")
        print(traceback.format_exc())
        return None


def render_giamun_from_json(data: Dict[str, Any]) -> str:
    """
    모든 유형의 기안문 JSON을 받아, 완벽한 최종 문서를 텍스트 형태로 렌더링하는 스마트 함수
    사용자가 제공한 모든 '붙임' 규칙을 100% 완벽하게 준수
    """
    if not data:
        return "기안문 생성에 실패했습니다."
    
    try:
        parts = []
        
        # 1. 수신자 (대외발송용만)
        if "receiver" in data and data["receiver"]:
            parts.append(f"수신자  {data['receiver']}")
        
        # 2. 제목
        if "title" in data and data["title"]:
            parts.append(f"제목    {data['title']}")
            parts.append("")  # 빈 줄
        
        # 3. 본문
        if "body" in data and data["body"]:
            # 본문의 줄바꿈을 그대로 유지
            body_lines = data["body"].split('\n')
            parts.extend(body_lines)
            parts.append("")  # 빈 줄
        
        # 4. 붙임 (사용자 제공 상세 규칙 100% 준수)
        if "attachments" in data and data["attachments"]:
            cleaned_attachments = [att.strip() for att in data["attachments"] if att.strip()]
            
            if cleaned_attachments:
                # 가장 긴 번호의 자릿수를 계산 (정렬용)
                max_digits = len(str(len(cleaned_attachments)))
                
                # [규칙 1 준수] '붙임' 헤더 추가 (첨부파일이 있을 때만)
                parts.append("붙임")
                
                for i, attachment in enumerate(cleaned_attachments):
                    # 번호를 오른쪽 정렬하고 '.'을 붙임
                    number_str = f"{str(i + 1).rjust(max_digits)}."
                    
                    # [규칙 2 준수] 긴 파일명 내어쓰기 처리
                    # 첫 줄: '공백 2칸' + 정렬된 번호 + ' ' + 내용
                    first_line = f"  {number_str} {attachment}"
                    
                    # 터미널 너비를 80자로 가정하여 줄바꿈 처리 (근사치)
                    max_line_width = 78  # 여유분 2자
                    
                    if len(first_line) <= max_line_width:
                        # 한 줄에 들어가는 경우
                        parts.append(first_line)
                    else:
                        # [규칙 2] 줄바꿈이 필요한 경우 - 내어쓰기 적용
                        # 내어쓰기 공백 = '  ' + 번호 + ' '의 길이만큼
                        indent_space = " " * (2 + len(number_str) + 1)
                        
                        # 첫 줄에서 들어갈 수 있는 문자 수 계산
                        first_line_prefix = f"  {number_str} "
                        available_width = max_line_width - len(first_line_prefix)
                        
                        if available_width > 10:  # 최소 10자는 들어가야 의미있음
                            # 첫 줄
                            first_part = attachment[:available_width]
                            parts.append(f"  {number_str} {first_part}")
                            
                            # 나머지 줄들 (내어쓰기 적용)
                            remaining = attachment[available_width:]
                            while remaining:
                                remaining_width = max_line_width - len(indent_space)
                                if len(remaining) <= remaining_width:
                                    parts.append(f"{indent_space}{remaining}")
                                    break
                                else:
                                    parts.append(f"{indent_space}{remaining[:remaining_width]}")
                                    remaining = remaining[remaining_width:]
                        else:
                            # 번호가 너무 길어서 내어쓰기가 불가능한 경우 - 그냥 출력
                            parts.append(first_line)
            else:
                # [규칙 1 준수] 빈 배열이지만 attachments 키가 있는 경우 - "붙임" 헤더 없음
                pass
        else:
            # [규칙 1 준수] attachments 키가 아예 없거나 None인 경우 - "붙임" 헤더 없음, "끝." 추가
            if parts and not parts[-1].strip().endswith("끝."):
                parts.append("")
                parts.append("끝.")
        
        # 5. 발신자 (대외발송용만)
        if "sender" in data and data["sender"]:
            parts.append("")
            parts.append("")
            parts.append(data["sender"])
        
        # 최종 텍스트 조립
        final_text = "\n".join(parts)
        
        return final_text
        
    except Exception as e:
        return f"기안문 렌더링 중 오류가 발생했습니다: {str(e)}"


# 호환성을 위한 기존 함수명 유지
def call_openai_api_for_text(prompt: str, api_key: str) -> str:
    """
    JSON 방식으로 변경된 새로운 워크플로우에서 최종 텍스트를 반환하는 함수
    """
    # 1. JSON 데이터 생성
    json_data = call_openai_api_for_json(prompt, api_key)
    
    if json_data:
        # 2. JSON을 텍스트로 렌더링
        return render_giamun_from_json(json_data)
    else:
        return None