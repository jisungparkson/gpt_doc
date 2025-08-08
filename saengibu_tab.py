"""
생기부 기록 탭
"""
import streamlit as st
import streamlit.components.v1 as components
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

def draw_saengibu_tab(prompts):
    """생기부 기록 탭 UI"""
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
                        st.session_state.student_data[i]["achievement"] = st.text_area(
                            "성취기준",
                            value=st.session_state.student_data[i]["achievement"],
                            placeholder=f"성취기준을 입력해주세요. (선택사항)",
                            height=100,
                            key=f"ach_{i}",
                            label_visibility="collapsed"
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
                                        llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
                                        prompt = prompts["student_record"]
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
                        
                        .text-cell {{
                            padding: 20px;
                            position: relative;
                            background: white;
                        }}
                        
                        .text-content {{
                            line-height: 1.6;
                            font-size: 13px;
                            color: #2d3748;
                            min-height: 60px;
                            margin-bottom: 10px;
                            padding-right: 100px;
                        }}
                        
                        .button-group {{
                            display: flex;
                            gap: 8px;
                            justify-content: flex-end;
                            margin-top: 12px;
                        }}
                        
                        .copy-btn, .edit-btn {{
                            background: none;
                            border: 1px solid #e2e8f0;
                            padding: 6px 12px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 12px;
                            transition: all 0.2s ease;
                        }}
                        
                        .copy-btn {{
                            color: #4299e1;
                            border-color: #4299e1;
                        }}
                        
                        .copy-btn:hover {{
                            background: #4299e1;
                            color: white;
                        }}
                        
                        .edit-btn {{
                            color: #48bb78;
                            border-color: #48bb78;
                        }}
                        
                        .edit-btn:hover {{
                            background: #48bb78;
                            color: white;
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
                        }}
                        
                        .save-btn, .cancel-btn {{
                            padding: 6px 12px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 12px;
                            margin-top: 8px;
                            margin-right: 8px;
                        }}
                        
                        .save-btn {{
                            background: #48bb78;
                            color: white;
                        }}
                        
                        .cancel-btn {{
                            background: #e2e8f0;
                            color: #4a5568;
                        }}
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
                                    <td style="text-align: center; padding: 20px; background: #f8fafc; font-weight: 700;">{i + 1}</td>
                                    <td style="text-align: center; padding: 20px; background: #f8fafc; font-weight: 600;">{result_data['name']}</td>
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
                
                custom_table_html += """
                        ];
                        
                        function copyText(index) {
                            const text = originalTexts[index];
                            if (navigator.clipboard) {
                                navigator.clipboard.writeText(text).then(function() {
                                    showMessage('복사되었습니다!', 'success');
                                });
                            } else {
                                const textArea = document.createElement('textarea');
                                textArea.value = text;
                                document.body.appendChild(textArea);
                                textArea.select();
                                document.execCommand('copy');
                                document.body.removeChild(textArea);
                                showMessage('복사되었습니다!', 'success');
                            }
                        }
                        
                        function editText(index) {
                            const cell = document.getElementById('text_' + index);
                            const currentText = originalTexts[index];
                            
                            cell.innerHTML = `
                                <textarea class="edit-textarea">${currentText}</textarea>
                                <button class="save-btn" onclick="saveEdit(${index})">저장</button>
                                <button class="cancel-btn" onclick="cancelEdit(${index})">취소</button>
                            `;
                            cell.querySelector('textarea').focus();
                        }
                        
                        function saveEdit(index) {
                            const cell = document.getElementById('text_' + index);
                            const textarea = cell.querySelector('textarea');
                            const newText = textarea.value;
                            
                            originalTexts[index] = newText;
                            
                            cell.innerHTML = `
                                <div class="text-content">
                                    ${newText.replace(/\\n/g, '<br>')}
                                </div>
                                <div class="button-group">
                                    <button class="copy-btn" onclick="copyText(${index})">복사</button>
                                    <button class="edit-btn" onclick="editText(${index})">수정</button>
                                </div>
                            `;
                            
                            showMessage('수정되었습니다!', 'success');
                        }
                        
                        function cancelEdit(index) {
                            const cell = document.getElementById('text_' + index);
                            const originalText = originalTexts[index];
                            
                            cell.innerHTML = `
                                <div class="text-content">
                                    ${originalText.replace(/\\n/g, '<br>')}
                                </div>
                                <div class="button-group">
                                    <button class="copy-btn" onclick="copyText(${index})">복사</button>
                                    <button class="edit-btn" onclick="editText(${index})">수정</button>
                                </div>
                            `;
                        }
                        
                        function showMessage(message, type) {
                            const messageDiv = document.createElement('div');
                            messageDiv.textContent = message;
                            messageDiv.style.cssText = `
                                position: fixed;
                                top: 20px;
                                right: 20px;
                                background: ${type === 'success' ? '#48bb78' : '#f56565'};
                                color: white;
                                padding: 12px 20px;
                                border-radius: 8px;
                                font-weight: 600;
                                z-index: 1000;
                                animation: slideIn 0.3s ease-out;
                            `;
                            
                            const style = document.createElement('style');
                            style.textContent = `
                                @keyframes slideIn {
                                    from { transform: translateX(100%); }
                                    to { transform: translateX(0); }
                                }
                            `;
                            document.head.appendChild(style);
                            document.body.appendChild(messageDiv);
                            
                            setTimeout(() => {
                                messageDiv.remove();
                                style.remove();
                            }, 3000);
                        }
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
                        key=f"behavior_name_{i}",
                        label_visibility="collapsed"
                    )
                
                with cols[2]:
                    st.session_state.behavior_student_data[i]["behavior_content"] = st.text_area(
                        "행동 내용",
                        value=st.session_state.behavior_student_data[i]["behavior_content"],
                        placeholder=f"{st.session_state.behavior_student_data[i]['name']}의 행동 특성, 성장 모습, 인성 발달 등을 구체적으로 기록해주세요.",
                        height=100,
                        key=f"behavior_content_{i}",
                        label_visibility="collapsed"
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
                                    llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
                                    prompt = prompts["behavior_record"]
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
                
                # 행발 결과 표시용 HTML 테이블
                behavior_table_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        .behavior-table-container {
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                            overflow: hidden;
                            border: 1px solid #e2e8f0;
                        }
                        
                        .behavior-table {
                            width: 100%;
                            border-collapse: collapse;
                        }
                        
                        .behavior-table th {
                            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                            color: white;
                            padding: 16px;
                            text-align: center;
                            font-weight: 600;
                            font-size: 14px;
                        }
                        
                        .behavior-table td {
                            padding: 20px;
                            border-bottom: 1px solid #e2e8f0;
                            vertical-align: top;
                        }
                        
                        .behavior-number {
                            text-align: center;
                            background: #f8fafc;
                            font-weight: 700;
                            width: 80px;
                        }
                        
                        .behavior-name {
                            text-align: center;
                            background: #f8fafc;
                            font-weight: 600;
                            width: 120px;
                        }
                        
                        .behavior-content {
                            line-height: 1.6;
                            font-size: 13px;
                            color: #2d3748;
                        }
                        
                        .behavior-actions {
                            margin-top: 10px;
                            display: flex;
                            gap: 8px;
                            justify-content: flex-end;
                        }
                        
                        .behavior-btn {
                            padding: 6px 12px;
                            border: 1px solid;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 12px;
                            background: white;
                        }
                        
                        .behavior-copy {
                            color: #4299e1;
                            border-color: #4299e1;
                        }
                        
                        .behavior-edit {
                            color: #48bb78;
                            border-color: #48bb78;
                        }
                    </style>
                </head>
                <body>
                    <div class="behavior-table-container">
                        <table class="behavior-table">
                            <thead>
                                <tr>
                                    <th>번호</th>
                                    <th>이름</th>
                                    <th>행발 내용</th>
                                </tr>
                            </thead>
                            <tbody>
                """
                
                # 행발 데이터 추가
                for i, result in enumerate(st.session_state.generated_behavior_table_results):
                    behavior_table_html += f"""
                                <tr>
                                    <td class="behavior-number">{i+1:02d}</td>
                                    <td class="behavior-name">{result["name"]}</td>
                                    <td>
                                        <div class="behavior-content" id="behavior_{i}">
                                            {result["result"].replace(chr(10), '<br>')}
                                        </div>
                                        <div class="behavior-actions">
                                            <button class="behavior-btn behavior-copy" onclick="copyBehavior({i})">복사</button>
                                            <button class="behavior-btn behavior-edit" onclick="editBehavior({i})">수정</button>
                                        </div>
                                    </td>
                                </tr>
                    """
                
                behavior_table_html += """
                            </tbody>
                        </table>
                    </div>
                    <script>
                        const behaviorTexts = [
                """
                
                # JavaScript 배열에 행발 텍스트 추가
                for i, result in enumerate(st.session_state.generated_behavior_table_results):
                    escaped_text = result["result"].replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
                    behavior_table_html += f"            '{escaped_text}'"
                    if i < len(st.session_state.generated_behavior_table_results) - 1:
                        behavior_table_html += ","
                    behavior_table_html += "\n"
                
                behavior_table_html += """
                        ];
                        
                        function copyBehavior(index) {
                            const text = behaviorTexts[index];
                            if (navigator.clipboard) {
                                navigator.clipboard.writeText(text).then(() => {
                                    showBehaviorMessage('복사되었습니다!');
                                });
                            }
                        }
                        
                        function editBehavior(index) {
                            const contentDiv = document.getElementById('behavior_' + index);
                            const currentText = behaviorTexts[index];
                            
                            contentDiv.innerHTML = `
                                <textarea style="width:100%; min-height:100px; padding:10px; border:2px solid #e2e8f0; border-radius:8px; font-size:13px; line-height:1.6;" id="edit_${index}">${currentText}</textarea>
                                <div style="margin-top:8px;">
                                    <button onclick="saveBehavior(${index})" style="background:#48bb78; color:white; border:none; padding:6px 12px; border-radius:4px; cursor:pointer; margin-right:8px;">저장</button>
                                    <button onclick="cancelBehavior(${index})" style="background:#e2e8f0; color:#4a5568; border:none; padding:6px 12px; border-radius:4px; cursor:pointer;">취소</button>
                                </div>
                            `;
                        }
                        
                        function saveBehavior(index) {
                            const textarea = document.getElementById('edit_' + index);
                            const newText = textarea.value;
                            behaviorTexts[index] = newText;
                            
                            const contentDiv = document.getElementById('behavior_' + index);
                            contentDiv.innerHTML = newText.replace(/\\n/g, '<br>');
                            showBehaviorMessage('수정되었습니다!');
                        }
                        
                        function cancelBehavior(index) {
                            const contentDiv = document.getElementById('behavior_' + index);
                            contentDiv.innerHTML = behaviorTexts[index].replace(/\\n/g, '<br>');
                        }
                        
                        function showBehaviorMessage(message) {
                            const msgDiv = document.createElement('div');
                            msgDiv.textContent = message;
                            msgDiv.style.cssText = `
                                position: fixed;
                                top: 20px;
                                right: 20px;
                                background: #48bb78;
                                color: white;
                                padding: 12px 20px;
                                border-radius: 8px;
                                font-weight: 600;
                                z-index: 1000;
                            `;
                            document.body.appendChild(msgDiv);
                            setTimeout(() => msgDiv.remove(), 3000);
                        }
                    </script>
                </body>
                </html>
                """
                
                # HTML 컴포넌트로 표시
                st.components.v1.html(behavior_table_html, height=600, scrolling=True)