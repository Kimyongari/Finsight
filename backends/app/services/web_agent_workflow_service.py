import asyncio
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from app.core.llm.llm import Midm
from app.core.web_search_agent.embedding import get_naver_embedding, cosine_similarity
from app.core.web_search_agent.web_search import WebSearchTool
from app.schemas.langraph_states.state_models import web_agent_state
from dotenv import load_dotenv


class web_agent_workflow:
    """LangGraph 기반 웹 에이전트 워크플로우.

    사용자 질문을 받아 웹 검색, 문서 필터링, 답변 생성까지의
    전체 프로세스를 상태 기반으로 관리합니다.
    """

    def __init__(self):
        load_dotenv()
        self.llm = Midm()
        self.workflow = self.setup()
        self.similarity_threshold = 0.48

    async def query_rewriter(self, state: web_agent_state) -> web_agent_state:
        """LLM을 사용하여 사용자 질문을 바탕으로 검색 쿼리를 생성합니다.

        Args:
            state: user_question을 포함한 워크플로우 상태

        Returns:
            generated_queries가 업데이트된 상태
        """
        question = state.user_question
        today = datetime.now().strftime("%Y-%m-%d")

        rewrite_prompt = (
            f"주어진 질문에 대해 답변하기 위해, 웹에서 검색할 검색어 4개를 생성하세요. "
            "절대 다른 설명을 추가하지 말고, 검색어만을 생성하세요. "
            "검색어를 작성 시, 되도록 최신 자료를 가져오도록 작성하세요. 오늘 날짜는 {today} 입니다."
            f"특히 질문에 '최근', '현재' 같은 단어가 포함된 경우에는 검색어에 {today[0:5]}를 포함하세요. "
        )

        try:
            rewritten_queries_str = await self.llm.acall(system_prompt=rewrite_prompt, user_input=f"질문: {question}")

            if not rewritten_queries_str or "LLM 호출에 실패했습니다." in rewritten_queries_str:
                print("[오류] LLM이 유효한 검색어를 생성하지 못했습니다.")
                return {"generated_queries": []}

            queries = [
                q.strip() for q in rewritten_queries_str.strip().split("\n") if q.strip()
            ]
            queries = queries[:4]  # 최대 4개로 제한

            print(f"[INFO] 생성된 검색어 {len(queries)}개: {queries}")
            return {"generated_queries": queries}

        except Exception as e:
            print(f"[오류] 검색어 생성 중 오류 발생: {e}")
            return {"generated_queries": []}

    async def document_collector(self, state: web_agent_state) -> web_agent_state:
        """생성된 검색 쿼리를 사용하여 웹에서 문서를 수집합니다.

        Args:
            state: generated_queries를 포함한 워크플로우 상태

        Returns:
            collected_documents가 업데이트된 상태
        """
        queries = state.generated_queries

        if not queries:
            print("[오류] 검색어가 없어 문서 수집을 건너뜁니다.")
            return {"collected_documents": []}

        print(f"[INFO] {len(queries)}개의 검색어로 각각 2개씩 병렬 검색을 실행합니다.")

        try:
            # 각 쿼리마다 2개씩 검색하여 총 8개 문서 수집
            tasks = [
                WebSearchTool(query=q, num_results=2).search_and_scrape()
                for q in queries
            ]
            results = await asyncio.gather(*tasks)

            # 결과를 하나의 리스트로 합치기
            all_documents = [doc for doc_list in results for doc in doc_list]

            print(f"[INFO] 총 {len(all_documents)}개의 문서를 수집했습니다.")
            return {"collected_documents": all_documents}

        except Exception as e:
            print(f"[오류] 문서 수집 중 오류 발생: {e}")
            return {"collected_documents": []}

    async def document_filter(self, state: web_agent_state) -> web_agent_state:
        """임베딩 유사도를 사용하여 상위 4개 문서를 필터링합니다.

        Args:
            state: user_question과 collected_documents를 포함한 워크플로우 상태

        Returns:
            filtered_documents와 similarity_score가 업데이트된 상태
        """
        question = state.user_question
        documents = state.collected_documents
        top_k = 4

        if not documents:
            print("[오류] 필터링할 문서가 없습니다.")
            return {"filtered_documents": [], "similarity_score": 0.0}

        print(f"[INFO] {len(documents)}개의 문서 중 유사도 상위 {top_k}개를 필터링합니다.")

        try:
            contents = [doc["content"] for doc in documents]

            # 질문의 임베딩 생성
            question_embedding = await get_naver_embedding(question)
            if not question_embedding:
                print("[오류] 질문 임베딩 생성 실패. 필터링을 건너뜁니다.")
                return {"filtered_documents": documents[:top_k], "similarity_score": 0.0}

            # 각 문서의 임베딩 생성
            doc_embeddings = await asyncio.gather(
                *[get_naver_embedding(c) for c in contents]
            )

            # 유사도 계산 및 정렬
            doc_sims = [
                (doc, cosine_similarity(question_embedding, emb))
                for doc, emb in zip(documents, doc_embeddings)
                if emb
            ]
            doc_sims.sort(key=lambda x: x[1], reverse=True)

            # 상위 K개 선택
            top_docs = [doc for doc, sim in doc_sims[:top_k]]
            top_similarities = [sim for doc, sim in doc_sims[:top_k]]
            avg_similarity = sum(top_similarities) / len(top_similarities) if top_similarities else 0.0

            print(f"[DEBUG] 상위 {len(top_docs)}개 문서의 평균 유사도: {avg_similarity:.4f}")
            return {"filtered_documents": top_docs, "similarity_score": avg_similarity}

        except Exception as e:
            print(f"[오류] 문서 필터링 중 예상치 못한 오류 발생: {e}")
            return {"filtered_documents": documents[:top_k], "similarity_score": 0.0}

    async def answer_generator(self, state: web_agent_state) -> web_agent_state:
        """유사도에 따라 분기 처리하여 최종 답변을 생성합니다.

        Args:
            state: 모든 필요한 데이터를 포함한 워크플로우 상태

        Returns:
            final_answer, answer_type, search_results가 업데이트된 상태
        """
        question = state.user_question
        filtered_docs = state.filtered_documents
        avg_similarity = state.similarity_score

        if not filtered_docs:
            return {
                "final_answer": "필터링 결과, 답변에 사용할 관련성 높은 문서를 찾지 못했습니다.",
                "answer_type": "오류",
                "search_results": []
            }

        print(f"[3/5] 유사도 평균 ({avg_similarity:.4f}) 기반 답변 방식 결정 (임계치: {self.similarity_threshold})")

        try:
            if avg_similarity >= self.similarity_threshold:
                # 고유사도: LLM이 문서를 참고해 통합 답변 생성
                print("[4/5] 고유사도 모드: 통합 분석 답변 생성")
                final_answer = await self._create_integrated_answer(question, filtered_docs)
                answer_type = "통합_분석"
            else:
                # 저유사도: 문서별 요약 제공
                print("[4/5] 저유사도 모드: 문서별 요약 제공")
                final_answer = await self._create_document_summary(question, filtered_docs)
                answer_type = "문서별_요약"

            print("[5/5] 최종 답변 완료")

            if not final_answer:
                return {
                    "final_answer": "최종 답변 생성에 실패했습니다.",
                    "answer_type": "오류",
                    "search_results": []
                }

            return {
                "final_answer": final_answer,
                "answer_type": answer_type,
                "search_results": filtered_docs
            }

        except Exception as e:
            print(f"[오류] 답변 생성 중 오류 발생: {e}")
            return {
                "final_answer": "답변 생성 중 오류가 발생했습니다.",
                "answer_type": "오류",
                "search_results": []
            }

    async def _create_integrated_answer(self, question: str, documents: list[dict]) -> str:
        """문서들을 종합적으로 분석하여 통합 답변을 생성합니다."""
        context = self._format_context(documents)

        if not context:
            return "컨텍스트 생성에 실패했습니다."

        answer_prompt = (
            "당신은 전문 분석가입니다. 주어진 문서들을 종합적으로 분석하여 "
            "사용자의 질문에 대해 상세하고 체계적인 답변을 Markdown 형식으로 작성해주세요. "
            "답변은 다음 구조를 따라주세요:\n"
            "1. ## 요약\n"
            "2. ## 주요 내용\n"
            "3. ## 상세 분석\n"
            "4. ## 결론\n\n"
            "중요: 각 섹션 제목은 정확히 '## 제목' 형태로 작성하세요. '#'이나 '# ##' 같은 형태는 사용하지 마세요. "
            "참고 자료 섹션은 생성하지 마세요. 각 섹션은 구체적이고 근거있는 내용으로 작성해주세요."
        )

        answer_content = (
            f"질문: {question}\n\nContext:\n{context}\n\n"
            "위 문서들을 종합적으로 분석하여 질문에 대해 체계적으로 답변해주세요."
        )

        # LLM으로 답변 생성
        llm_answer = await self.llm.acall(system_prompt=answer_prompt, user_input=answer_content)

        # 실제 사용된 문서들로 참고 자료 섹션 직접 생성
        reference_section = "\n\n## 참고 자료\n\n"
        for idx, doc in enumerate(documents, 1):
            reference_section += f"{idx}. **{doc.get('title', 'N/A')}** ({doc.get('link', 'N/A')}): {doc.get('snippet', 'N/A')[:100]}{'...' if len(doc.get('snippet', '')) > 100 else ''}\n\n"

        return llm_answer + reference_section

    async def _create_document_summary(self, question: str, documents: list[dict]) -> str:
        """문서별로 요약을 생성하여 Markdown 형태로 반환합니다."""
        summary_parts = ["## 문서별 요약\n\n다음은 질문하신 내용에 대한 관련 문서 목록입니다.\n"]

        for idx, doc in enumerate(documents, 1):
            summary_prompt = (
                "주어진 문서 내용의 내용을 간략하게 요약해주세요. "
                "답변은 3문장으로 간결하게 작성하세요."
            )
            summary_content = (
                f"질문: {question}\n\n"
                f"문서 제목: {doc.get('title', 'N/A')}\n"
                f"문서 내용: {doc.get('content', 'N/A')[:1000]}..."
            )
            summary = await self.llm.acall(system_prompt=summary_prompt, user_input=summary_content)

            summary_parts.append(
                f"### {idx}. {doc.get('title', 'N/A')}\n"
                f"- **내용 요약**: {summary if summary else doc.get('snippet', 'N/A')}\n"
                f"- **출처**: [{doc.get('title', 'N/A')}]({doc.get('link', 'N/A')})\n"
            )

        return "\n".join(summary_parts)

    def _format_context(self, documents: list[dict]) -> str:
        """문서 목록을 LLM에 전달할 최종 컨텍스트 문자열로 포맷합니다."""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"결과 {i}: {doc['title']}\n"
                f"출처: {doc['link']}\n"
                f"요약: {doc['snippet']}\n"
                f"전문: {doc['content']}"
            )
        return "\n\n".join(context_parts)

    def setup(self):
        """LangGraph 노드와 엣지를 정의하여 워크플로우를 구성합니다.

        Returns:
            컴파일된 LangGraph 워크플로우
        """
        workflow = StateGraph(web_agent_state)

        # 노드 추가
        workflow.add_node("query_rewriter", self.query_rewriter)
        workflow.add_node("document_collector", self.document_collector)
        workflow.add_node("document_filter", self.document_filter)
        workflow.add_node("answer_generator", self.answer_generator)

        # 엣지 연결
        workflow.add_edge(START, "query_rewriter")
        workflow.add_edge("query_rewriter", "document_collector")
        workflow.add_edge("document_collector", "document_filter")
        workflow.add_edge("document_filter", "answer_generator")
        workflow.add_edge("answer_generator", END)

        return workflow.compile()

    async def run(self, question: str) -> dict:
        """웹 에이전트 워크플로우를 실행합니다.

        Args:
            question: 사용자 질문

        Returns:
            성공 여부, 답변, 검색 결과를 포함한 딕셔너리
        """
        print(f"\n--- 웹 검색 에이전트 시작 ---")

        input_state = web_agent_state(
            user_question=question,
            generated_queries=[],
            collected_documents=[],
            filtered_documents=[],
            similarity_score=0.0,
            final_answer="",
            answer_type="",
            search_results=[]
        )

        try:
            result = await self.workflow.ainvoke(input=input_state)

            return {
                "success": True,
                "answer": result["final_answer"],
                "search_results": result["search_results"],
                "answer_type": result["answer_type"],
                "similarity_score": result["similarity_score"],
                "similarity_threshold": self.similarity_threshold
            }

        except Exception as e:
            print(f"[오류] 워크플로우 실행 중 오류 발생: {e}")
            return {
                "success": False,
                "answer": f"워크플로우 실행 중 오류가 발생했습니다: {str(e)}",
                "search_results": []
            }