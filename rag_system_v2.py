import pandas as pd
import numpy as np
import pickle
import os
import re
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings("ignore")

class SchoolInfoRAG:
    def __init__(self, csv_path: str = "data/school_info.csv"):
        """
        학교 정보 RAG 시스템 초기화
        
        Args:
            csv_path: CSV 파일 경로
        """
        self.csv_path = csv_path
        self.data = None
        self.model = None
        self.question_embeddings = None
        self.answers = None
        self.questions = None
        self.use_sentence_transformers = False
        
        # 모델 저장 경로
        self.model_path = "rag_model_v2.pkl"
        
        # 데이터 로드 및 초기화
        self.load_data()
        self.initialize_model()
    
    def load_data(self):
        """CSV 데이터 로드"""
        try:
            self.data = pd.read_csv(self.csv_path)
            print(f"데이터 로드 완료: {len(self.data)}개 질문-답변 쌍")
        except Exception as e:
            print(f"데이터 로드 실패: {e}")
            raise
    
    def initialize_model(self):
        """모델 초기화 - sentence-transformers 시도, 실패시 sklearn 사용"""
        # 기존 모델이 있으면 로드 시도
        if os.path.exists(self.model_path):
            try:
                self.load_model()
                return
            except Exception as e:
                print(f"기존 모델 로드 실패: {e}")
        
        # 새 모델 생성
        try:
            # sentence-transformers 시도
            from sentence_transformers import SentenceTransformer
            print("sentence-transformers를 사용하여 RAG 모델 구축 중...")
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.use_sentence_transformers = True
            self.build_sentence_transformer_model()
        except ImportError:
            print("sentence-transformers가 설치되지 않음. sklearn으로 대체...")
            self.build_sklearn_model()
        except Exception as e:
            print(f"sentence-transformers 초기화 실패: {e}")
            print("sklearn으로 대체...")
            self.build_sklearn_model()
        
        # 모델 저장
        self.save_model()
    
    def build_sentence_transformer_model(self):
        """Sentence Transformers를 사용한 모델 구축"""
        # 질문과 답변 추출
        self.questions = self.data['question'].fillna('').astype(str).tolist()
        self.answers = self.data['answer'].fillna('').astype(str).tolist()
        
        # 질문들을 임베딩으로 변환
        print("질문 임베딩 생성 중...")
        self.question_embeddings = self.model.encode(self.questions)
        print("Sentence Transformers 모델 구축 완료")
    
    def build_sklearn_model(self):
        """sklearn을 사용한 백업 모델 구축"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            print("sklearn을 사용하여 RAG 모델 구축 중...")
            
            # 질문과 답변 추출
            self.questions = self.data['question'].fillna('').astype(str).tolist()
            self.answers = self.data['answer'].fillna('').astype(str).tolist()
            
            # 질문 텍스트 전처리
            processed_questions = [self.preprocess_text(q) for q in self.questions]
            
            # TF-IDF 벡터화
            self.model = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words=None,
                sublinear_tf=True,
                norm='l2'
            )
            
            # 질문들을 벡터화
            self.question_embeddings = self.model.fit_transform(processed_questions)
            self.use_sentence_transformers = False
            print("sklearn 모델 구축 완료")
            
        except ImportError as e:
            print(f"sklearn도 사용할 수 없음: {e}")
            print("키워드 매칭 모드로 전환...")
            self.build_keyword_model()
    
    def build_keyword_model(self):
        """키워드 매칭 백업 모델"""
        print("키워드 매칭 모델 구축 중...")
        
        # 질문과 답변 추출
        self.questions = self.data['question'].fillna('').astype(str).tolist()
        self.answers = self.data['answer'].fillna('').astype(str).tolist()
        self.model = None
        self.question_embeddings = None
        self.use_sentence_transformers = False
        
        print("키워드 매칭 모델 구축 완료")
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if pd.isna(text):
            return ""
        
        text = str(text).strip()
        text = re.sub(r'[^\w\s가-힣.,?!]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.lower()
    
    def search_similar_sentence_transformers(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """Sentence Transformers를 사용한 유사도 검색"""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # 쿼리 임베딩 생성
            query_embedding = self.model.encode([query])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_embedding, self.question_embeddings).flatten()
            
            # 상위 k개 결과 선택
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    results.append((
                        self.questions[idx],
                        self.answers[idx],
                        float(similarities[idx])
                    ))
            
            return results
        except Exception as e:
            print(f"Sentence Transformers 검색 실패: {e}")
            return self.search_similar_sklearn(query, top_k)
    
    def search_similar_sklearn(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """sklearn을 사용한 유사도 검색"""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # 쿼리 전처리 및 벡터화
            processed_query = self.preprocess_text(query)
            query_vector = self.model.transform([processed_query])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_vector, self.question_embeddings).flatten()
            
            # 상위 k개 결과 선택
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:
                    results.append((
                        self.questions[idx],
                        self.answers[idx],
                        float(similarities[idx])
                    ))
            
            return results
        except Exception as e:
            print(f"sklearn 검색 실패: {e}")
            return self.search_similar_keyword(query, top_k)
    
    def search_similar_keyword(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """키워드 매칭을 사용한 백업 검색"""
        try:
            # 쿼리에서 키워드 추출
            query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
            
            results = []
            for i, question in enumerate(self.questions):
                question_keywords = set(re.findall(r'\b\w+\b', question.lower()))
                
                # 공통 키워드 비율 계산
                if len(question_keywords) > 0:
                    common_keywords = query_keywords & question_keywords
                    similarity = len(common_keywords) / len(question_keywords | query_keywords)
                    
                    if similarity > 0:
                        results.append((question, self.answers[i], similarity))
            
            # 유사도 순으로 정렬하고 상위 k개 반환
            results.sort(key=lambda x: x[2], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"키워드 매칭 실패: {e}")
            return []
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        """
        유사한 질문-답변 검색 (우선순위: sentence-transformers > sklearn > keyword)
        """
        if not query.strip():
            return []
        
        try:
            if self.use_sentence_transformers and self.model is not None:
                return self.search_similar_sentence_transformers(query, top_k)
            elif self.model is not None:
                return self.search_similar_sklearn(query, top_k)
            else:
                return self.search_similar_keyword(query, top_k)
        except Exception as e:
            print(f"검색 실패: {e}")
            return self.search_similar_keyword(query, top_k)
    
    def get_answer(self, query: str, threshold: float = 0.1) -> dict:
        """
        질문에 대한 답변 생성 - 상위 3개 결과 반환
        """
        similar_results = self.search_similar(query, top_k=3)
        
        if not similar_results:
            return {
                'results': [{
                    'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.',
                    'confidence': 0.0
                }],
                'method': 'none'
            }
        
        # 가장 유사한 결과
        best_match = similar_results[0]
        best_similarity = best_match[2]
        
        # 임계값 확인
        if best_similarity < threshold:
            return {
                'results': [{
                    'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.',
                    'confidence': float(best_similarity)
                }],
                'method': 'sentence_transformers' if self.use_sentence_transformers else 'sklearn' if self.model else 'keyword'
            }
        
        # 상위 3개 결과를 리스트로 구성
        results = []
        for question, answer, similarity in similar_results[:3]:
            if similarity >= threshold:
                results.append({
                    'answer': answer,
                    'confidence': float(similarity),
                    'question': question
                })
        
        # 최소 1개는 반환하되, 임계값 미달 시에도 가장 좋은 것 1개는 포함
        if not results and similar_results:
            results.append({
                'answer': similar_results[0][1],
                'confidence': float(similar_results[0][2]),
                'question': similar_results[0][0]
            })
        
        return {
            'results': results,
            'method': 'sentence_transformers' if self.use_sentence_transformers else 'sklearn' if self.model else 'keyword'
        }
    
    def save_model(self):
        """모델 저장"""
        try:
            model_data = {
                'questions': self.questions,
                'answers': self.answers,
                'use_sentence_transformers': self.use_sentence_transformers,
                'question_embeddings': self.question_embeddings if not self.use_sentence_transformers else None,
                'model': self.model if not self.use_sentence_transformers else None
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print("모델 저장 완료")
        except Exception as e:
            print(f"모델 저장 실패: {e}")
    
    def load_model(self):
        """저장된 모델 로드"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.questions = model_data['questions']
            self.answers = model_data['answers']
            self.use_sentence_transformers = model_data.get('use_sentence_transformers', False)
            
            if self.use_sentence_transformers:
                # sentence-transformers 모델 다시 로드
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                # 임베딩 다시 생성 (저장하기엔 너무 큼)
                self.question_embeddings = self.model.encode(self.questions)
            else:
                self.question_embeddings = model_data.get('question_embeddings')
                self.model = model_data.get('model')
            
            print("저장된 모델 로드 완료")
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            raise

# 전역 RAG 인스턴스
rag_system_v2 = None

def initialize_rag():
    """RAG 시스템 초기화"""
    global rag_system_v2
    if rag_system_v2 is None:
        rag_system_v2 = SchoolInfoRAG()
    return rag_system_v2

def get_rag_answer(query: str) -> dict:
    """RAG 시스템을 통해 답변 얻기"""
    rag = initialize_rag()
    return rag.get_answer(query)

if __name__ == "__main__":
    # 테스트
    print("RAG 시스템 v2 테스트")
    rag = initialize_rag()
    
    test_queries = [
        "교무실 팩스 번호",
        "교장선생님 연락처",
        "김화자 선생님",
        "학교 와이파이"
    ]
    
    for query in test_queries:
        print(f"\n질문: {query}")
        result = get_rag_answer(query)
        print(f"답변: {result['answer']}")
        print(f"신뢰도: {result['confidence']:.3f}")
        print(f"방법: {result['method']}")