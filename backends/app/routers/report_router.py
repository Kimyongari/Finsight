
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from app.services.report_service import ReportService

router = APIRouter()

@router.get("/{stock_code}", 
            summary="기업 분석 보고서 생성",
            response_class=PlainTextResponse) 
async def generate_company_report(
    stock_code: str,
    report_service: ReportService = Depends(ReportService)
):
    """
    종목 코드(stock_code)를 받아 해당 기업에 대한 상세 분석 보고서를 Markdown 형식으로 생성합니다.

    - **stock_code**: KRX에서 사용하는 6자리 종목 코드 (예: 삼성전자 - 005930)
    """
    try:
        report = await report_service.generate_report_by_stock_code(stock_code)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류 발생: {str(e)}")
