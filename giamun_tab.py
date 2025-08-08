"""
기안문 작성 탭
"""
import streamlit as st
from utils import run_chain_and_display

def draw_giamun_tab(prompts):
    """기안문 작성 탭 UI"""
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
                    }, st, prompts)
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
                    }, st, prompts)
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
                    }, st, prompts)
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
                    }, st, prompts)
                else: st.warning("활동명과 활동 개요를 입력해주세요.")