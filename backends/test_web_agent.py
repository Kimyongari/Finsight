import asyncio
import sys
import os
import csv
from datetime import datetime
import requests
import urllib.parse
import httpx
from bs4 import BeautifulSoup
import random

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.web_agent_workflow_service import web_agent_workflow

# test_web_agent.py 전용 WebSearchTool 클래스 (SearchAPI 사용)
class WebSearchTool:
    """테스트용 WebSearchTool - SearchAPI 사용"""

    # User-Agent 풀
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    ]

    def __init__(self, query: str, num_results: int = 5):
        self.query = query
        self.num_results = num_results
        self.api_key = 'q4wGQfPGh3kPd1AqsHBp7EKn'

    async def _fetch_search_results(self) -> list:
        """SearchAPI를 사용하여 검색 결과를 가져옵니다."""
        encoded_query = urllib.parse.quote(self.query)
        url = f"https://www.searchapi.io/api/v1/search?engine=google&gl=kr&hl=ko&q={encoded_query}&api_key={self.api_key}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("organic_results", [])
        except Exception as e:
            print(f"[오류] SearchAPI 요청 중 오류 발생: {e}")
            return []

    async def _scrape_page(self, url: str) -> str:
        """주어진 URL의 웹 페이지를 스크래핑하여 본문 텍스트를 추출합니다."""
        try:
            user_agent = random.choice(self.USER_AGENTS)
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            async with httpx.AsyncClient(
                follow_redirects=True,
                verify=False,
                timeout=15.0
            ) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            selectors = ["#article_body", "#dic_area", "#newsct_article", ".article_view", "#article-view-content-div", "#contents", ".content"]
            content_html = None
            for selector in selectors:
                content_html = soup.select_one(selector)
                if content_html:
                    break

            text_content = content_html.get_text() if content_html else soup.get_text()

            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = "\n".join(chunk for chunk in chunks if chunk)[:4000]
            return content
        except Exception as e:
            print(f"[오류] 스크래핑 실패: {url}, 오류: {e}")
            return ""

    async def search_and_scrape(self) -> list[dict]:
        """SearchAPI로 검색 후 각 결과 페이지를 스크래핑하여 문서 목록을 반환합니다."""
        search_results = await self._fetch_search_results()

        if not search_results:
            return []

        # 필요한 개수만큼 결과 제한
        search_results = search_results[:self.num_results + 5]  # 스크래핑 실패 대비 여유분

        tasks = [self._scrape_page(r.get("link", "")) for r in search_results if r.get("link")]
        scraped_contents = await asyncio.gather(*tasks)

        documents = []
        for r, c in zip(search_results, scraped_contents):
            if c and r.get("link"):
                documents.append({
                    "title": r.get("title", ""),
                    "link": r.get("link"),
                    "snippet": r.get("snippet", ""),
                    "publish_date": r.get("date", ""),
                    "content": c,
                })
            if len(documents) == self.num_results:
                break

        return documents

# 정량 평가용 20개 질문
EVALUATION_QUESTIONS = [ # 질문 리스트 변경
    "2025년부터 시행되는 망분리 규제 완화 조치가 국내 핀테크 기업의 클라우드 기반 서비스 개발 및 해외 시장 진출 전략에 어떤 기회와 위협 요인을 제공할 것으로 보십니까?",
    "제4인터넷전문은행의 출범이 기존 인터넷은행(카카오뱅크, 케이뱅크, 토스뱅크)의 비즈니스 모델, 특히 중저신용자 대출 시장에 미칠 파급효과를 예측해 주세요.",
    "마이데이터 2.0 사업이 기존 금융사의 데이터 활용 전략에 어떤 변화를 요구하며, 비금융 데이터와의 결합을 통한 초개인화 서비스의 성공 요건은 무엇이라고 보나요?",
    "코로나19 이후 급증한 개인 투자자들의 해외주식 직접투자 트렌드가 국내 증권사의 리테일 브로커리지 수익 모델 다변화에 주는 시사점은 무엇인가요?",
    "'영끌', '빚투'로 대표되는 한국의 높은 가계부채 수준이 향후 금융 시스템 안정성에 미치는 잠재적 리스크와, 이를 관리하기 위한 정책적 대안을 제시해 주세요.",
    "한국의 독특한 '전세' 제도가 금리 변동기에 주택 시장 및 가계 금융에 미치는 영향과, 시스템 리스크 관점에서 보완해야 할 점은 무엇이라고 생각하십니까?",
    "청년도약계좌와 같은 정책금융상품이 청년층의 실질적인 자산 형성에 기여하는 효과와, 시장 원리에 기반한 장기 투자 문화 정착에 미치는 한계점을 논해주세요.",
]

def select_llm_model():
    """LLM 모델을 선택하는 함수"""
    print("=== LLM 모델 선택 ===")
    print("1. Midm (기본값)")
    print("2. SK")
    print("3. LG")
    print()

    while True:
        try:
            choice = input("사용할 LLM 모델을 선택하세요 (1-3): ").strip()

            if choice == "1" or choice == "":
                return "Midm"
            elif choice == "2":
                return "SK"
            elif choice == "3":
                return "LG"
            else:
                print("올바른 번호를 입력해주세요 (1-3)")
        except KeyboardInterrupt:
            print("\n프로그램이 중단되었습니다.")
            exit()


def select_mode():
    """실행 모드를 선택하는 함수"""
    print("\n=== 모드 선택 ===")
    print("1. 검색 테스트 (대화형)")
    print("2. 정량 평가 실시")
    print()

    while True:
        try:
            choice = input("실행 모드를 선택하세요 (1-2): ").strip()

            if choice == "1":
                return "search_test"
            elif choice == "2":
                return "quantitative_evaluation"
            else:
                print("올바른 번호를 입력해주세요 (1-2)")
        except KeyboardInterrupt:
            print("\n프로그램이 중단되었습니다.")
            exit()



async def quantitative_evaluation(selected_llm):
    """정량 평가를 수행하는 함수 - 5개씩 배치 처리로 rate limiting 방지"""
    print(f"\n=== 정량 평가 실시 ({selected_llm} 모델) ===")
    print(f"총 {len(EVALUATION_QUESTIONS)}개의 질문을 처리합니다.")
    print("Rate limiting 방지를 위해 5개씩 배치 처리하며, 배치 간 30초 대기합니다.")
    print("=" * 60)

    # 웹 에이전트 워크플로우 인스턴스 생성
    try:
        web_agent = web_agent_workflow(llm_type=selected_llm, web_search_tool_class=WebSearchTool)
        print("✅ 워크플로우 초기화 성공")
    except Exception as e:
        print(f"❌ 워크플로우 초기화 실패: {e}")
        return

    results = []
    batch_size = 10  # 5개에서 10개로 증가 (재시도 로직 덕분에 더 공격적으로 가능)
    total_questions = len(EVALUATION_QUESTIONS)

    # 질문들을 배치로 나누기
    for batch_start in range(0, total_questions, batch_size):
        batch_end = min(batch_start + batch_size, total_questions)
        batch_questions = EVALUATION_QUESTIONS[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (total_questions + batch_size - 1) // batch_size

        print(f"\n🔄 배치 {batch_num}/{total_batches} 처리 중 (질문 {batch_start + 1}-{batch_end}개)")

        # 현재 배치의 질문들 처리
        for i, question in enumerate(batch_questions):
            idx = batch_start + i + 1
            print(f"\n[{idx}/{total_questions}] 처리 중: {question[:50]}...")

            try:
                # 1. query_rewriter 실행
                from app.schemas.langraph_states.state_models import web_agent_state

                state = web_agent_state(
                    user_question=question,
                    generated_queries=[],
                    collected_documents=[],
                    filtered_documents=[],
                    similarity_score=0.0,
                    final_answer="",
                    answer_type="",
                    search_results=[]
                )

                # 단계별 실행
                state_after_rewrite = await web_agent.query_rewriter(state)
                if not state_after_rewrite.get("generated_queries"):
                    print(f"   ❌ 쿼리 생성 실패")
                    results.append({
                        "question_num": idx,
                        "question": question,
                        "queries": "",
                        "similarity": 0.0
                    })
                    continue

                # 상태 업데이트
                state = web_agent_state(
                    user_question=question,
                    generated_queries=state_after_rewrite["generated_queries"],
                    collected_documents=[],
                    filtered_documents=[],
                    similarity_score=0.0,
                    final_answer="",
                    answer_type="",
                    search_results=[]
                )

                # 2. document_collector 실행
                state_after_collect = await web_agent.document_collector(state)
                if not state_after_collect.get("collected_documents"):
                    print(f"   ❌ 문서 수집 실패")
                    results.append({
                        "question_num": idx,
                        "question": question,
                        "queries": ", ".join(state_after_rewrite["generated_queries"]),
                        "similarity": 0.0
                    })
                    continue

                # 상태 업데이트
                state = web_agent_state(
                    user_question=question,
                    generated_queries=state_after_rewrite["generated_queries"],
                    collected_documents=state_after_collect["collected_documents"],
                    filtered_documents=[],
                    similarity_score=0.0,
                    final_answer="",
                    answer_type="",
                    search_results=[]
                )

                # 3. document_filter 실행 (재시도 로직 포함)
                state_after_filter = await web_agent.document_filter(state)
                similarity_score = state_after_filter.get("similarity_score", 0.0)

                queries_str = ", ".join(state_after_rewrite["generated_queries"])

                print(f"   ✅ 완료 - 쿼리: {len(state_after_rewrite['generated_queries'])}개, 유사도: {similarity_score:.4f}")

                # 결과 저장
                results.append({
                    "question_num": idx,
                    "question": question,
                    "queries": queries_str,
                    "similarity": similarity_score
                })

                # 콘솔 출력
                print(f"   📝 질문: {question}")
                print(f"   🔍 생성된 쿼리: {queries_str}")
                print(f"   📊 평균 유사도: {similarity_score:.4f}")

            except Exception as e:
                print(f"   ❌ 오류 발생: {e}")
                results.append({
                    "question_num": idx,
                    "question": question,
                    "queries": "",
                    "similarity": 0.0
                })

        # 배치 처리 완료 후 짧은 대기 (마지막 배치가 아닌 경우에만)
        if batch_end < total_questions:
            wait_time = 5  # 30초에서 5초로 단축 (재시도 로직이 있으니 더 공격적으로)
            print(f"\n⏳ 배치 {batch_num} 완료. 다음 배치 준비을 위해 {wait_time}초 대기 중...")
            await asyncio.sleep(wait_time)
            print("✅ 대기 완료. 다음 배치를 처리합니다.")

    # CSV 파일 저장
    save_results_to_csv(results, selected_llm)

    print(f"\n=== 정량 평가 완료 ===")
    print(f"처리된 질문 수: {len(results)}")
    if results:
        avg_similarity = sum(r["similarity"] for r in results) / len(results)
        print(f"전체 평균 유사도: {avg_similarity:.4f}")


def save_results_to_csv(results, model_name):
    """결과를 CSV 파일로 저장하는 함수"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{model_name}_result_{timestamp}.csv"

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['질문번호', '질문내용', '생성된쿼리', '평균유사도']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                writer.writerow({
                    '질문번호': result['question_num'],
                    '질문내용': result['question'],
                    '생성된쿼리': result['queries'],
                    '평균유사도': result['similarity']
                })

        print(f"✅ 결과가 {filename}에 저장되었습니다.")

    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")


async def main():
    """메인 함수 - LLM 모델 선택 및 모드 선택"""
    print("=== 웹 에이전트 테스트 프로그램 ===")

    # 1. LLM 모델 선택
    selected_llm = select_llm_model()
    print(f"선택된 LLM: {selected_llm}")

    # 2. 모드 선택
    selected_mode = select_mode()
    print(f"선택된 모드: {selected_mode}")

    # 3. 선택된 모드에 따라 실행
    if selected_mode == "search_test":
        # 모드 1: 검색 테스트 (기존 로직)
        await test_web_agent_interactive(selected_llm)
    elif selected_mode == "quantitative_evaluation":
        # 모드 2: 정량 평가
        await quantitative_evaluation(selected_llm)


async def test_web_agent_interactive(selected_llm):
    """웹 에이전트 워크플로우를 대화형으로 테스트하는 함수 (기존 test_web_agent)"""
    print("\n=== 웹 검색 에이전트 워크플로우 테스트 ===")
    print("질문을 입력하세요 (종료하려면 'quit' 입력):")

    # 웹 에이전트 워크플로우 인스턴스 생성
    try:
        web_agent = web_agent_workflow(llm_type=selected_llm, web_search_tool_class=WebSearchTool)
        print("✅ 워크플로우 초기화 성공")
    except Exception as e:
        print(f"❌ 워크플로우 초기화 실패: {e}")
        return

    while True:
        try:
            # 사용자 입력 받기
            question = input("\n질문: ").strip()

            # 종료 조건
            if question.lower() in ['quit', 'exit', '종료', 'q']:
                print("테스트를 종료합니다.")
                break

            if not question:
                print("질문을 입력해주세요.")
                continue

            print(f"\n검색 중... 질문: {question}")
            print("=" * 60)

            # 웹 에이전트 워크플로우 실행
            result = await web_agent.run(question)

            # 결과 출력
            print("\n" + "=" * 60)
            print("🔍 검색 결과")
            print("=" * 60)

            if result["success"]:
                print(f"✅ 검색 성공!")
                print(f"📊 상위 4개 문서의 평균 유사도: {result.get('similarity_score', 0):.4f}")
                print(f"📄 사용된 문서 수: {len(result.get('search_results', []))}")
                print(f"🎯 답변 방식: {result.get('answer_type', 'N/A')}")
                print(f"⚖️ 유사도 임계치: {result.get('similarity_threshold', 0.48)}")

                # 유사도에 따른 답변 모드 표시
                if result.get('similarity_score', 0) >= result.get('similarity_threshold', 0.48):
                    print("🔥 고유사도 모드: 통합 분석 답변")
                else:
                    print("📄 저유사도 모드: 문서별 요약")

                print("\n💬 답변 내용:")
                print("-" * 40)
                print(result["answer"])
                print("-" * 40)

            else:
                print(f"❌ 검색 실패: {result['answer']}")

        except KeyboardInterrupt:
            print("\n\n프로그램이 중단되었습니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            print("다시 시도해주세요.")


if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(main())