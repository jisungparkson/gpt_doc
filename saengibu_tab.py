"""
생기부 기록 탭 - UI 깨짐 현상을 완전히 해결한 최종 안정화 버전
"""
import streamlit as st
import streamlit.components.v1 as components
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import pandas as pd
from io import BytesIO
import json
from utils import PRIMARY_MODEL

# --- 헬퍼 함수: 데이터프레임을 엑셀 파일(bytes)로 변환 ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def draw_saengibu_tab(prompts):
    """생기부 기록 탭 UI (모든 기능이 포함된 최종 안정화 버전)"""
    st.header("📖 생기부 기록 도우미")
    st.markdown("학생의 활동을 구체적으로 입력할수록, 학생의 역량과 성장이 돋보이는 좋은 결과물이 나옵니다.")
    
    record_tab1, record_tab2 = st.tabs(["📚 교과평어 (교과세특)", "🌱 행발 (행동발달상황)"])
    
    # --- 교과평어 서브탭 ---
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
                    "창의적 사고역량", "비판적 사고역량", "문제해결역량",
                    "의사소통역량", "협업역량", "정보활용역량", "자기관리역량",
                    "시민의식", "국제사회문화이해", "융합적 사고력", "탐구역량",
                    "추론역량", "정보처리역량", "의사결정역량"
                ]
                competency_selected = st.multiselect("핵심 역량 키워드 (선택사항)", competency_options, key="competency_multiselect")
                competency = ", ".join(competency_selected) if competency_selected else ""
        
        # [엑셀 업로드/다운로드 UI]
        with st.container(border=True):
            st.subheader("👥 학생 명단 설정")
            
            # 엑셀 양식 다운로드
            sample_df = pd.DataFrame({
                "번호": [1, 2, 3, 4, 5],
                "이름": ["김교육", "이사랑", "박희망", "최성장", "정발전"]
            })
            st.download_button(
                label="📥 엑셀 양식 다운로드",
                data=to_excel(sample_df),
                file_name="학생_명단_양식.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True,
                key="download_seutuk_template"
            )
            
            # 엑셀 파일 업로드
            uploaded_file = st.file_uploader(
                label="📂 학생 명단 엑셀 파일을 여기에 끌어다 놓거나, 클릭하여 업로드하세요.",
                type=['xlsx'], 
                key="seutuk_uploader",
                help="엑셀 파일에 '이름' 컬럼이 있어야 합니다."
            )
            
            # 학생 수 설정 (업로드가 없으면 수동 입력)
            if uploaded_file:
                try:
                    df = pd.read_excel(uploaded_file)
                    if '이름' in df.columns:
                        student_names = df['이름'].dropna().astype(str).tolist()
                        num_students = len(student_names)
                        # 세션 상태에 업로드된 학생 데이터 저장
                        st.session_state.student_data = [
                            {"name": name, "observation": "", "achievement": ""} 
                            for name in student_names
                        ]
                        st.success(f"✅ {num_students}명의 학생 명단을 불러왔습니다.")
                    else:
                        st.error("❌ 엑셀 파일에 '이름' 컬럼이 없습니다.")
                        num_students = st.number_input("학생 수", min_value=1, max_value=40, value=5)
                except Exception as e:
                    st.error(f"❌ 파일 처리 중 오류: {e}")
                    num_students = st.number_input("학생 수", min_value=1, max_value=40, value=5)
            else:
                num_students = st.number_input("학생 수", min_value=1, max_value=40, value=5)
                
        # 학생 정보 입력 표
        if subject:
            with st.container(border=True):
                st.subheader(f"📄 {subject} 교과세특 생성")
                
                # 세션 상태에 학생 데이터 초기화 (업로드가 없었던 경우만)
                if 'student_data' not in st.session_state or (not uploaded_file and len(st.session_state.student_data) != num_students):
                    st.session_state.student_data = [
                        {"name": f"학생{i+1}", "observation": "", "achievement": ""} 
                        for i in range(num_students)
                    ]
                
                # 표 헤더
                header_cols = st.columns([1, 2, 4, 3, 1.5])
                with header_cols[0]:
                    st.markdown("**번호**")
                with header_cols[1]:
                    st.markdown("**이름**")
                with header_cols[2]:
                    st.markdown("**학습 내용 (관찰 내용)**")
                with header_cols[3]:
                    st.markdown("**성취기준(선택)**")
                with header_cols[4]:
                    st.markdown("**개별 생성**")
                
                st.divider()
                
                # 학생 데이터 입력 행
                for i in range(len(st.session_state.student_data)):
                    cols = st.columns([1, 2, 4, 3, 1.5])
                    
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
                            placeholder="성취기준을 입력해주세요. (선택사항)",
                            height=100,
                            key=f"ach_{i}"
                        )
                    
                    # '개별 생성' 버튼을 마지막 컬럼에 추가
                    with cols[4]:
                        # 버튼을 컬럼 중앙에 위치시키기 위한 트릭
                        st.write("")
                        st.write("")
                        if st.button("✨ 개별 생성", key=f"generate_single_{i}", use_container_width=True):
                            student_data = st.session_state.student_data[i]
                            if student_data["observation"].strip():
                                with st.spinner(f"{student_data['name']} 교과세특 생성 중..."):
                                    try:
                                        # LLM 호출 로직 (기존 '전체 생성' 로직과 동일)
                                        llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
                                        prompt = prompts["student_record"]
                                        chain = prompt | llm | StrOutputParser()
                                        result = chain.invoke({
                                            "subject": subject,
                                            "competency": competency,
                                            "observation": student_data["observation"],
                                            "achievement": student_data["achievement"]
                                        })

                                        # 결과 리스트가 없으면 먼저 생성
                                        if 'generated_table_results' not in st.session_state or len(st.session_state.generated_table_results) != len(st.session_state.student_data):
                                            st.session_state.generated_table_results = [
                                                {"original_number": j + 1, "name": st.session_state.student_data[j]["name"], "result": ""} for j in range(len(st.session_state.student_data))
                                            ]
                                        
                                        # 해당 학생의 결과만 업데이트
                                        st.session_state.generated_table_results[i] = {
                                            "original_number": i + 1,
                                            "name": student_data["name"],
                                            "result": result
                                        }
                                        st.success(f"{student_data['name']} 생성 완료!")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"생성 실패: {e}")
                            else:
                                st.warning("관찰 내용을 먼저 입력해주세요.")
                    
                    if i < len(st.session_state.student_data) - 1:
                        st.markdown("---")

                st.divider()
                
                # [빈 학생 처리 기능이 포함된 생성 로직]
                col_generate = st.columns([3, 1])
                with col_generate[1]:
                    if st.button("✨ 전체 생성", use_container_width=True, key="generate_all"):
                        st.session_state.generated_table_results = []
                        
                        for i, data in enumerate(st.session_state.student_data):
                            if data["observation"].strip():  # 내용이 있을 때만 생성
                                with st.spinner(f"{data['name']} 교과세특 생성 중..."):
                                    try:
                                        llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
                                        prompt = prompts["student_record"]
                                        chain = prompt | llm | StrOutputParser()
                                        
                                        result = chain.invoke({
                                            "subject": subject,
                                            "competency": competency,
                                            "observation": data["observation"],
                                            "achievement": data["achievement"]
                                        })
                                        
                                        st.session_state.generated_table_results.append({
                                            "original_number": i + 1,
                                            "name": data["name"],
                                            "result": result
                                        })
                                    except Exception as e:
                                        st.error(f"{data['name']} 교과세특 생성 실패: {e}")
                                        st.session_state.generated_table_results.append({
                                            "original_number": i + 1,
                                            "name": data["name"],
                                            "result": f"생성 실패: {e}"
                                        })
                            else:  # 내용이 없으면 빈 결과로 추가 (번호 유지)
                                st.session_state.generated_table_results.append({
                                    "original_number": i + 1,
                                    "name": data["name"],
                                    "result": ""  # 빈 문자열
                                })
                        
                        st.success("전체 학생 교과세특 생성 완료!")

        # [UI 깨짐 현상을 해결한 최종 결과 표시 코드]
        if 'generated_table_results' in st.session_state and st.session_state.generated_table_results:
            with st.container(border=True):
                st.subheader("📄 생성 결과")
                
                # 헤더 (NEIS 문구 제거)
                st.markdown(f"""
                <div style="background-color: #e8f4f8; padding: 8px 12px; border: 1px solid #ddd; border-bottom: none; display: flex; justify-content: flex-start; align-items: center; font-size: 14px;">
                    <span style="color: #0066cc; font-weight: bold;">{subject}</span>
                </div>
                """, unsafe_allow_html=True)

                # 엑셀 다운로드를 위한 데이터프레임 생성
                results_data = st.session_state.generated_table_results
                df_seutuk = pd.DataFrame({
                    "번호": [data["original_number"] for data in results_data],
                    "이름": [data["name"] for data in results_data],
                    "평어": [data["result"] for data in results_data]
                })

                # 결과 엑셀 다운로드 버튼
                st.download_button(
                    label="📥 결과 엑셀 파일 다운로드",
                    data=to_excel(df_seutuk),
                    file_name=f"{subject}_교과세특_결과.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
                
                # HTML 생성을 위한 데이터 준비
                results_for_html = []
                for item in results_data:
                    results_for_html.append({
                        "number": item["original_number"],
                        "name": item["name"],
                        "text": item["result"]
                    })

                # 데이터를 안전한 JSON 문자열로 변환
                json_data = json.dumps(results_for_html)

                # HTML/CSS/JS (안전한 데이터 전달 방식으로 수정)
                custom_table_html = f"""
                <!DOCTYPE html><html><head><meta charset="UTF-8">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; 
                        background: #f8fafc; 
                        padding: 10px; 
                        line-height: 1.4;
                    }}
                    .custom-table-container {{ 
                        background: white; 
                        border-radius: 8px; 
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); 
                        overflow: hidden; 
                        border: 1px solid #e2e8f0; 
                        width: 100%;
                        max-width: 100%;
                    }}
                    .custom-table {{ 
                        width: 100%; 
                        border-collapse: separate; 
                        border-spacing: 0; 
                        table-layout: fixed;
                    }}
                    .custom-table th {{ 
                        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); 
                        color: white; 
                        padding: 12px 8px; 
                        text-align: center; 
                        font-weight: 600; 
                        font-size: 13px; 
                        border: none;
                        white-space: nowrap;
                    }}
                    .custom-table th:nth-child(1), .custom-table td:nth-child(1) {{ width: 10%; }}
                    .custom-table th:nth-child(2), .custom-table td:nth-child(2) {{ width: 20%; }}
                    .custom-table th:nth-child(3), .custom-table td:nth-child(3) {{ width: 70%; }}
                    .custom-table td {{ 
                        padding: 0; 
                        border-bottom: 1px solid #e2e8f0; 
                        vertical-align: top; 
                        word-wrap: break-word;
                    }}
                    .number-cell, .name-cell {{
                        text-align: center; 
                        padding: 15px 8px; 
                        background: #f8fafc; 
                        font-weight: 600; 
                        vertical-align: middle;
                        white-space: nowrap;
                    }}
                    .text-cell {{ 
                        padding: 15px; 
                        position: relative; 
                        background: white; 
                        min-height: 80px;
                    }}
                    .text-content {{ 
                        line-height: 1.6; 
                        font-size: 13px; 
                        color: #374151; 
                        min-height: 40px; 
                        margin-bottom: 8px; 
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        hyphens: auto;
                    }}
                    .counter-info {{ 
                        text-align: right; 
                        color: #6b7280; 
                        font-size: 11px; 
                        margin: 8px 0;
                        font-style: italic;
                    }}
                    .button-group {{ 
                        display: flex; 
                        gap: 6px; 
                        justify-content: flex-end; 
                        margin-top: 10px; 
                    }}
                    .copy-btn, .edit-btn {{ 
                        background: none; 
                        border: 1px solid #d1d5db; 
                        padding: 4px 8px; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 11px; 
                        transition: all 0.2s ease; 
                        white-space: nowrap;
                    }}
                    .copy-btn {{ 
                        color: #2563eb; 
                        border-color: #2563eb; 
                    }}
                    .copy-btn:hover {{ 
                        background: #2563eb; 
                        color: white; 
                    }}
                    .edit-btn {{ 
                        color: #059669; 
                        border-color: #059669; 
                    }}
                    .edit-btn:hover {{ 
                        background: #059669; 
                        color: white; 
                    }}
                    .edit-textarea {{ 
                        width: 100%; 
                        min-height: 80px; 
                        padding: 10px; 
                        border: 2px solid #d1d5db; 
                        border-radius: 6px; 
                        font-size: 13px; 
                        font-family: inherit; 
                        line-height: 1.6; 
                        resize: vertical;
                        outline: none;
                    }}
                    .edit-textarea:focus {{
                        border-color: #2563eb;
                    }}
                    .save-btn, .cancel-btn {{ 
                        padding: 4px 10px; 
                        border: none; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 11px; 
                        margin-top: 6px; 
                        margin-right: 6px;
                    }}
                    .save-btn {{ 
                        background: #059669; 
                        color: white; 
                    }}
                    .save-btn:hover {{
                        background: #047857;
                    }}
                    .cancel-btn {{ 
                        background: #6b7280; 
                        color: white; 
                    }}
                    .cancel-btn:hover {{
                        background: #4b5563;
                    }}
                </style>
                </head><body>
                <div id="seutuk-table-container"></div>
                <script>
                    const data = {json_data};
                    const container = document.getElementById('seutuk-table-container');
                    
                    let tableHTML = `<div class="custom-table-container"><table class="custom-table">
                        <thead><tr><th>번호</th><th>이름</th><th>평어</th></tr></thead><tbody>`;

                    data.forEach((item, index) => {{
                        const charCount = item.text.length;
                        const byteCount = (new TextEncoder().encode(item.text)).length;
                        
                        tableHTML += `
                            <tr id="row-seutuk-${{index}}">
                                <td class="number-cell">${{item.number.toString().padStart(2, '0')}}</td>
                                <td class="name-cell">${{item.name}}</td>
                                <td class="text-cell">
                                    <div class="text-content">${{item.text.replace(/\\n/g, '<br>')}}</div>
                                    <div class="counter-info">${{charCount}}자 / ${{byteCount}}byte</div>
                                    <div class="button-group">
                                        <button class="copy-btn" onclick="copyText('seutuk', ${{index}})">복사</button>
                                        <button class="edit-btn" onclick="editText('seutuk', ${{index}})">수정</button>
                                    </div>
                                </td>
                            </tr>`;
                    }});

                    tableHTML += `</tbody></table></div>`;
                    container.innerHTML = tableHTML;

                    function copyText(prefix, index) {{
                        const text = data[index].text;
                        navigator.clipboard.writeText(text).then(() => showMessage('복사되었습니다!', 'success'));
                    }}

                    function editText(prefix, index) {{
                        const row = document.getElementById(`row-${{prefix}}-${{index}}`);
                        const cell = row.querySelector('.text-cell');
                        const currentText = data[index].text;

                        cell.innerHTML = `
                            <textarea class="edit-textarea">${{currentText}}</textarea>
                            <div class="button-group">
                                <button class="save-btn" onclick="saveEdit('${{prefix}}', ${{index}})">저장</button>
                                <button class="cancel-btn" onclick="cancelEdit('${{prefix}}', ${{index}})">취소</button>
                            </div>
                        `;
                        cell.querySelector('textarea').focus();
                    }}
                    
                    function saveEdit(prefix, index) {{
                        const row = document.getElementById(`row-${{prefix}}-${{index}}`);
                        const cell = row.querySelector('.text-cell');
                        const newText = cell.querySelector('textarea').value;

                        // Update data model
                        data[index].text = newText;

                        // Re-render the cell
                        cancelEdit(prefix, index); // cancelEdit re-renders from the current data model
                        showMessage('수정되었습니다!', 'success');
                    }}

                    function cancelEdit(prefix, index) {{
                        const row = document.getElementById(`row-${{prefix}}-${{index}}`);
                        const cell = row.querySelector('.text-cell');
                        const item = data[index];
                        const charCount = item.text.length;
                        const byteCount = (new TextEncoder().encode(item.text)).length;

                        cell.innerHTML = `
                            <div class="text-content">${{item.text.replace(/\\n/g, '<br>')}}</div>
                            <div class="counter-info">${{charCount}}자 / ${{byteCount}}byte</div>
                            <div class="button-group">
                                <button class="copy-btn" onclick="copyText('${{prefix}}', ${{index}})">복사</button>
                                <button class="edit-btn" onclick="editText('${{prefix}}', ${{index}})">수정</button>
                            </div>
                        `;
                    }}
                    
                    function showMessage(message, type) {{
                        const messageDiv = document.createElement('div');
                        messageDiv.textContent = message;
                        messageDiv.style.cssText = `
                            position: fixed;
                            top: 20px;
                            right: 20px;
                            background: ${{type === 'success' ? '#10b981' : '#ef4444'}};
                            color: white;
                            padding: 10px 16px;
                            border-radius: 6px;
                            font-weight: 600;
                            font-size: 13px;
                            z-index: 10000;
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                            animation: slideIn 0.3s ease-out;
                        `;
                        
                        const style = document.createElement('style');
                        style.textContent = `
                            @keyframes slideIn {{
                                from {{ transform: translateX(100%); opacity: 0; }}
                                to {{ transform: translateX(0); opacity: 1; }}
                            }}
                        `;
                        document.head.appendChild(style);
                        document.body.appendChild(messageDiv);
                        
                        setTimeout(() => {{
                            messageDiv.remove();
                            style.remove();
                        }}, 2500);
                    }}
                </script>
                </body></html>
                """
                
                # HTML 컴포넌트로 표시
                components.html(custom_table_html, height=600, scrolling=True)
        
        else:
            st.info("ℹ️ 과목을 먼저 입력해주세요.")
    
    # --- 행발 서브탭 (교과평어 탭과 동일한 구조로 복원) ---
    with record_tab2:
        st.markdown("여러 학생의 행발을 표 형태로 한 번에 생성할 수 있습니다.")
        
        # [엑셀 업로드/다운로드 UI]
        with st.container(border=True):
            st.subheader("👥 학생 명단 설정")
            
            # 엑셀 양식 다운로드
            sample_df_behavior = pd.DataFrame({
                "번호": [1, 2, 3, 4, 5],
                "이름": ["김교육", "이사랑", "박희망", "최성장", "정발전"]
            })
            st.download_button(
                label="📥 엑셀 양식 다운로드",
                data=to_excel(sample_df_behavior),
                file_name="학생_명단_양식_행발.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True,
                key="download_hangbal_template"
            )
            
            # 엑셀 파일 업로드
            uploaded_file_behavior = st.file_uploader(
                label="📂 학생 명단 엑셀 파일을 여기에 끌어다 놓거나, 클릭하여 업로드하세요.",
                type=['xlsx'], 
                key="hangbal_uploader",
                help="엑셀 파일에 '이름' 컬럼이 있어야 합니다."
            )
            
            # 학생 수 설정 (업로드가 없으면 수동 입력)
            if uploaded_file_behavior:
                try:
                    df_behavior = pd.read_excel(uploaded_file_behavior)
                    if '이름' in df_behavior.columns:
                        student_names_behavior = df_behavior['이름'].dropna().astype(str).tolist()
                        num_behavior_students = len(student_names_behavior)
                        # 세션 상태에 업로드된 학생 데이터 저장
                        st.session_state.behavior_student_data = [
                            {"name": name, "behavior_content": ""} 
                            for name in student_names_behavior
                        ]
                        st.success(f"✅ {num_behavior_students}명의 학생 명단을 불러왔습니다.")
                    else:
                        st.error("❌ 엑셀 파일에 '이름' 컬럼이 없습니다.")
                        num_behavior_students = st.number_input("학생 수", min_value=1, max_value=40, value=5, key="num_behavior_students_manual")
                except Exception as e:
                    st.error(f"❌ 파일 처리 중 오류: {e}")
                    num_behavior_students = st.number_input("학생 수", min_value=1, max_value=40, value=5, key="num_behavior_students_error")
            else:
                num_behavior_students = st.number_input("학생 수", min_value=1, max_value=40, value=5, key="num_behavior_students")
                
        # 학생 정보 입력 표
        with st.container(border=True):
            st.subheader("📄 행발 생성")
            
            # 세션 상태에 학생 데이터 초기화 (업로드가 없었던 경우만)
            if 'behavior_student_data' not in st.session_state or (not uploaded_file_behavior and len(st.session_state.behavior_student_data) != num_behavior_students):
                st.session_state.behavior_student_data = [
                    {"name": f"학생{i+1}", "behavior_content": ""} 
                    for i in range(num_behavior_students)
                ]
            
            # 표 헤더
            header_cols = st.columns([1, 2, 4, 1.5])
            with header_cols[0]:
                st.markdown("**번호**")
            with header_cols[1]:
                st.markdown("**이름**")
            with header_cols[2]:
                st.markdown("**행동 내용 (관찰된 행동 특성)**")
            with header_cols[3]:
                st.markdown("**개별생성**")
            
            st.divider()
            
            # 학생 데이터 입력 행
            for i in range(len(st.session_state.behavior_student_data)):
                cols = st.columns([1, 2, 4, 1.5])
                
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
                
                with cols[3]:
                    if st.button("✨ 개별 생성", key=f"generate_single_behavior_{i}"):
                        if st.session_state.behavior_student_data[i]["behavior_content"].strip():
                            with st.spinner(f"{st.session_state.behavior_student_data[i]['name']} 행발 생성 중..."):
                                try:
                                    llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
                                    prompt = prompts["behavior_record"]
                                    chain = prompt | llm | StrOutputParser()
                                    
                                    result = chain.invoke({
                                        "behavior_trait": "학생의 행동 특성 및 성장 모습",
                                        "observation": st.session_state.behavior_student_data[i]["behavior_content"],
                                        "growth_point": "학생의 개인적 성장과 발달 과정"
                                    })
                                    
                                    # 기존 결과가 있으면 업데이트, 없으면 새로 추가
                                    if 'generated_behavior_table_results' not in st.session_state:
                                        st.session_state.generated_behavior_table_results = []
                                    
                                    # 해당 학생의 기존 결과 찾아서 업데이트
                                    updated = False
                                    for j, existing_result in enumerate(st.session_state.generated_behavior_table_results):
                                        if existing_result["original_number"] == i + 1:
                                            st.session_state.generated_behavior_table_results[j] = {
                                                "original_number": i + 1,
                                                "name": st.session_state.behavior_student_data[i]["name"],
                                                "result": result
                                            }
                                            updated = True
                                            break
                                    
                                    # 기존 결과가 없으면 새로 추가
                                    if not updated:
                                        st.session_state.generated_behavior_table_results.append({
                                            "original_number": i + 1,
                                            "name": st.session_state.behavior_student_data[i]["name"],
                                            "result": result
                                        })
                                    
                                    st.success(f"{st.session_state.behavior_student_data[i]['name']} 행발 생성 완료!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"{st.session_state.behavior_student_data[i]['name']} 행발 생성 실패: {e}")
                        else:
                            st.warning("행동 내용을 입력해주세요.")
                
                if i < len(st.session_state.behavior_student_data) - 1:
                    st.markdown("---")
            
            st.divider()
            
            # [빈 학생 처리 기능이 포함된 생성 로직]
            col_generate = st.columns([3, 1])
            with col_generate[1]:
                if st.button("✨ 전체 생성", use_container_width=True, key="generate_all_behavior"):
                    st.session_state.generated_behavior_table_results = []
                    
                    for i, data in enumerate(st.session_state.behavior_student_data):
                        if data["behavior_content"].strip():  # 내용이 있을 때만 생성
                            with st.spinner(f"{data['name']} 행발 생성 중..."):
                                try:
                                    llm = ChatOpenAI(model=PRIMARY_MODEL, temperature=0.5)
                                    prompt = prompts["behavior_record"]
                                    chain = prompt | llm | StrOutputParser()
                                    
                                    result = chain.invoke({
                                        "behavior_trait": "학생의 행동 특성 및 성장 모습",
                                        "observation": data["behavior_content"],
                                        "growth_point": "학생의 개인적 성장과 발달 과정"
                                    })
                                    
                                    st.session_state.generated_behavior_table_results.append({
                                        "original_number": i + 1,
                                        "name": data["name"],
                                        "result": result
                                    })
                                except Exception as e:
                                    st.error(f"{data['name']} 행발 생성 실패: {e}")
                                    st.session_state.generated_behavior_table_results.append({
                                        "original_number": i + 1,
                                        "name": data["name"],
                                        "result": f"생성 실패: {e}"
                                    })
                        else:  # 내용이 없으면 빈 결과로 추가 (번호 유지)
                            st.session_state.generated_behavior_table_results.append({
                                "original_number": i + 1,
                                "name": data["name"],
                                "result": ""  # 빈 문자열
                            })
                            
                    st.success("전체 학생 행발 생성 완료!")

        # [행발 결과 표시 UI]
        if 'generated_behavior_table_results' in st.session_state and st.session_state.generated_behavior_table_results:
            with st.container(border=True):
                st.subheader("📄 생성 결과")
                
                # 헤더
                st.markdown("""
                <div style="background-color: #e8f4f8; padding: 8px 12px; border: 1px solid #ddd; border-bottom: none; display: flex; justify-content: flex-start; align-items: center; font-size: 14px;">
                    <span style="color: #0066cc; font-weight: bold;">행동발달상황</span>
                </div>
                """, unsafe_allow_html=True)

                # 엑셀 다운로드를 위한 데이터프레임 생성
                behavior_results_data = st.session_state.generated_behavior_table_results
                df_behavior = pd.DataFrame({
                    "번호": [data["original_number"] for data in behavior_results_data],
                    "이름": [data["name"] for data in behavior_results_data],
                    "행발내용": [data["result"] for data in behavior_results_data]
                })

                # 결과 엑셀 다운로드 버튼
                st.download_button(
                    label="📥 결과 엑셀 파일 다운로드",
                    data=to_excel(df_behavior),
                    file_name="행동발달상황_결과.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
                
                # HTML 생성을 위한 데이터 준비
                behavior_results_for_html = []
                for item in behavior_results_data:
                    behavior_results_for_html.append({
                        "number": item["original_number"],
                        "name": item["name"],
                        "text": item["result"]
                    })

                # 데이터를 안전한 JSON 문자열로 변환
                behavior_json_data = json.dumps(behavior_results_for_html)

                # 행발용 결과 테이블 (안전한 데이터 전달 방식으로 수정)
                behavior_table_html = f"""
                <!DOCTYPE html><html><head><meta charset="UTF-8">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; 
                        background: #f8fafc; 
                        padding: 10px; 
                        line-height: 1.4;
                    }}
                    .behavior-table-container {{ 
                        background: white; 
                        border-radius: 8px; 
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); 
                        overflow: hidden; 
                        border: 1px solid #e2e8f0; 
                        width: 100%;
                        max-width: 100%;
                    }}
                    .behavior-table {{ 
                        width: 100%; 
                        border-collapse: separate; 
                        border-spacing: 0; 
                        table-layout: fixed;
                    }}
                    .behavior-table th {{ 
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                        color: white; 
                        padding: 12px 8px; 
                        text-align: center; 
                        font-weight: 600; 
                        font-size: 13px; 
                        border: none;
                        white-space: nowrap;
                    }}
                    .behavior-table th:nth-child(1), .behavior-table td:nth-child(1) {{ width: 10%; }}
                    .behavior-table th:nth-child(2), .behavior-table td:nth-child(2) {{ width: 20%; }}
                    .behavior-table th:nth-child(3), .behavior-table td:nth-child(3) {{ width: 70%; }}
                    .behavior-table td {{ 
                        padding: 0; 
                        border-bottom: 1px solid #e2e8f0; 
                        vertical-align: top; 
                        word-wrap: break-word;
                    }}
                    .number-cell, .name-cell {{
                        text-align: center; 
                        padding: 15px 8px; 
                        background: #f0fdf4; 
                        font-weight: 600; 
                        vertical-align: middle;
                        white-space: nowrap;
                    }}
                    .text-cell {{ 
                        padding: 15px; 
                        position: relative; 
                        background: white; 
                        min-height: 80px;
                    }}
                    .text-content {{ 
                        line-height: 1.6; 
                        font-size: 13px; 
                        color: #374151; 
                        min-height: 40px; 
                        margin-bottom: 8px; 
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        hyphens: auto;
                    }}
                    .counter-info {{ 
                        text-align: right; 
                        color: #6b7280; 
                        font-size: 11px; 
                        margin: 8px 0;
                        font-style: italic;
                    }}
                    .button-group {{ 
                        display: flex; 
                        gap: 6px; 
                        justify-content: flex-end; 
                        margin-top: 10px; 
                    }}
                    .copy-btn, .edit-btn {{ 
                        background: none; 
                        border: 1px solid #d1d5db; 
                        padding: 4px 8px; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 11px; 
                        transition: all 0.2s ease; 
                        white-space: nowrap;
                    }}
                    .copy-btn {{ 
                        color: #2563eb; 
                        border-color: #2563eb; 
                    }}
                    .copy-btn:hover {{ 
                        background: #2563eb; 
                        color: white; 
                    }}
                    .edit-btn {{ 
                        color: #10b981; 
                        border-color: #10b981; 
                    }}
                    .edit-btn:hover {{ 
                        background: #10b981; 
                        color: white; 
                    }}
                    .edit-textarea {{ 
                        width: 100%; 
                        min-height: 80px; 
                        padding: 10px; 
                        border: 2px solid #d1d5db; 
                        border-radius: 6px; 
                        font-size: 13px; 
                        font-family: inherit; 
                        line-height: 1.6; 
                        resize: vertical;
                        outline: none;
                    }}
                    .edit-textarea:focus {{
                        border-color: #10b981;
                    }}
                    .save-btn, .cancel-btn {{ 
                        padding: 4px 10px; 
                        border: none; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 11px; 
                        margin-top: 6px; 
                        margin-right: 6px;
                    }}
                    .save-btn {{ 
                        background: #10b981; 
                        color: white; 
                    }}
                    .save-btn:hover {{
                        background: #059669;
                    }}
                    .cancel-btn {{ 
                        background: #6b7280; 
                        color: white; 
                    }}
                    .cancel-btn:hover {{
                        background: #4b5563;
                    }}
                </style>
                </head><body>
                <div id="behavior-table-container"></div>
                <script>
                    const behaviorData = {behavior_json_data};
                    const behaviorContainer = document.getElementById('behavior-table-container');
                    
                    let behaviorTableHTML = `<div class="behavior-table-container"><table class="behavior-table">
                        <thead><tr><th>번호</th><th>이름</th><th>행발 내용</th></tr></thead><tbody>`;

                    behaviorData.forEach((item, index) => {{
                        const charCount = item.text.length;
                        const byteCount = (new TextEncoder().encode(item.text)).length;
                        
                        behaviorTableHTML += `
                            <tr id="row-behavior-${{index}}">
                                <td class="number-cell">${{item.number.toString().padStart(2, '0')}}</td>
                                <td class="name-cell">${{item.name}}</td>
                                <td class="text-cell">
                                    <div class="text-content">${{item.text.replace(/\\n/g, '<br>')}}</div>
                                    <div class="counter-info">${{charCount}}자 / ${{byteCount}}byte</div>
                                    <div class="button-group">
                                        <button class="copy-btn" onclick="copyBehaviorText('behavior', ${{index}})">복사</button>
                                        <button class="edit-btn" onclick="editBehaviorText('behavior', ${{index}})">수정</button>
                                    </div>
                                </td>
                            </tr>`;
                    }});

                    behaviorTableHTML += `</tbody></table></div>`;
                    behaviorContainer.innerHTML = behaviorTableHTML;

                    function copyBehaviorText(prefix, index) {{
                        const text = behaviorData[index].text;
                        navigator.clipboard.writeText(text).then(() => showBehaviorMessage('복사되었습니다!', 'success'));
                    }}

                    function editBehaviorText(prefix, index) {{
                        const row = document.getElementById(`row-${{prefix}}-${{index}}`);
                        const cell = row.querySelector('.text-cell');
                        const currentText = behaviorData[index].text;

                        cell.innerHTML = `
                            <textarea class="edit-textarea">${{currentText}}</textarea>
                            <div class="button-group">
                                <button class="save-btn" onclick="saveBehaviorEdit('${{prefix}}', ${{index}})">저장</button>
                                <button class="cancel-btn" onclick="cancelBehaviorEdit('${{prefix}}', ${{index}})">취소</button>
                            </div>
                        `;
                        cell.querySelector('textarea').focus();
                    }}
                    
                    function saveBehaviorEdit(prefix, index) {{
                        const row = document.getElementById(`row-${{prefix}}-${{index}}`);
                        const cell = row.querySelector('.text-cell');
                        const newText = cell.querySelector('textarea').value;

                        // Update data model
                        behaviorData[index].text = newText;

                        // Re-render the cell
                        cancelBehaviorEdit(prefix, index); // cancelBehaviorEdit re-renders from the current data model
                        showBehaviorMessage('수정되었습니다!', 'success');
                    }}

                    function cancelBehaviorEdit(prefix, index) {{
                        const row = document.getElementById(`row-${{prefix}}-${{index}}`);
                        const cell = row.querySelector('.text-cell');
                        const item = behaviorData[index];
                        const charCount = item.text.length;
                        const byteCount = (new TextEncoder().encode(item.text)).length;

                        cell.innerHTML = `
                            <div class="text-content">${{item.text.replace(/\\n/g, '<br>')}}</div>
                            <div class="counter-info">${{charCount}}자 / ${{byteCount}}byte</div>
                            <div class="button-group">
                                <button class="copy-btn" onclick="copyBehaviorText('${{prefix}}', ${{index}})">복사</button>
                                <button class="edit-btn" onclick="editBehaviorText('${{prefix}}', ${{index}})">수정</button>
                            </div>
                        `;
                    }}
                    
                    function showBehaviorMessage(message, type) {{
                        const messageDiv = document.createElement('div');
                        messageDiv.textContent = message;
                        messageDiv.style.cssText = `
                            position: fixed;
                            top: 20px;
                            right: 20px;
                            background: ${{type === 'success' ? '#10b981' : '#ef4444'}};
                            color: white;
                            padding: 10px 16px;
                            border-radius: 6px;
                            font-weight: 600;
                            font-size: 13px;
                            z-index: 10000;
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                            animation: slideIn 0.3s ease-out;
                        `;
                        
                        const style = document.createElement('style');
                        style.textContent = `
                            @keyframes slideIn {{
                                from {{ transform: translateX(100%); opacity: 0; }}
                                to {{ transform: translateX(0); opacity: 1; }}
                            }}
                        `;
                        document.head.appendChild(style);
                        document.body.appendChild(messageDiv);
                        
                        setTimeout(() => {{
                            messageDiv.remove();
                            style.remove();
                        }}, 2500);
                    }}
                </script>
                </body></html>
                """
                
                # HTML 컴포넌트로 표시
                components.html(behavior_table_html, height=600, scrolling=True)
