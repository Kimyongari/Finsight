from fastapi import APIRouter
from pydantic import BaseModel
from app.services.web_agent_workflow_service import web_agent_workflow
from app.schemas.response_models.response_models import WebSearchResponse

router = APIRouter()

class WebSearchRequest(BaseModel):
    question: str

@router.get("/health")
async def get_web_agent_status():
    return {"message": "Web Agent router is active"}

@router.post("/agent/web-search", summary="웹 검색 에이전트 실행")
async def run_web_agent(request: WebSearchRequest) -> WebSearchResponse:
    """
    사용자의 질문을 받아 웹 검색 에이전트 워크플로우를 실행하고 최종 답변을 반환합니다.
    """
    workflow = web_agent_workflow()
    result = await workflow.run(request.question)

    return WebSearchResponse(
        answer=result["answer"],
        success=result["success"],
        search_results=result["search_results"]
    )
