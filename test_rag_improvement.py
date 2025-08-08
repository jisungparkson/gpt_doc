"""
RAG 시스템 성능 개선 테스트
full_text 컬럼 추가 전후 비교
"""
import pandas as pd
from rag_system_v2 import get_rag_answer, initialize_rag

def test_improved_rag():
    """개선된 RAG 시스템 테스트"""
    print("=== RAG 시스템 개선 테스트 ===\n")
    
    # RAG 시스템 초기화
    rag = initialize_rag()
    
    # 테스트 케이스들
    test_cases = [
        # 질문에만 있는 키워드로 검색
        "교장선생님",
        "김화자",
        
        # 답변에만 있는 키워드로 검색
        "8401",  # 교장선생님 내선번호
        "팩스",
        
        # 조합 검색
        "교무실 전화",
        "선생님 내선번호",
        
        # 구체적인 검색
        "1-1반 담임",
        "체육 선생님"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"{i}. 질문: '{query}'")
        result = get_rag_answer(query)
        
        print(f"   검색 방법: {result['method']}")
        
        if result['results']:
            best_result = result['results'][0]
            print(f"   최고 답변: {best_result['answer']}")
            print(f"   신뢰도: {best_result['confidence']:.3f}")
            if 'question' in best_result:
                print(f"   매칭된 질문: {best_result['question']}")
        else:
            print("   답변을 찾을 수 없습니다.")
        
        print()

if __name__ == "__main__":
    test_improved_rag()