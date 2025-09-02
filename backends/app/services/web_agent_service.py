import asyncio
from datetime import datetime

from app.core.llm.llm import Midm
from app.core.web_search_agent.embedding import get_naver_embedding, cosine_similarity
from app.core.web_search_agent.web_search import WebSearchTool


class WebAgentService:
    def __init__(self):
        self.llm = Midm()

    async def _filter_documents_by_similarity(
        self, question: str, documents: list[dict], top_k: int = 3
    ) -> list[dict]:
        """질문과 문서 목록의 유사도를 계산하여 상위 K개의 문서를 반환합니다."""
        print(f"[INFO] {len(documents)}개의 문서 중 유사도 상위 {top_k}개를 필터링합니다.")
        contents = [doc["content"] for doc in documents]
        try:
            question_embedding = await get_naver_embedding(question)
            if not question_embedding:
                print("[오류] 질문 임베딩 생성 실패. 필터링을 건너뜁니다.")
                return documents[:top_k]
            doc_embeddings = await asyncio.gather(
                *[get_naver_embedding(c) for c in contents]
            )
            doc_sims = [
                (doc, cosine_similarity(question_embedding, emb))
                for doc, emb in zip(documents, doc_embeddings)
                if emb
            ]
            doc_sims.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, sim in doc_sims[:top_k]]
        except Exception as e:
            print(f"[오류] 문서 필터링 중 예상치 못한 오류 발생: {e}")
            return documents[:top_k]

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

    async def _rewrite_and_search(
        self, question: str, num_results_per_query: int = 1
    ) -> list[dict]:
        """LLM으로 검색어를 재작성하고 다시 검색하여 문서 목록을 반환합니다."""
        print("[INFO] 검색어 재작성 및 추가 검색을 시작합니다.")
        today = datetime.now().strftime("%Y-%m-%d")
        rewrite_prompt = (
            "주어진 질문에 대해 답변하기 위해, 웹에서 검색할 검색어 5개를 생성하세요. "
            "절대 다른 설명을 추가하지 말고, 검색어 5개만을 생성하세요. "
            f"검색어를 작성 시, 반드시 최신 자료를 가져오도록 작성하세요. 오늘 날짜: {today}"
        )
        rewritten_queries_str = await self.llm.acall(rewrite_prompt, f"질문: {question}")
        if not rewritten_queries_str or "LLM 호출에 실패했습니다." in rewritten_queries_str:
             print("[오류] LLM이 유효한 검색어를 생성하지 못했습니다.")
             return []

        queries = [
            q.strip() for q in rewritten_queries_str.strip().split("\n") if q.strip()
        ]
        print(f"[INFO] 재작성된 검색어: {queries}")
        if not queries:
            print("[오류] LLM이 유효한 검색어를 생성하지 못했습니다.")
            return []
        print(f"[INFO] {len(queries)}개의 재작성된 검색어로 비동기 검색을 실행합니다.")
        tasks = [
            WebSearchTool(query=q, num_results=num_results_per_query).search_and_scrape()
            for q in queries
        ]
        results = await asyncio.gather(*tasks)
        return [doc for doc_list in results for doc in doc_list]

    async def search(self, question: str) -> str:
        """웹 검색 에이전트의 전체 워크플로우를 실행합니다."""
        print(f"\n--- 웹 검색 에이전트 시작 ---")

        # 1단계: 초기 검색
        print("[1/5] 초기 검색 및 스크래핑")
        documents = await WebSearchTool(query=question, num_results=5).search_and_scrape()
        if not documents:
            return "초기 검색 결과, 관련 문서를 찾지 못했습니다."

        # 2단계: 초기 컨텍스트 필터링
        print("[2/5] 초기 검색 결과 필터링")
        filtered_docs = await self._filter_documents_by_similarity(question, documents, top_k=3)
        context = self._format_context(filtered_docs)

        if not context:
            return "초기 컨텍스트 생성에 실패했습니다."

        # 3단계: 컨텍스트 유효성 검사
        print("[3/5] 컨텍스트 유효성 검사")
        validation_prompt = (
            "주어진 context가 사용자의 질문에 답변하기에 충분한 정보를 담고 있는지 판단하세요. "
            "충분하다면 'yes', 그렇지 않다면 'no'라고만 대답하세요."
        )
        is_context_sufficient = await self.llm.acall(
            validation_prompt, f"질문: {question}\n\nContext:\n{context}"
        )
        print(f"[INFO] 컨텍스트 유효성 검사 결과: {is_context_sufficient}")

        # 4단계: 컨텍스트가 불충분할 경우 재검색
        if is_context_sufficient and "yes" not in is_context_sufficient.lower():
            print("[4/5] 추가 검색 및 필터링")
            rewritten_docs = await self._rewrite_and_search(question, num_results_per_query=1)
            if not rewritten_docs:
                return "재검색 결과, 관련 문서를 찾지 못해 답변을 생성할 수 없습니다."

            final_docs = await self._filter_documents_by_similarity(
                question, rewritten_docs, top_k=3
            )
            context = self._format_context(final_docs)
        else:
            print("[4/5] 초기 컨텍스트가 충분하여 답변 생성으로 넘어갑니다.")

        if not context:
            return "필터링 결과, 답변에 사용할 관련성 높은 문서를 찾지 못했습니다."

        # 5단계: 최종 답변 생성
        print("[5/5] 최종 답변 생성")
        answer_prompt = (
            "당신은 주어진 context 정보를 바탕으로 사용자의 질문에 대해 "
            "친절하고 상세하게 답변하는 AI 어시스턴트입니다."
        )
        answer_content = (
            f"질문: {question}\n\nContext:\n{context}\n\n"
            "위 Context를 바탕으로 질문에 대해 답변해주세요."
        )
        final_answer = await self.llm.acall(answer_prompt, answer_content)

        return final_answer if final_answer else "최종 답변 생성에 실패했습니다."
