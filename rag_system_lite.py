import pandas as pd
import re
from typing import List, Tuple, Dict
import json
import os

class SchoolInfoRAGLite:
    def __init__(self, csv_path: str = "data/school_info.csv"):
        """
        가벼운 학교 정보 RAG 시스템 (의존성 최소화)
        
        Args:
            csv_path: CSV 파일 경로
        """
        self.csv_path = csv_path
        self.data = None
        self.questions = []
        self.answers = []
        self.keywords_index = {}
        
        # 데이터 로드 및 초기화
        self.load_data()
        self.build_keyword_index()
    
    def load_data(self):
        """CSV 데이터 로드"""
        try:
            self.data = pd.read_csv(self.csv_path)
            self.questions = self.data['question'].fillna('').astype(str).tolist()
            self.answers = self.data['answer'].fillna('').astype(str).tolist()
            print(f"데이터 로드 완료: {len(self.data)}개 질문-답변 쌍")
        except Exception as e:
            print(f"데이터 로드 실패: {e}")
            raise
    
    def extract_keywords(self, text: str) -> set:
        """텍스트에서 키워드 추출"""
        # 한글, 영문, 숫자만 추출
        text = re.sub(r'[^\w\s가-힣]', ' ', text.lower())
        keywords = set(re.findall(r'\b\w+\b', text))
        
        # 한 글자 키워드는 제외 (조사, 어미 등)
        keywords = {kw for kw in keywords if len(kw) > 1}
        
        return keywords
    
    def build_keyword_index(self):
        """키워드 인덱스 구축"""
        print("키워드 인덱스 구축 중...")
        
        for i, question in enumerate(self.questions):
            keywords = self.extract_keywords(question)
            
            for keyword in keywords:
                if keyword not in self.keywords_index:
                    self.keywords_index[keyword] = []
                self.keywords_index[keyword].append(i)
        
        print(f"키워드 인덱스 구축 완료: {len(self.keywords_index)}개 키워드")
    
    def calculate_similarity(self, query: str, question: str) -> float:
        """문자열 유사도 계산 (간단한 방법)"""
        query_keywords = self.extract_keywords(query)
        question_keywords = self.extract_keywords(question)
        
        if not query_keywords or not question_keywords:
            return 0.0
        
        # Jaccard 유사도 계산
        intersection = len(query_keywords & question_keywords)
        union = len(query_keywords | question_keywords)
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # 길이 보정 (더 긴 문장일수록 매칭이 어려우므로)
        length_factor = min(len(query_keywords), len(question_keywords)) / max(len(query_keywords), len(question_keywords))
        
        return jaccard_similarity * length_factor
    
    def search_by_exact_match(self, query: str) -> List[Tuple[str, str, float]]:
        """정확한 매칭 검색"""
        results = []
        query_lower = query.lower()
        
        for i, question in enumerate(self.questions):
            question_lower = question.lower()
            
            # 완전 매칭
            if query_lower == question_lower:
                results.append((question, self.answers[i], 1.0))
            # 부분 매칭
            elif query_lower in question_lower or question_lower in query_lower:
                # 더 정확한 유사도 계산
                similarity = self.calculate_similarity(query, question)
                if similarity > 0:
                    results.append((question, self.answers[i], similarity))
        
        return results
    
    def search_by_keywords(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """키워드 기반 검색"""
        query_keywords = self.extract_keywords(query)
        
        if not query_keywords:
            return []
        
        # 각 질문에 대한 점수 계산
        question_scores = {}
        
        for keyword in query_keywords:
            if keyword in self.keywords_index:
                for question_idx in self.keywords_index[keyword]:
                    if question_idx not in question_scores:
                        question_scores[question_idx] = 0
                    question_scores[question_idx] += 1
        
        # 점수를 유사도로 변환하고 정렬
        results = []
        for question_idx, score in question_scores.items():
            similarity = score / len(query_keywords)  # 정규화
            results.append((
                self.questions[question_idx],
                self.answers[question_idx],
                similarity
            ))
        
        # 유사도 순으로 정렬
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results[:top_k]
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """유사한 질문-답변 검색"""
        if not query.strip():
            return []
        
        # 1. 정확한 매칭 먼저 시도
        exact_results = self.search_by_exact_match(query)
        if exact_results:
            return exact_results[:top_k]
        
        # 2. 키워드 기반 검색
        keyword_results = self.search_by_keywords(query, top_k)
        
        # 3. 추가적으로 모든 질문과 유사도 계산 (상위 결과가 부족한 경우)
        if len(keyword_results) < top_k:
            all_similarities = []
            
            for i, question in enumerate(self.questions):
                # 이미 키워드 검색에서 찾은 것은 제외
                if not any(question == result[0] for result in keyword_results):
                    similarity = self.calculate_similarity(query, question)
                    if similarity > 0:
                        all_similarities.append((question, self.answers[i], similarity))
            
            # 유사도 순으로 정렬
            all_similarities.sort(key=lambda x: x[2], reverse=True)
            
            # 키워드 결과와 합치기
            keyword_results.extend(all_similarities[:top_k - len(keyword_results)])
        
        return keyword_results[:top_k]
    
    def get_answer(self, query: str, threshold: float = 0.1) -> dict:
        """질문에 대한 답변 생성"""
        similar_results = self.search_similar(query, top_k=3)
        
        if not similar_results:
            return {
                'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.',
                'confidence': 0.0,
                'sources': [],
                'method': 'keyword_lite'
            }
        
        # 가장 유사한 결과
        best_match = similar_results[0]
        best_similarity = best_match[2]
        
        # 임계값 확인
        if best_similarity < threshold:
            return {
                'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.',
                'confidence': float(best_similarity),
                'sources': [],
                'method': 'keyword_lite'
            }
        
        # 관련 답변들 수집
        sources = []
        for question, answer, similarity in similar_results:
            if similarity >= threshold:
                sources.append({
                    'question': question,
                    'answer': answer,
                    'similarity': float(similarity)
                })
        
        # 가장 유사한 답변을 메인 답변으로 사용
        main_answer = similar_results[0][1]
        
        return {
            'answer': main_answer,
            'confidence': float(best_similarity),
            'sources': sources,
            'method': 'keyword_lite'
        }

# 전역 RAG 인스턴스
rag_system_lite = None

def initialize_rag():
    """RAG 시스템 초기화"""
    global rag_system_lite
    if rag_system_lite is None:
        rag_system_lite = SchoolInfoRAGLite()
    return rag_system_lite

def get_rag_answer(query: str) -> dict:
    """RAG 시스템을 통해 답변 얻기"""
    rag = initialize_rag()
    return rag.get_answer(query)

if __name__ == "__main__":
    # 테스트
    print("RAG 시스템 Lite 테스트")
    rag = initialize_rag()
    
    test_queries = [
        "교무실 팩스 번호",
        "교장선생님 연락처", 
        "김화자 선생님",
        "학교 와이파이",
        "팩스번호가 뭐야"
    ]
    
    for query in test_queries:
        print(f"\n질문: {query}")
        result = get_rag_answer(query)
        print(f"답변: {result['answer']}")
        print(f"신뢰도: {result['confidence']:.3f}")
        print(f"방법: {result['method']}")
        if result['sources']:
            print("참고 자료:")
            for i, source in enumerate(result['sources'][:2]):
                print(f"  {i+1}. {source['question']} (유사도: {source['similarity']:.3f})")