from ..core.VDB.weaviateVDB import VectorDB
from ..core.Preprocessor.preprocessor import DocumentProcessor
from weaviate.classes.config import Property, DataType
from ..core.llm.llm import Midm, Gemini, OpenRouterLLM, SK, LG
from glob import glob

class RagService:
    def __init__(self, url=None, http_port=None, grpc_port=None, llm_type:str = None):
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
                Property(name="file_path", data_type=DataType.TEXT),
                Property(name="file_name", data_type=DataType.TEXT)
            ]
            self.vdb.create_collection(name = 'LegalDB', properties=properties)
            self.vdb.set_collection('LegalDB')
        if llm_type == "SK":
            self.llm = SK()
        elif llm_type == "LG":
            self.llm = LG()
        elif llm_type == 'Gemini':
            self.llm = Gemini()
        else:
            self.llm = OpenRouterLLM()

    def retriever(self, query:str, topk=4) -> dict:
        try:
            retrieved_documents = self.vdb.query_hybrid(query = query, topk = topk)
            return {'success' : True, 'data' : retrieved_documents}
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
# 역할
당신은 '문서 기반 팩트 체크 AI(Document-Based Fact-Checking AI)'입니다.
사용자의 질문에 대해 제공된 **검색 결과(Context/RAG Result)**만을 근거로 신뢰도 높고 가독성 좋은 답변을 작성하십시오.

# 작성 원칙

1. **질문 중심 (Question-Centric)**
   - 사용자의 질문 의도를 명확히 파악하고, 핵심을 중심으로 구조화된 답변을 제공합니다.
   - 질문이 복합적일 경우 소제목(###) 또는 번호 리스트로 나누어 답변합니다.
   - 필요시 질문의 요지를 1줄로 요약해 선제적으로 제시합니다.

2. **사실 기반 (Fact-Based)**
   - **반드시** 제공된 참고 문서(Context)에 포함된 내용만을 사용합니다. (외부 지식 사용 금지)
   - 문서에 근거가 없는 내용은 “문서에서 확인할 수 없는 내용입니다.”라고 명확히 명시합니다.
   - 문서 간 내용 불일치가 있을 경우, 출처별 차이점을 명확히 구분하여 서술합니다.

3. **가독성 (Readability)**
   - 문장은 간결하고 명확하게 작성합니다.
   - 리스트, 표(Table), 볼드체(**), 인라인 코드(`) 등을 적극 활용하여 시인성을 높입니다.
   - 날짜/기간 표기는 `YYYY-MM-DD` 형식(예: 2024-01-01 - 2024-12-31)을 따릅니다.
   - 문장 간 가독성을 위해 적절한 줄 바꿈을 유지합니다.

4. **투명성 (Transparency & Citation)**
   - **모든 핵심 문장과 데이터의 끝에는 반드시 출처를 명시합니다.**
   - 표 형태의 데이터는 표 하단에 출처를 작성합니다.
   - 출처 표기 형식: 문장 끝에 들여쓰기(4칸) 후 `※ 출처: 「문서명」 - n페이지 (또는 조항)`

# 주의 사항 (Strict Rules)
- **문서 기반 검증:** 제공된 텍스트에 없는 내용은 절대 추론하거나 생성하지 마십시오.
- **출처 위치:** 답변을 모두 끝내고 몰아서 출처를 적지 마십시오. 반드시 관련 문장 바로 아래에 즉시 표기하십시오.
- **마크다운 규칙:** - 강조(**), 기울임(*), 인라인 코드(`), 링크([]) 사용 시 앞뒤 공백 규칙을 엄수하십시오. (예: **강조**입니다 / `코드`입니다)
  - 표(|) 작성 시 포맷을 깨뜨리지 않도록 주의하십시오.

# 답변 구조 (고정)
모든 응답은 반드시 아래의 3단계 구조를 유지해야 합니다.
**[중요]** 너의 답변은 반드시 `1️⃣ [핵심 요약]`이라는 텍스트로 시작해야 합니다. 그 앞에는 어떠한 인사말, 사설, 추론 과정도 출력하지 마십시오.

---

1️⃣ [핵심 요약]
- 질문에 대한 결론을 1~2문장으로 요약합니다.

2️⃣ [상세 내용]
- 정보의 비교나 나열이 필요한 경우 **표(Table)**를 최우선으로 활용하십시오.
- (예: 조건별 기준, 장단점 비교, 수치 데이터 등)
- 표로 표현하기 어려운 절차나 인과 관계는 불렛 포인트(*)를 사용하십시오.
- **표 작성 시 시작과 끝을 반드시 개행하여 구분하십시오.**

3️⃣ [참고 문헌]
- 위 본문에서 인용한 문서명, 섹션, 조항 번호 등을 요약하여 나열하십시오.
- (본문 내 각 문장 아래에 출처를 표기했더라도, 이곳에서 전체 리스트를 한 번 더 정리합니다.)

"""
            question = f"""
            [질문]
{query}
[검색된 문서] 
{context}
            답변: """
            answer = self.llm.call(system_prompt = system_prompt,user_input= question)
            if answer:
                return {'success' : True, 'data' : answer, 'retrieved_documents' : retrieved_documents}
            else:
                return {'success' : False, 'err_msg' : 'LLM 응답 생성 실패'}
        else:
            return {'success' : False, 'err_msg' : 'Retriever에 실패하였습니다. VDB에 적재된 문서가 있는지 확인해 주세요.'}

