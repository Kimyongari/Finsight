from fastapi import APIRouter
from ..services.rag_service import RagService
from ..schemas.request_models.request_models import RAGRequest
from ..schemas.response_models.response_models import RAGResponse

router = APIRouter()

@router.get("/health")
async def get_rag_status():
    return {"message": "RAG router is active"}

@router.post("/query")
async def query_rag(request: RAGRequest) -> RAGResponse:
    user_query = request.query
    service = RagService()
    response = service.generate_answer(query=user_query)
    if 'err_msg' in response:
        return RAGResponse(success = response['success'], answer = response['err_msg'])
    else:
        return RAGResponse(success = response['success'], answer = response['data'])
