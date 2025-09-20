from langgraph.graph import StateGraph, START, END
from app.core.llm.llm import Midm
from app.core.VDB.weaviateVDB import VectorDB
from dotenv import load_dotenv
from app.schemas.langraph_states.state_models import advanced_rag_state

class advanced_rag_workflow:
    def __init__(self):
        load_dotenv()
        self.llm = Midm()
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
                    print(name,'에 해당하는 참조 조문이 vdb 내에 없습니다.')
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
당신은 "전자금융감독규정"에 대한 내용을 설명하고 안내하는 전문 Assistant입니다.

- 사용자의 질문에 대해 반드시 [참고자료]와 [참조된 조문]의 내용만을 바탕으로 대답하세요.
- 문서에 명시되지 않은 질문에는 "문서에 명시되어 있지 않습니다."라고 답변하세요.
- 답변 마지막 줄에 출처를 아래 형식으로 명확히 표기하세요.
- 만약 참조된 조문이 있다면 참고자료 뿐만 아니라 참조된 조문까지 활용하여 자세한 설명을 제공하세요.

### 출력 형식 ###
## 사용자 질문
- 사용자 질문 핵심 정리

## 답변에 대한 근거
- 질문에 대한 자세한 한국어 답변

## 결론
- 질문에 대한 최종 요약 및 결론

## 출처
- 주어진 문서 중 답변에 활용된 법령 (예시: 「전자금융감독규정」 제(장 번호)장 (절 제목) 제(조 번호)조 형태로 작성)
※ 문서에 장 또는 절이 명시되지 않은 경우 생략 가능합니다. 예: 「전자금융감독규정」 제5조

### 참고자료 ###
{contexts1}

### 참조된 조문 ###
{contexts2}
"""            
        user_input = f"""
질문: {question}
답변: """
        
        answer = self.llm.call(system_prompt=system_prompt, user_input = user_input)

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
