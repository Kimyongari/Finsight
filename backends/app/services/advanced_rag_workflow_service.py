from langgraph.graph import StateGraph, START, END
from app.core.llm.llm import Midm, Gemini, SK, LG, OpenRouterLLM
from app.core.VDB.weaviateVDB import VectorDB
from dotenv import load_dotenv
from app.schemas.langraph_states.state_models import advanced_rag_state

class advanced_rag_workflow:
    def __init__(self, llm_type:str = None):
        load_dotenv()
        if llm_type == "SK":
            self.llm = SK()
        elif llm_type == "LG":
            self.llm = LG()
        elif llm_type == 'Gemini':
            self.llm = Gemini()
        else:
            self.llm = OpenRouterLLM()
        self.vdb = VectorDB()
        self.vdb.set_collection('LegalDB')
        self.workflow = self.setup()

    def retriever(self, state: advanced_rag_state, topk=4, alpha = 0.5) -> advanced_rag_state:
        question = state.user_question
        retrieved_documents = self.vdb.query_hybrid(query = question, topk = topk, alpha = alpha)
        return {'retrieved_documents' : retrieved_documents}
    
    def reference_search(self, state: advanced_rag_state) -> advanced_rag_state:
        retrieved_documents = state.retrieved_documents
        context_list = [doc['text'] for doc in retrieved_documents]
        contexts = "\n\n".join(context_list)
        system_prompt = f"""
당신은 법령 분석 전문가입니다.
사용자가 제공한 문서에서 다른 법령의 참조 조항을 정확하게 찾아냅니다.
당신의 역할은 이 문서에서 언급된 참조 조항의 법령 이름과 그에 해당하는 조 정보를 모두 추출하여 출력하는 것입니다.

## 지침

- 문서를 꼼꼼히 분석하여 장, 절, 조 등으로 표시된 참조를 모두 찾습니다.
- 참조된 내용은 다음 형식으로 정확히 출력합니다:
- "법령명 제X조(조항이름)" 의 형식을 반드시 준수하세요.
- 여러 개의 참조가 있을 경우, 각 항목을 쉼표(,)로 구분하여 출력합니다.
- 중복된 참조가 있을 경우 한 번만 출력합니다.
- 참조된 조의 이름이 있다면 반드시 괄호까지 포함하여 작성하세요.
- 다른 말은 절대 하지 않고 불필요한 설명, 문장부호, 기타 문구 없이 참조 법령 조항만 출력합니다.

## 예시 출력
전자금융감독규정 제14조의2(클라우드 컴퓨팅서비스 이용절차 등),개인정보보호법 제7조의11(위원의 제척ㆍ기피ㆍ회피),전자금융거래법 시행령 제2조의4(클라우드 컴퓨팅서비스의 보고)

## 주의 사항
- 지침을 반드시 준수하세요.
- 다른 말은 절대 하지 않고 참조 법령 조항만 출력 형식에 맞게 출력하세요.
"""
        user_input = f"제공된 문서 : {contexts}"
        result = self.llm.call(system_prompt=system_prompt, user_input=user_input)
        try:
            references = []
            result = [i.replace(' ','') for i in result.split(',')]
            for name in result:
                reference = self.vdb.query_hybrid_with_filter(name = name)
                if reference:
                    if reference['text'] not in context_list:
                        references.append(reference)
                        print(name,'에 해당하는 참조 조문이 vdb 내에 존재하여 참조 조문 목록에 추가하였습니다.')
                    else:
                        print(name,'에 해당하는 참조 조문이 vdb 내에 존재하여 참조 조문 목록에 추가하려 했으나 이미 검색된 문서에 존재하여 스킵합니다.')
                else:
                    pass
            return {'references' : references}
            
        except Exception as e:
            print(f'참조조문 파싱오류 발생. 오류 : {e} / 검색 결과:', result)
            return {'references' : []}
        
    def generation(self, state: advanced_rag_state) -> advanced_rag_state:
        question = state.user_question
        retrieved_documents = state.retrieved_documents
        references = state.references
        contexts1 = "\n\n".join([doc['text'] for doc in retrieved_documents])
        contexts2 = "\n\n".join([doc['text'] for doc in references])
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
        {question}
        
        [검색된 문서] 
        {contexts1}
        
        [참조조문]
        {contexts2}
        답변: 
        """
        
        answer = self.llm.call(system_prompt=system_prompt, user_input = question)

        return {'answer' : answer}
    
    def setup(self):
        workflow = StateGraph(advanced_rag_state)
        workflow.add_node(self.retriever, "retriever")
        workflow.add_node(self.reference_search, "reference_search")
        workflow.add_node(self.generation, "generation")
        workflow.add_edge(START, "retriever")
        workflow.add_edge("retriever", "reference_search")
        workflow.add_edge("reference_search", "generation")
        workflow.add_edge("generation", END)
        workflow = workflow.compile()        
        return workflow

    def run(self, question):
        input = advanced_rag_state(user_question=question, retrieved_documents=[{}], answer='', references = [{}])
        try:
            result = self.workflow.invoke(input=input)
            response = {'success' : True, 'answer' : result['answer'], 'retrieved_documents' : result['retrieved_documents'], 'references' : result['references']}
            return response
        except Exception as e:
            response = {'success' : False, 'err_msg' : e}
            return response
