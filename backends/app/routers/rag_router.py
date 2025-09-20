import os
from fastapi import APIRouter
from ..services.rag_service import RagService
from ..services.vanilla_rag_workflow_service import vanilla_rag_workflow
from ..schemas.request_models.request_models import RAGRequest, RegisterRequest
from ..schemas.response_models.response_models import RAGResponse, RegisterResponse, ResetResponse, InitResponse

router = APIRouter()

@router.get("/health")
async def get_rag_status():
    return {"message": "RAG router is active"}

@router.post("/query")
async def query_rag(request: RAGRequest) -> RAGResponse:
    user_query = request.query
    workflow = vanilla_rag_workflow()
    response = workflow.run(question = user_query)
        
    if 'err_msg' in response:
        return RAGResponse(success = response['success'], answer = response['err_msg'], retrieved_documents=[{}])
    else:
        return RAGResponse(success = response['success'], answer = response['data'], retrieved_documents=response['retrieved_documents'])
    
@router.post("/register")
async def register(request: RegisterRequest) -> RegisterResponse:
    file_names = request.file_name
    service = RagService()
    results = [service.register(file_name=x) for x in file_names]
    all_success = all(r['success'] for r in results)

    if all_success:
        return RegisterResponse(success = True, msg=f"{', '.join(file_names)} 문서를 VDB에 적재하였습니다.")
    else:
        failed = [f"{file_names[i]}: {r['err_msg']}" for i, r in enumerate(results) if not r['success']]
        return RegisterResponse(
            success=False,
            msg=f"다음 문서를 VDB에 적재하는 데 실패하였습니다. 오류: {', '.join(failed)}"
        )
    

@router.get("/reset")
async def reset():
    service = RagService()
    result = service.reset()
    if result['success']:
        return ResetResponse(success = True, msg = 'VDB를 성공적으로 리셋하였습니다.') 
    else:
        return ResetResponse(success = False, msg = result['err_msg'])
    
@router.get("/initialize")
async def initalize():
    service = RagService()
    result = service.initialize()
    if result['success']:
        return InitResponse(success = True, msg = "pdf폴더 내에 존재하는 법령 문서를 전부 적재하였습니다.")
    else:
        return InitResponse(success = False, msg = result['err_msg'])