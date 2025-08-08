import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from typing import List, Tuple
import re

class SchoolInfoRAG:
    def __init__(self, csv_path: str = "data/school_info.csv"):
        """
        학교 정보 RAG 시스템 초기화
        
        Args:
            csv_path: CSV 파일 경로
        """
        self.csv_path = csv_path
        self.data = None
        self.vectorizer = None
        self.question_vectors = None
        self.answers = None
        self.questions = None
        
        # 모델 저장 경로
        self.model_path = "rag_model.pkl"
        
        # 데이터 로드 및 초기화
        self.load_data()
        
        # 기존 모델이 있으면 로드, 없으면 새로 생성
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            self.build_model()
            self.save_model()
    
    def load_data(self):
        """CSV 데이터 로드"""
        try:
            self.data = pd.read_csv(self.csv_path)
            print(f"데이터 로드 완료: {len(self.data)}개 질문-답변 쌍")
        except Exception as e:
            print(f"데이터 로드 실패: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if pd.isna(text):
            return ""
        
        # 기본 정리
        text = str(text).strip()
        
        # 특수문자 정리 (한글, 영문, 숫자, 공백, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,?!]', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.lower()
    
    def build_model(self):
        """RAG 모델 구축"""
        print("RAG 모델 구축 시작...")
        
        # 질문과 답변 추출
        self.questions = self.data['question'].fillna('').astype(str).tolist()
        self.answers = self.data['answer'].fillna('').astype(str).tolist()
        
        # 질문 텍스트 전처리
        processed_questions = [self.preprocess_text(q) for q in self.questions]
        
        # TF-IDF 벡터화
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),  # 1-gram과 2-gram 사용
            stop_words=None,  # 한글에는 기본 불용어 사전이 없음
            sublinear_tf=True,
            norm='l2'
        )
        
        # 질문들을 벡터화
        self.question_vectors = self.vectorizer.fit_transform(processed_questions)
        
        print("RAG 모델 구축 완료")
    
    def save_model(self):
        """모델 저장"""
        model_data = {
            'vectorizer': self.vectorizer,
            'question_vectors': self.question_vectors,
            'questions': self.questions,
            'answers': self.answers
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print("모델 저장 완료")
    
    def load_model(self):
        """저장된 모델 로드"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.vectorizer = model_data['vectorizer']
            self.question_vectors = model_data['question_vectors']
            self.questions = model_data['questions']
            self.answers = model_data['answers']
            
            print("저장된 모델 로드 완료")
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            print("새 모델을 생성합니다...")
            self.build_model()
            self.save_model()
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """
        유사한 질문-답변 검색
        
        Args:
            query: 사용자 질문
            top_k: 반환할 상위 결과 개수
            
        Returns:
            List of (question, answer, similarity_score) tuples
        """
        if not query.strip():
            return []
        
        # 질문 전처리 및 벡터화
        processed_query = self.preprocess_text(query)
        query_vector = self.vectorizer.transform([processed_query])
        
        # 코사인 유사도 계산
        similarities = cosine_similarity(query_vector, self.question_vectors).flatten()
        
        # 상위 k개 결과 선택
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # 유사도가 0보다 큰 경우만
                results.append((
                    self.questions[idx],
                    self.answers[idx],
                    float(similarities[idx])
                ))
        
        return results
    
    def get_answer(self, query: str, threshold: float = 0.1) -> dict:
        """
        질문에 대한 답변 생성
        
        Args:
            query: 사용자 질문
            threshold: 최소 유사도 임계값
            
        Returns:
            답변 정보가 담긴 딕셔너리
        """
        similar_results = self.search_similar(query, top_k=3)
        
        if not similar_results:
            return {
                'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.',
                'confidence': 0.0,
                'sources': []
            }
        
        # 가장 유사한 결과
        best_match = similar_results[0]
        best_similarity = best_match[2]
        
        if best_similarity < threshold:
            return {
                'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.',
                'confidence': float(best_similarity),
                'sources': []
            }
        
        # 높은 유사도의 결과들을 조합하여 답변 생성
        relevant_answers = []
        sources = []
        
        for question, answer, similarity in similar_results:
            if similarity >= threshold:
                relevant_answers.append(answer)
                sources.append({
                    'question': question,
                    'answer': answer,
                    'similarity': float(similarity)
                })
        
        # 가장 유사한 답변을 메인 답변으로 사용
        main_answer = relevant_answers[0] if relevant_answers else "관련 정보를 찾을 수 없습니다."
        
        return {
            'answer': main_answer,
            'confidence': float(best_similarity),
            'sources': sources
        }

# 전역 RAG 인스턴스
rag_system = None

def initialize_rag():
    """RAG 시스템 초기화"""
    global rag_system
    if rag_system is None:
        rag_system = SchoolInfoRAG()
    return rag_system

def get_rag_answer(query: str) -> dict:
    """RAG 시스템을 통해 답변 얻기"""
    rag = initialize_rag()
    return rag.get_answer(query)