import os
from fastapi import APIRouter
from ..services.rag_service import RagService
from ..services.vanilla_rag_workflow_service import vanilla_rag_workflow
from ..services.advanced_rag_workflow_service import advanced_rag_workflow
from ..schemas.request_models.request_models import RAGRequest, RegisterRequest,DeleteObjectsRequest
from ..schemas.response_models.response_models import RAGResponse, RegisterResponse, ResetResponse, InitResponse, AdvancedRAGResponse, ShowResponse, DeleteObjectsResponse
from ..services.vdb_service import VDBService

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
        return AdvancedRAGResponse(success = response['success'], answer = response['err_msg'], retrieved_documents=[{}], references = [{}])
    else:
        return AdvancedRAGResponse(success = response['success'], answer = response['answer'], retrieved_documents=response['retrieved_documents'], references = response['references'])

@router.post("/register")
async def register(request: RegisterRequest) -> RegisterResponse:
    file_names = request.file_name
    service = VDBService()
    for file_name in file_names:
        result = service.register(file_name = file_name)
        if result['success']:
            continue
        else:
            e = result['err_msg']
            return RegisterResponse(success = False, msg = f'{file_name} 문서를 VDB에 적재하는 데에 실패하였습니다. 오류 메세지 : {e}')
    return RegisterResponse(success = True, msg = f'{file_name}문서를 VDB에 적재하였습니다.')
    

@router.get("/reset")
async def reset():
    service = VDBService()
    result = service.reset()
    if result['success']:
        return ResetResponse(success = True, msg = 'VDB를 성공적으로 리셋하였습니다.') 
    else:
        return ResetResponse(success = False, msg = result['err_msg'])
    
@router.get("/initialize")
async def initalize():
    service = VDBService()
    result = service.initialize()
    if result['success']:
        return InitResponse(success = True, msg = f"pdf폴더 내에 존재하는 법령 문서를 전부 적재하였습니다. \n적재된파일\n {result['files']}")
    else:
        return InitResponse(success = False, msg = result['err_msg'])
    
@router.get("/show_files_in_collection")    
async def show_files_in_collection() -> ShowResponse:
    service = VDBService()
    result = service.show_files_in_collection()
    if result['success']:
        return ShowResponse(success = True, msg = "collection 내에 존재하는 file과 chunk 수를 불러오는 데에 성공하였습니다.", unique_file_name_and_chunk = result['unique_file_name_and_chunk'])
    else:
        return ShowResponse(success = False, msg = result['err_msg'], unique_file_name_and_chunk = [])
    
@router.post("/delete_objects_from_file_name")
async def delete_objects_from_file_name(request:DeleteObjectsRequest) -> DeleteObjectsResponse:
    service = VDBService()
    file_name = request.file_name
    result = service.delete_objects_from_file_name(file_name = file_name)
    if result['success']:
        return DeleteObjectsResponse(success = True, msg = f"{file_name}에 해당하는 objects들을 전부 삭제하였습니다.")
    else:
        return DeleteObjectsResponse(success = False, msg = result['err_msg'])