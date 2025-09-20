import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.web_agent_workflow_service import web_agent_workflow


async def test_web_agent():
    """웹 에이전트 워크플로우를 테스트하는 함수"""
    print("=== 웹 검색 에이전트 워크플로우 테스트 ===")
    print("질문을 입력하세요 (종료하려면 'quit' 입력):")

    # 웹 에이전트 워크플로우 인스턴스 생성
    try:
        web_agent = web_agent_workflow()
        print("✅ 워크플로우 초기화 성공")
    except Exception as e:
        print(f"❌ 워크플로우 초기화 실패: {e}")
        return

    while True:
        try:
            # 사용자 입력 받기 (Python의 input()이 scanf와 유사한 역할)
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
    asyncio.run(test_web_agent())