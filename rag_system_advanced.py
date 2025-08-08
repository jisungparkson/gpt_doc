"""
LangChain 기반 고급 RAG 시스템
MultiQueryRetriever와 개선된 데이터 처리를 통한 검색 정확도 향상
"""
import pandas as pd
import numpy as np
import os
import warnings
from typing import List, Dict, Any, Optional
import pickle
from pathlib import Path

warnings.filterwarnings("ignore")

# LangChain imports (최신 버전 사용)
from langchain.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

class AdvancedSchoolInfoRAG:
    def __init__(self, csv_path: str = "data/school_info.csv"):
        """
        고급 학교 정보 RAG 시스템 초기화
        
        Args:
            csv_path: CSV 파일 경로
        """
        self.csv_path = csv_path
        self.vectorstore = None
        self.retriever = None
        self.multi_query_retriever = None
        self.llm = None
        self.documents = None
        self.embedding_model = None
        
        # 저장 경로
        self.vectorstore_path = "vectorstore_advanced"
        self.cache_path = "rag_cache_advanced.pkl"
        
        print("고급 RAG 시스템 초기화 중...")
        self.initialize()
    
    def load_and_process_data(self):
        """CSV 데이터를 로드하고 LangChain Document 형태로 변환"""
        try:
            print("CSV 데이터 로드 및 처리 중...")
            df = pd.read_csv(self.csv_path)
            print(f"총 {len(df)}개의 질문-답변 쌍 로드됨")
            
            # Document 객체 생성 - 질문과 답변을 하나의 문서로 결합
            documents = []
            for index, row in df.iterrows():
                # 질문과 답변을 자연스러운 형태로 결합
                content = f"질문: {row['question']}\n답변: {row['answer']}"
                
                # 메타데이터 추가 (검색 결과 추적용)
                metadata = {
                    'source': f"school_info_row_{index}",
                    'question': str(row['question']),
                    'answer': str(row['answer']),
                    'row_index': index
                }
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            self.documents = documents
            print(f"총 {len(documents)}개의 Document 생성 완료")
            return documents
            
        except Exception as e:
            print(f"데이터 로드 및 처리 실패: {e}")
            raise
    
    def setup_embeddings(self):
        """임베딩 모델 설정 - OpenAI 우선, 실패시 HuggingFace로 대체"""
        try:
            # OpenAI 임베딩 시도
            print("OpenAI 임베딩 모델 초기화 중...")
            self.embedding_model = OpenAIEmbeddings()
            print("OpenAI 임베딩 모델 설정 완료")
            return True
        except Exception as e:
            print(f"OpenAI 임베딩 실패: {e}")
            try:
                # HuggingFace 임베딩으로 대체
                print("HuggingFace 임베딩 모델로 대체 중...")
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                )
                print("HuggingFace 임베딩 모델 설정 완료")
                return True
            except Exception as e2:
                print(f"HuggingFace 임베딩도 실패: {e2}")
                return False
    
    def create_vectorstore(self):
        """벡터 스토어 생성 또는 로드"""
        try:
            # 기존 벡터 스토어가 있으면 로드 시도
            if os.path.exists(self.vectorstore_path):
                try:
                    print("기존 벡터 스토어 로드 중...")
                    self.vectorstore = FAISS.load_local(
                        self.vectorstore_path, 
                        self.embedding_model,
                        allow_dangerous_deserialization=True
                    )
                    print("기존 벡터 스토어 로드 완료")
                    return True
                except Exception as e:
                    print(f"기존 벡터 스토어 로드 실패: {e}")
                    print("새로운 벡터 스토어를 생성합니다.")
            
            # 새로운 벡터 스토어 생성
            print("새로운 벡터 스토어 생성 중...")
            
            # 텍스트 분할 (필요시)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            # 문서가 너무 길 경우에만 분할
            processed_docs = []
            for doc in self.documents:
                if len(doc.page_content) > 800:
                    splits = text_splitter.split_documents([doc])
                    processed_docs.extend(splits)
                else:
                    processed_docs.append(doc)
            
            # FAISS 벡터 스토어 생성
            self.vectorstore = FAISS.from_documents(
                processed_docs,
                self.embedding_model
            )
            
            # 벡터 스토어 저장
            self.vectorstore.save_local(self.vectorstore_path)
            print(f"벡터 스토어 생성 및 저장 완료 (총 {len(processed_docs)}개 문서)")
            
            return True
            
        except Exception as e:
            print(f"벡터 스토어 생성 실패: {e}")
            return False
    
    def setup_llm(self):
        """LLM 설정"""
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",  # 비용 효율적인 모델 사용
                temperature=0.1,
                max_tokens=1000
            )
            print("LLM 설정 완료")
            return True
        except Exception as e:
            print(f"LLM 설정 실패: {e}")
            return False
    
    def setup_retrievers(self):
        """검색기 설정 - 기본 retriever와 MultiQueryRetriever"""
        try:
            # 기본 retriever 설정
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 5,  # 더 많은 결과 검색
                    "score_threshold": 0.3  # 임계값 낮춤
                }
            )
            
            # MultiQueryRetriever 설정 (핵심 개선점)
            if self.llm:
                print("MultiQueryRetriever 설정 중...")
                self.multi_query_retriever = MultiQueryRetriever.from_llm(
                    retriever=self.retriever,
                    llm=self.llm,
                    prompt=self._get_multi_query_prompt()
                )
                print("MultiQueryRetriever 설정 완료")
            
            return True
            
        except Exception as e:
            print(f"검색기 설정 실패: {e}")
            return False
    
    def _get_multi_query_prompt(self):
        """MultiQueryRetriever용 커스텀 프롬프트"""
        return PromptTemplate(
            input_variables=["question"],
            template="""당신은 학교 정보 검색을 도와주는 AI 어시스턴트입니다. 
사용자의 질문을 받아서, 다양한 관점에서 관련 정보를 찾을 수 있는 3-5개의 검색 질문을 생성해주세요.

원본 질문: {question}

다음과 같은 다양한 관점에서 검색 질문을 만들어 주세요:
1. 직접적인 정보 요청
2. 관련 담당자나 부서 정보
3. 연락처나 위치 정보
4. 관련 업무나 절차 정보
5. 유사하거나 관련된 다른 키워드

각 질문은 한 줄씩 작성해주세요."""
        )
    
    def initialize(self):
        """전체 RAG 시스템 초기화"""
        try:
            # 1. 데이터 로드 및 처리
            self.load_and_process_data()
            
            # 2. 임베딩 모델 설정
            if not self.setup_embeddings():
                raise Exception("임베딩 모델 설정 실패")
            
            # 3. 벡터 스토어 생성
            if not self.create_vectorstore():
                raise Exception("벡터 스토어 생성 실패")
            
            # 4. LLM 설정
            if not self.setup_llm():
                print("LLM 설정 실패 - MultiQueryRetriever를 사용할 수 없습니다")
            
            # 5. 검색기 설정
            if not self.setup_retrievers():
                raise Exception("검색기 설정 실패")
            
            print("고급 RAG 시스템 초기화 완료!")
            
        except Exception as e:
            print(f"RAG 시스템 초기화 실패: {e}")
            raise
    
    def search_with_multi_query(self, query: str, use_multi_query: bool = True) -> List[Document]:
        """MultiQueryRetriever를 사용한 검색"""
        try:
            if use_multi_query and self.multi_query_retriever:
                print(f"MultiQueryRetriever로 검색: '{query}'")
                results = self.multi_query_retriever.get_relevant_documents(query)
                print(f"MultiQuery 검색 결과: {len(results)}개 문서")
            else:
                print(f"기본 retriever로 검색: '{query}'")
                results = self.retriever.get_relevant_documents(query)
                print(f"기본 검색 결과: {len(results)}개 문서")
            
            return results
            
        except Exception as e:
            print(f"검색 실패: {e}")
            # 폴백: 기본 검색기 사용
            if self.retriever:
                return self.retriever.get_relevant_documents(query)
            return []
    
    def get_answer(self, query: str, use_multi_query: bool = True, max_results: int = 3) -> Dict[str, Any]:
        """
        질문에 대한 답변 생성
        
        Args:
            query: 검색 질문
            use_multi_query: MultiQueryRetriever 사용 여부
            max_results: 최대 반환 결과 수
        """
        if not query.strip():
            return {
                'results': [{
                    'answer': '질문을 입력해주세요.',
                    'confidence': 0.0
                }],
                'method': 'none',
                'query': query
            }
        
        try:
            # 문서 검색
            docs = self.search_with_multi_query(query, use_multi_query)
            
            if not docs:
                return {
                    'results': [{
                        'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.',
                        'confidence': 0.0
                    }],
                    'method': 'multi_query' if use_multi_query else 'basic',
                    'query': query
                }
            
            # 결과 처리 및 점수 계산
            results = []
            seen_answers = set()  # 중복 제거용
            
            for i, doc in enumerate(docs[:max_results * 2]):  # 더 많이 가져와서 중복 제거 후 선택
                try:
                    # 메타데이터에서 원본 답변 추출
                    answer = doc.metadata.get('answer', '답변을 찾을 수 없습니다.')
                    question = doc.metadata.get('question', '')
                    
                    # 중복 제거
                    if answer in seen_answers:
                        continue
                    seen_answers.add(answer)
                    
                    # 간단한 신뢰도 점수 계산 (검색 순서 기반)
                    confidence = max(0.9 - i * 0.15, 0.1)
                    
                    results.append({
                        'answer': answer,
                        'confidence': confidence,
                        'question': question,
                        'source': doc.metadata.get('source', ''),
                        'content_preview': doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    })
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    print(f"결과 처리 오류: {e}")
                    continue
            
            # 최소 1개 결과는 보장
            if not results and docs:
                try:
                    first_doc = docs[0]
                    results.append({
                        'answer': first_doc.metadata.get('answer', first_doc.page_content),
                        'confidence': 0.5,
                        'question': first_doc.metadata.get('question', ''),
                        'source': first_doc.metadata.get('source', ''),
                        'content_preview': first_doc.page_content[:100] + "..."
                    })
                except:
                    results.append({
                        'answer': '검색 결과를 처리하는 중 오류가 발생했습니다.',
                        'confidence': 0.1
                    })
            
            return {
                'results': results,
                'method': 'multi_query' if use_multi_query else 'basic',
                'query': query,
                'total_docs_found': len(docs)
            }
            
        except Exception as e:
            print(f"답변 생성 실패: {e}")
            return {
                'results': [{
                    'answer': f'검색 중 오류가 발생했습니다: {str(e)}',
                    'confidence': 0.0
                }],
                'method': 'error',
                'query': query
            }

# 전역 RAG 인스턴스
advanced_rag_system = None

def initialize_rag():
    """고급 RAG 시스템 초기화"""
    global advanced_rag_system
    if advanced_rag_system is None:
        advanced_rag_system = AdvancedSchoolInfoRAG()
    return advanced_rag_system

def get_rag_answer(query: str, use_multi_query: bool = True) -> Dict[str, Any]:
    """
    고급 RAG 시스템을 통해 답변 얻기
    
    Args:
        query: 검색 질문
        use_multi_query: MultiQueryRetriever 사용 여부 (기본값: True)
    """
    rag = initialize_rag()
    return rag.get_answer(query, use_multi_query=use_multi_query)

if __name__ == "__main__":
    # 테스트
    print("=== 고급 RAG 시스템 테스트 ===")
    
    test_queries = [
        "학년업무",        # answer에만 있는 키워드
        "노주영",          # 사람 이름
        "교장선생님",      # 일반적인 질문
        "팩스 번호",       # 구체적인 정보
        "8401",           # 숫자 검색
        "김화자",          # 교장 이름
        "1-1반 담임",      # 복합 검색
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"질문: '{query}'")
        print("-" * 50)
        
        # MultiQuery 사용
        result = get_rag_answer(query, use_multi_query=True)
        print(f"검색 방법: {result['method']}")
        print(f"총 발견 문서: {result.get('total_docs_found', 'N/A')}개")
        
        for i, res in enumerate(result['results'][:2], 1):  # 상위 2개만 표시
            print(f"\n답변 {i}:")
            print(f"  내용: {res['answer']}")
            print(f"  신뢰도: {res['confidence']:.3f}")
            if 'question' in res and res['question']:
                print(f"  원본 질문: {res['question']}")