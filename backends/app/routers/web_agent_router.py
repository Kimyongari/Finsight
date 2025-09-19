from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.web_agent_service import WebAgentService
from app.schemas.response_models.response_models import WebSearchResponse

router = APIRouter()

class WebSearchRequest(BaseModel):
    question: str

@router.post("/agent/web-search", summary="웹 검색 에이전트 실행")
async def run_web_agent(
    request: WebSearchRequest,
    agent_service: WebAgentService = Depends(WebAgentService)
) -> WebSearchResponse:
    """
    사용자의 질문을 받아 웹 검색 에이전트를 실행하고 최종 답변을 반환합니다.
    """
    result = await agent_service.search(request.question)
    return WebSearchResponse(
        answer=result["answer"],
        success=result["success"],
        search_results=result["search_results"]
    )
