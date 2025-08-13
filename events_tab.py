import streamlit as st
import streamlit.components.v1 as components

def draw_events_tab():
    """화정초 월중행사 탭 UI (레이아웃 충돌 해결 최종 버전)"""
    st.header("📅 화정초 월중행사")
    st.markdown("매월 학교의 주요 행사 일정을 확인하실 수 있습니다. 아래에서 바로 보거나, 버튼을 눌러 직접 편집할 수 있습니다.")

    google_doc_edit_url = "https://docs.google.com/document/d/1HdnvbG-VlB-T5349iKXY8eli8PFxbt1QQzKovFeGNIs/edit?usp=sharing"

    st.link_button("✍️ 구글 문서에서 직접 편집하기", google_doc_edit_url, use_container_width=True)
    
    st.info("👆 위 버튼을 클릭하면 새 탭에서 편집 화면이 열립니다.")
    st.divider()

    st.subheader("📄 문서 미리보기")
    
    # iframe에 삽입(embed)하기 위한 미리보기 URL 생성
    embed_url = google_doc_edit_url.replace("/edit?usp=sharing", "/preview")

    # HTML과 CSS를 사용하여 iframe을 100% 너비의 div로 감싸서, 강제로 전체 너비를 차지하게 만듭니다.
    components.html(
        f'''
        <div style="width: 100%; overflow: hidden;">
            <iframe
                src="{embed_url}"
                style="width: 100%; height: 800px; border: none; margin: 0; padding: 0;">
            </iframe>
        </div>
        ''',
        height=810  # iframe 높이 + 약간의 여유
    )