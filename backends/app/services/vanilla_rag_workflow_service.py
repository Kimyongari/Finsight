from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain.schema.messages import HumanMessage, SystemMessage
from app.core.llm.llm import Midm
from app.core.VDB.weaviateVDB import VectorDB
from dotenv import load_dotenv
from app.schemas.langraph_states.state_models import vanilla_rag_state


class vanilla_rag_workflow:
    def __init__(self):
        load_dotenv()
        self.llm = Midm()
        self.vdb = VectorDB()
        self.vdb.set_collection('LegalDB')
        self.workflow = self.setup()

    def retriever(self, state: vanilla_rag_state, topk=4, alpha = 0.5) -> vanilla_rag_state:
        question = state.user_question
        try:
            retrieved_documents = self.vdb.query_hybrid(query = question, topk = topk, alpha = alpha)
            return {'retrieved_documents' : retrieved_documents}
        except Exception as e:
            print(f'retriever 과정 중 오류 발생 : {e} 빈 리스트를 return 합니다.')
            return {'retrieved_documents' : []}
    
    def generation(self, state: vanilla_rag_state) -> vanilla_rag_state:
        question = state.user_question
        retrieved_documents = state.retrieved_documents
        contexts = "\n\n".join([doc['text'] for doc in retrieved_documents])
        system_prompt = f"""
당신은 "전자금융감독규정"에 대한 내용을 설명하고 안내하는 전문 Assistant입니다.

- 사용자의 질문에 대해 반드시 [참고자료]의 내용만을 바탕으로 대답하세요.
- 문서에 명시되지 않은 질문에는 "문서에 명시되어 있지 않습니다."라고 답변하세요.
- 답변 마지막 줄에 출처를 아래 형식으로 명확히 표기하세요.

### 출력 형식 ###
## 사용자 질문
- 사용자 질문 핵심 정리

## 결론
- 질문에 대한 최종 요약 및 결론

## 답변에 대한 근거
- 질문에 대한 자세한 한국어 답변

## 출처
- 주어진 문서 중 답변에 활용된 법령 (「전자금융감독규정」 제(장 번호)장 (절 제목) 제(조 번호)조 형태로 작성)
※ 문서에 장 또는 절이 명시되지 않은 경우 생략 가능합니다. 예: 「전자금융감독규정」 제5조

### 참고자료 ###
{contexts}
"""            
        user_input = f"""
질문: {question}
답변: """
        
        answer = self.llm.call(system_prompt=system_prompt, user_input = user_input)

        return {'answer' : answer}
    def setup(self):
        workflow = StateGraph(vanilla_rag_state)
        workflow.add_node(self.retriever, "retriever")
        workflow.add_node(self.generation, "generation")
        workflow.add_edge(START, "retriever")
        workflow.add_edge("retriever", "generation")
        workflow.add_edge("generation", END)
        workflow = workflow.compile()        
        return workflow

    def run(self, question):
        input = vanilla_rag_state(user_question=question, retrieved_documents=[{}], answer='')
        try:
            result = self.workflow.invoke(input=input)
            response = {'success' : True, 'answer' : result['answer'], 'retrieved_documents' : result['retrieved_documents']}
            return response
        except Exception as e:
            response = {'success' : False, 'err_msg' : e}
            return response
