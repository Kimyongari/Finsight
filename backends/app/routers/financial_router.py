from fastapi import APIRouter
from ..schemas.request_models.request_models import ReportRequest, KeywordRequest
from ..schemas.response_models.response_models import StatementResponse, CorplistResponse
from ..services.financial_service import FinancialService
router = APIRouter()

@router.get("/health")
async def get_financial_status():
    return {"message": "Financial router is active"}

@router.post("/corp_list")
async def get_corp_list_from_keyword(request: KeywordRequest) -> CorplistResponse:
    keyword = request.keyword
    service = FinancialService()
    result = service.search_corp_code_with_keyword(keyword=keyword)
    if result['success']:
        response = CorplistResponse(data = result['data'], success=True, err_msg='')
    else:
        response = CorplistResponse(data = [{}], success=False, err_msg = result['err_msg'])

    return response

@router.post("/statement")
async def get_financial_statement(request: ReportRequest) ->StatementResponse:
    # This is a placeholder for your financial service logic
    service = FinancialService()
    corp_code = request.corp_code
    if len(corp_code) != 8:
        response = StatementResponse(statement = '재무제표 추출에 실패했습니다. corp_code를 확인해 주세요.', success = False)
        return response
    result = service.extract_financial_statements(corp_code=corp_code)
    if result['success']:
        response = StatementResponse(statement = result['statement'], success=True)
    else:
        response = StatementResponse(statement = '재무제표 추출에 실패했습니다. corp_code를 확인해 주세요.', success = False)
    return response
