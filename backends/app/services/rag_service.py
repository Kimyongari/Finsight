from ..core.VDB.weaviateVDB import VectorDB
from ..core.Preprocessor.preprocessor import DocumentProcessor
from weaviate.classes.config import Property, DataType
from ..core.llm.llm import Midm
from glob import glob

class RagService:
    def __init__(self, url=None, http_port=None, grpc_port=None):
        self.vdb = VectorDB(url=url, http_port=http_port, grpc_port=grpc_port)
        if 'LegalDB' in self.vdb.show_collection():
            self.vdb.set_collection('LegalDB')
        else:
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="n_char", data_type=DataType.INT),
                Property(name="n_word", data_type=DataType.INT),
                Property(name="i_page", data_type=DataType.INT),
                Property(name="i_chunk_on_page", data_type=DataType.INT),
                Property(name="n_chunk_of_page", data_type=DataType.INT),
                Property(name="i_chunk_on_doc", data_type=DataType.INT),
                Property(name="n_chunk_of_doc", data_type=DataType.INT),
                Property(name="n_page", data_type=DataType.INT),
                Property(name="name", data_type=DataType.TEXT),
                Property(name="file_path", data_type=DataType.TEXT)
            ]
            self.vdb.create_collection(name = 'LegalDB', properties=properties)
            self.vdb.set_collection('LegalDB')
        self.llm = Midm()

    def retriever(self, query:str, topk=4) -> dict:
        try:
            retrieved_documents = self.vdb.query_hybrid(query = query, topk = topk)
            return {'success' : True, 'data' : retrieved_documents}
        except Exception as e:
            return {'success' : False, 'err_msg' : str(e)}
    
    def show_collections(self):
        return self.vdb.show_collection()
    
    def set_collection(self, name:str):
        try:
            self.vdb.set_collection(name)
            return {'success': True}
        except Exception as e:
            return {'success' : False, 'err_msg' : str(e)}

    def generate_answer(self, query:str) -> dict:
        result = self.retriever(query = query, topk = 4)
        print(result)
        if result['success']:
            retrieved_documents = result['data']
            context = "\n\n".join([doc['text'] for doc in retrieved_documents])
            self.context = context
            system_prompt = f"""
당신은 "전자금융감독규정"에 대한 내용을 설명하고 안내하는 전문 Assistant입니다.

- 사용자의 질문에 대해 반드시 [참고자료]의 내용만을 바탕으로 대답하세요.
- 문서에 명시되지 않은 질문에는 "문서에 명시되어 있지 않습니다."라고 답변하세요.
- 답변 마지막 줄에 출처를 아래 형식으로 명확히 표기하세요.

### 출력 형식 ###
## 사용자 질문
- 사용자 질문 핵심 정리

## 답변에 대한 근거
- 질문에 대한 자세한 한국어 답변

## 결론
- 질문에 대한 최종 요약 및 결론

## 출처
- 주어진 문서 중 답변에 활용된 법령 (「전자금융감독규정」 제(장 번호)장 (절 제목) 제(조 번호)조 형태로 작성)
※ 문서에 장 또는 절이 명시되지 않은 경우 생략 가능합니다. 예: 「전자금융감독규정」 제5조

### 참고자료 ###
{context}
"""            
            question = f"""
질문: {query}
답변: """
            answer = self.llm.call(system_prompt = system_prompt,user_input= question)
            if answer:
                return {'success' : True, 'data' : answer, 'retrieved_documents' : retrieved_documents}
            else:
                return {'success' : False, 'err_msg' : 'LLM 응답 생성 실패'}
        else:
            return {'success' : False, 'err_msg' : 'Retriever에 실패하였습니다. VDB에 적재된 문서가 있는지 확인해 주세요.'}

    def initialize(self):
        try:
            paths = glob('./pdfs/*.pdf')
            files = [path.split('/')[-1] for path in paths]
            self.vdb.reset()
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="n_char", data_type=DataType.INT),
                Property(name="n_word", data_type=DataType.INT),
                Property(name="i_page", data_type=DataType.INT),
                Property(name="i_chunk_on_page", data_type=DataType.INT),
                Property(name="n_chunk_of_page", data_type=DataType.INT),
                Property(name="i_chunk_on_doc", data_type=DataType.INT),
                Property(name="n_chunk_of_doc", data_type=DataType.INT),
                Property(name="n_page", data_type=DataType.INT),
                Property(name="name", data_type=DataType.TEXT),
                Property(name="file_path", data_type=DataType.TEXT)
            ]
            self.vdb.create_collection(name = 'LegalDB', properties=properties)
            self.vdb.set_collection('LegalDB')
            processor = DocumentProcessor()
            all_chunks = []
            for path in paths:
                chunks = processor.preprocess(file_path = path)
                all_chunks += chunks
            objects = [{'text' : chunk.text,
                        'n_char' : chunk.n_char,
                        'n_word' : chunk.n_word,
                        'i_page' : chunk.i_page,
                        'i_chunk_on_page' : chunk.i_chunk_on_page,
                        'n_chunk_of_page' : chunk.n_chunk_of_page,
                        'i_chunk_on_doc' : chunk.i_chunk_on_doc,
                        'n_chunk_of_doc' : chunk.n_chunk_of_doc,
                        'n_page' : chunk.n_page,
                        'name' : chunk.name,
                        'file_path' : chunk.file_path } for chunk in all_chunks]
            self.vdb.add_objects(objects = objects)
            return {'success' : True, 'files' : paths}
        
        except Exception as e:
            print('Error during initialization:', str(e))
            return {'success' : False, 'err_msg' : str(e)}
        
    def register(self, file_name):
        path = f'./pdfs/{file_name}'
        try:
            processor = DocumentProcessor()
            chunks = processor.preprocess(file_path = path)
            if self.vdb.check(name = 'LegalDB'):
                objects = [{'text' : chunk.text,
                            'n_char' : chunk.n_char,
                            'n_word' : chunk.n_word,
                            'i_page' : chunk.i_page,
                            'i_chunk_on_page' : chunk.i_chunk_on_page,
                            'n_chunk_of_page' : chunk.n_chunk_of_page,
                            'i_chunk_on_doc' : chunk.i_chunk_on_doc,
                            'n_chunk_of_doc' : chunk.n_chunk_of_doc,
                            'n_page' : chunk.n_page,
                            'name' : chunk.name,
                            'file_path' : chunk.file_path } for chunk in chunks]
                self.vdb.add_objects(objects = objects)
                return {'success' : True}
            else:
                return {'success' : False}
    
        except Exception as e:
            print('Error during initialization:', str(e))
            return {'success' : False, 'err_msg' : str(e)}
        
    def reset(self):
        try:        
            self.vdb.reset()
            return {'success': True}
        except Exception as e:
            return {'success' : False, 'err_msg' : f'reset에 실패하였습니다. 오류 : {e}'}
        
    