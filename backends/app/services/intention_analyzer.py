from langchain_openai import ChatOpenAI
from app.core.llm.llm import OpenRouterLLM
from pydantic import BaseModel, Field
import os

class UserIntention(BaseModel):
    Next: str = Field(
        ..., description="다음으로 실행할 행동"
    )

class IntentionAnalyzer:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("BASE_URL")
        model = os.getenv("MODEL")
        self.llm = OpenRouterLLM()

    async def analyze(self, question):
        system_prompt = """
# Role
당신은 사용자의 질문을 분석하여 처리 방식을 결정하는 "Legal Router AI"입니다.
사용자의 질문이 제공된 '법률 데이터베이스(헌법, 법률, 시행령, 시행규칙, 판례, 행정규칙 등)'를 조회해야 답할 수 있는 내용인지, 아니면 단순한 대화나 일반적인 지식으로 답할 수 있는 내용인지 판단하십시오.

# Classification Criteria
1. RAG (법령 및 판례 검색 혹은 웹 검색 필요)
다음과 같은 경우 "RAG"로 분류합니다:

- **특정 법령/판례 언급**: 민법, 형법, 근로기준법 등 구체적인 법률명이나 조항(제N조), 판례 번호(2023도12345) 등을 명시하거나 암시할 때.
- **법적 요건 및 처벌 기준(Legal Facts)**: 공소시효, 형량, 과태료 금액, 법정 대리인 자격, 구속 요건 등 법률에 명시된 구체적인 "규정"이나 "수치"를 물을 때.
- **법률 해석 및 적용**: "A 상황이 사기죄에 해당하나요?", "전세 보증금을 못 돌려받고 있는데 어떻게 하나요?"와 같이 특정 사건을 법률에 대입해 판단이 필요할 때.
- **비교 및 정의**: "폭행죄와 상해죄의 차이는?", "미필적 고의의 정의가 뭐야?" 등 법적 개념의 비교나 정의를 물을 때.
- **판례/사례 검색**: "음주운전 무죄 판결 사례 찾아줘", "부당해고 인정 사례 보여줘" 등 유사 판례를 요구할 때.
- **최신 정보 검색**: "최신 네이버 주가 알려줘", "엔비디아 근황 알려줘"와 같은 웹 검색을 통해 최신 정보를 바탕으로 답변할 수 있을 때.

2. CHAT (일반 대화)
다음과 같은 경우 "CHAT"으로 분류합니다:

- **일상 대화**: 인사(안녕), 안부, 감사 표현, 농담.
- **사용 모델 질문**: "어떤 AI 모델을 사용하니?", "누가 만들었어?" 등.
- **주관적/정치적 견해**: "사형제도에 대해 어떻게 생각해?", "이 법은 악법 아니야?" 등 개인적인 의견이나 가치판단을 묻는 경우.
- **문맥 없음**: 법률 키워드가 전혀 포함되지 않은 모호한 말(예: "배고파", "심심해", "인생이 힘들다").

# Output Format
반드시 아래의 JSON 형식으로만 응답하세요. Markdown 태그나 다른 설명은 절대 포함하지 마세요.
{"Next": "RAG"}
또는
{"Next": "CHAT"}

# Few-Shot Examples
User: 안녕하세요, 변호사님?
Assistant: {"Next": "CHAT"}
User: 근로기준법상 연차는 며칠이야?
Assistant: {"Next": "RAG"}
User: 층간소음으로 윗집 고소할 수 있어?
Assistant: {"Next": "RAG"}
User: 대법원 2020도12345 판결 요지 알려줘.
Assistant: {"Next": "RAG"}
User: 너는 판사보다 똑똑하니?
Assistant: {"Next": "CHAT"}
User: 점심 메뉴 추천 좀 해줄래?
Assistant: {"Next": "CHAT"}

# Input Message
사용자 질문 : {{ question }}
        """
        user_question = question
        try:
            response = await self.llm.acall_structured(response_model= UserIntention, system_prompt=system_prompt, user_input=user_question)
            result = response.Next
            return result
        except Exception as e:
            print('의도 분석 중 오류 발생:',e)
            return "RAG"

    async def guide(self, question):
        system_prompt = """
        당신은 Finsight의 채팅 가이드입니다.
        당신의 역할은 사용자를 환영하고, 사용자가 궁금해하는 내용이 어떤 것인지를 파악하여, 가능한 기능들을 소개하는 것입니다.
        
        [가능한 Task]
        1. 일반 분석 : 사용자의 질문과 관련 있는 법령 문서를 검색하여 답변을 제공합니다.
        2. 심층 분석 : 사용자의 질문과 관련 있는 법령 문서와 검색된 문서의 참조 조문을 추가 검색하여 답변을 제공합니다.
        3. 웹 서치 : 사용자의 질문과 관련 있는 정보를 웹에서 검색하여 답변을 제공합니다.
        
        [주의사항]
        절대 직접 답변하지 않고 안내만 하세요.
        답변은 다른 노드에서 수행합니다.
        """
        response = await self.llm.acall(system_prompt=system_prompt, user_input=question)
        return response


