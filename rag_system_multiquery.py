"""
LangChain MultiQueryRetriever 기반 고급 RAG 시스템
검색 정확도 극대화를 위한 다중 질문 생성 및 검색
"""
import pandas as pd
import os
import warnings
from typing import List, Dict, Any
import pickle
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
warnings.filterwarnings("ignore")

try:
    # LangChain 필수 라이브러리들
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.docstore.document import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain.retrievers.multi_query import MultiQueryRetriever
    from langchain.prompts import PromptTemplate
    
    LANGCHAIN_AVAILABLE = True
    print("LangChain 라이브러리 로드 완료")
except ImportError as e:
    print(f"LangChain 라이브러리 로드 실패: {e}")
    LANGCHAIN_AVAILABLE = False

class MultiQueryRAGSystem:
    def __init__(self, csv_path: str = "data/school_info.csv"):
        """
        MultiQuery RAG 시스템 초기화
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 라이브러리가 설치되지 않았습니다.")
        
        self.csv_path = csv_path
        self.vectorstore = None
        self.basic_retriever = None
        self.multi_query_retriever = None
        self.llm = None
        self.documents = None
        self.embedding_model = None
        
        # 저장 경로
        self.vectorstore_path = "vectorstore_multiquery"
        
        print("MultiQuery RAG 시스템 초기화 시작...")
        self.initialize_system()
    
    def load_and_prepare_documents(self):
        """CSV 데이터를 로드하고 Document 형태로 변환"""
        try:
            print("CSV 데이터 로드 중...")
            df = pd.read_csv(self.csv_path)
            print(f"총 {len(df)}개의 데이터 로드됨")
            
            documents = []
            for idx, row in df.iterrows():
                # 질문과 답변을 자연스럽게 결합
                content = f"질문: {row['question']}\n답변: {row['answer']}"
                
                metadata = {
                    'source': f"school_info_{idx}",
                    'question': str(row['question']),
                    'answer': str(row['answer']),
                    'id': idx
                }
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            self.documents = documents
            print(f"{len(documents)}개의 Document 생성 완료")
            return True
            
        except Exception as e:
            print(f"데이터 로드 실패: {e}")
            return False
    
    def setup_embeddings(self):
        """임베딩 모델 설정"""
        try:
            # OpenAI 임베딩 시도
            print("OpenAI 임베딩 모델 설정 중...")
            self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
            print("OpenAI 임베딩 설정 완료")
            return True
        except Exception as e:
            print(f"OpenAI 임베딩 실패: {e}")
            try:
                print("HuggingFace 임베딩으로 대체...")
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                )
                print("HuggingFace 임베딩 설정 완료")
                return True
            except Exception as e2:
                print(f"임베딩 모델 설정 완전 실패: {e2}")
                return False
    
    def create_or_load_vectorstore(self):
        """벡터스토어 생성 또는 로드"""
        try:
            # 기존 벡터스토어 로드 시도
            if os.path.exists(self.vectorstore_path):
                try:
                    print("기존 벡터스토어 로드 시도...")
                    self.vectorstore = FAISS.load_local(
                        self.vectorstore_path, 
                        self.embedding_model,
                        allow_dangerous_deserialization=True
                    )
                    print("기존 벡터스토어 로드 성공")
                    return True
                except Exception as e:
                    print(f"기존 벡터스토어 로드 실패: {e}")
            
            # 새 벡터스토어 생성
            print("새 벡터스토어 생성 중...")
            self.vectorstore = FAISS.from_documents(
                documents=self.documents,
                embedding=self.embedding_model
            )
            
            # 저장
            self.vectorstore.save_local(self.vectorstore_path)
            print("벡터스토어 생성 및 저장 완료")
            return True
            
        except Exception as e:
            print(f"벡터스토어 생성 실패: {e}")
            return False
    
    def setup_llm(self):
        """LLM 설정 (선택사항)"""
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=500
            )
            print("LLM 설정 완료 - MultiQuery 기능 활성화")
            return True
        except Exception as e:
            print(f"LLM 설정 실패: {e}")
            print("MultiQuery 기능은 비활성화되지만 기본 검색은 정상 작동합니다.")
            self.llm = None
            return True  # LLM 없이도 계속 진행
    
    def setup_retrievers(self):
        """검색기들 설정"""
        try:
            # 기본 검색기 (임계값 낮춤)
            self.basic_retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 8}  # 임계값 제거하고 상위 8개만
            )
            print("기본 검색기 설정 완료")
            
            # MultiQuery 검색기 설정 (LLM이 있을 때만)
            if self.llm:
                # 커스텀 프롬프트 생성
                multi_query_prompt = PromptTemplate(
                    input_variables=["question"],
                    template="""당신은 학교 정보를 검색하는 전문가입니다. 
사용자의 질문을 바탕으로 관련 정보를 찾기 위한 다양한 검색 질문들을 생성해주세요.

원본 질문: {question}

이 질문과 관련된 정보를 찾기 위해 다음과 같은 관점에서 3-4개의 서로 다른 검색 질문을 만들어주세요:
1. 직접적인 질문
2. 관련 담당자나 부서 정보
3. 연락처나 위치 정보  
4. 관련 업무나 절차

각 질문은 개행으로 구분하여 작성해주세요."""
                )
                
                self.multi_query_retriever = MultiQueryRetriever.from_llm(
                    retriever=self.basic_retriever,
                    llm=self.llm,
                    prompt=multi_query_prompt
                )
                print("MultiQuery 검색기 설정 완료")
            else:
                print("LLM이 없어 MultiQuery 검색기를 설정할 수 없습니다.")
            
            return True
            
        except Exception as e:
            print(f"검색기 설정 실패: {e}")
            return False
    
    def initialize_system(self):
        """전체 시스템 초기화"""
        steps = [
            ("데이터 로드", self.load_and_prepare_documents),
            ("임베딩 설정", self.setup_embeddings),
            ("벡터스토어 생성", self.create_or_load_vectorstore),
            ("LLM 설정", self.setup_llm),
            ("검색기 설정", self.setup_retrievers)
        ]
        
        for step_name, step_func in steps:
            print(f"\n[{step_name}] 진행 중...")
            if not step_func():
                raise Exception(f"{step_name} 실패")
            print(f"[{step_name}] 완료")
        
        print("\n🎉 MultiQuery RAG 시스템 초기화 완료!")
    
    def search_documents(self, query: str, use_multi_query: bool = True) -> List[Document]:
        """문서 검색 (새 API 사용)"""
        try:
            if use_multi_query and self.multi_query_retriever:
                print(f"MultiQuery 검색 실행: '{query}'")
                docs = self.multi_query_retriever.invoke({"input": query})
                print(f"MultiQuery 검색 결과: {len(docs)}개 문서")
            else:
                print(f"기본 검색 실행: '{query}'")
                docs = self.basic_retriever.invoke(query)
                print(f"기본 검색 결과: {len(docs)}개 문서")
            
            return docs
        except Exception as e:
            print(f"검색 실패: {e}")
            # 폴백으로 직접 유사도 검색
            try:
                if self.vectorstore:
                    docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=5)
                    docs = [doc for doc, score in docs_and_scores if score < 1.0]  # 스코어 필터
                    print(f"폴백 검색 결과: {len(docs)}개 문서")
                    return docs
            except Exception as e2:
                print(f"폴백 검색도 실패: {e2}")
            return []
    
    def get_answer(self, query: str, use_multi_query: bool = True, max_results: int = 3) -> Dict[str, Any]:
        """질문에 대한 답변 생성"""
        if not query.strip():
            return {
                'results': [{'answer': '질문을 입력해주세요.', 'confidence': 0.0}],
                'method': 'none',
                'query': query
            }
        
        try:
            # 문서 검색
            docs = self.search_documents(query, use_multi_query)
            
            if not docs:
                return {
                    'results': [{'answer': '죄송합니다. 관련된 정보를 찾을 수 없습니다.', 'confidence': 0.0}],
                    'method': 'multi_query' if use_multi_query else 'basic',
                    'query': query
                }
            
            # 결과 정리
            results = []
            seen_answers = set()
            
            for i, doc in enumerate(docs[:max_results * 2]):
                try:
                    answer = doc.metadata.get('answer', doc.page_content)
                    question = doc.metadata.get('question', '')
                    
                    # 중복 제거
                    if answer in seen_answers:
                        continue
                    seen_answers.add(answer)
                    
                    # 신뢰도 계산 (순서 기반)
                    confidence = max(0.95 - i * 0.1, 0.2)
                    
                    results.append({
                        'answer': answer,
                        'confidence': confidence,
                        'question': question,
                        'source': doc.metadata.get('source', ''),
                        'preview': doc.page_content[:80] + "..."
                    })
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    print(f"결과 처리 오류: {e}")
                    continue
            
            # 최소 1개 결과 보장
            if not results and docs:
                first_doc = docs[0]
                results.append({
                    'answer': first_doc.metadata.get('answer', '답변을 찾을 수 없습니다.'),
                    'confidence': 0.5,
                    'question': first_doc.metadata.get('question', ''),
                    'source': first_doc.metadata.get('source', ''),
                    'preview': first_doc.page_content[:80] + "..."
                })
            
            return {
                'results': results,
                'method': 'multi_query' if use_multi_query else 'basic',
                'query': query,
                'total_docs': len(docs)
            }
            
        except Exception as e:
            print(f"답변 생성 실패: {e}")
            return {
                'results': [{'answer': f'오류 발생: {str(e)}', 'confidence': 0.0}],
                'method': 'error',
                'query': query
            }

# 전역 인스턴스
multiquery_rag = None

def initialize_rag():
    """RAG 시스템 초기화"""
    global multiquery_rag
    if multiquery_rag is None:
        multiquery_rag = MultiQueryRAGSystem()
    return multiquery_rag

def get_rag_answer(query: str, use_multi_query: bool = True) -> Dict[str, Any]:
    """답변 생성"""
    rag = initialize_rag()
    return rag.get_answer(query, use_multi_query=use_multi_query)

if __name__ == "__main__":
    print("=== MultiQuery RAG 시스템 테스트 ===")
    
    test_queries = [
        "학년업무",
        "노주영", 
        "교장선생님",
        "팩스",
        "8401",
        "1-1반",
        "체육선생님"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 테스트 질문: '{query}'")
        print("-" * 60)
        
        result = get_rag_answer(query, use_multi_query=True)
        
        print(f"검색 방법: {result['method']}")
        if 'total_docs' in result:
            print(f"찾은 문서 수: {result['total_docs']}개")
        
        for i, res in enumerate(result['results'][:2], 1):
            print(f"\n📋 답변 {i}:")
            print(f"  내용: {res['answer']}")
            print(f"  신뢰도: {res['confidence']:.2f}")
            if res.get('question'):
                print(f"  원본질문: {res['question']}")