import os
from fastapi import APIRouter
from ..services.rag_service import RagService
from ..services.vanilla_rag_workflow_service import vanilla_rag_workflow
from ..services.advanced_rag_workflow_service import advanced_rag_workflow
from ..schemas.request_models.request_models import RAGRequest, RegisterRequest
from ..schemas.response_models.response_models import RAGResponse, RegisterResponse, ResetResponse, InitResponse, AdvancedRAGResponse

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
        return RAGResponse(success = response['success'], answer = response['answer'], retrieved_documents=response['retrieved_documents'])
    
@router.post("/advanced_query")
async def query_rag(request: RAGRequest) -> AdvancedRAGResponse:
    user_query = request.query
    workflow = advanced_rag_workflow()
    response = workflow.run(question = user_query)
        
    if 'err_msg' in response:
        return RAGResponse(success = response['success'], answer = response['err_msg'], retrieved_documents=[{}], references = [{}])
    else:
        return RAGResponse(success = response['success'], answer = response['answer'], retrieved_documents=response['retrieved_documents'], references = response['references'])
    

@router.post("/register")
async def register(request: RegisterRequest) -> RegisterResponse:
    file_name = request.file_name
    service = RagService()
    result = service.register(file_name = file_name)
    if result['success']:
        return RegisterResponse(success = True, msg = f'{file_name}문서를 VDB에 적재하였습니다.')
    else:
        e = result['err_msg']
        return RegisterResponse(success = False, msg = f'{file_name} 문서를 VDB에 적재하는 데에 실패하였습니다. 오류 메세지 : {e}')
    

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
        return InitResponse(success = True, msg = f"pdf폴더 내에 존재하는 법령 문서를 전부 적재하였습니다. \n적재된파일\n {result['files']}")
    else:
        return InitResponse(success = False, msg = result['err_msg'])