
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from app.services.report_service import ReportService

router = APIRouter()

@router.get("/{corp_code}", 
            summary="기업 분석 보고서 생성",
            response_class=PlainTextResponse) 
async def generate_company_report(
    corp_code: str,
    report_service: ReportService = Depends(ReportService)
):
    """
    기업 코드(corp_code)를 받아 해당 기업에 대한 상세 분석 보고서를 Markdown 형식으로 생성합니다.

    - **corp_code**: KRX에서 사용하는 8자리 종목 코드 (예: 삼성전자 - 00126380)
    """
    try:
        report = await report_service.generate_report_by_corp_code(corp_code)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류 발생: {str(e)}")
