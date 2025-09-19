"""기업 분석 보고서 생성 서비스.

기업 코드를 입력받아 DART 기업 정보, 재무 데이터, 뉴스 분석,
차트 생성, 종합 결론을 포함한 분석 보고서를 생성합니다.
"""

from app.services.report_workflow import report_workflow


class ReportService:
    """기업 분석 보고서 생성 서비스."""

    def __init__(self):
        """보고서 생성 워크플로우를 초기화."""
        self.workflow = report_workflow()

    async def generate_report(self, corp_code: str) -> str:
        """기업 코드로 완전한 분석 보고서를 생성.

        Args:
            corp_code: 8자리 기업 코드 (예: "00126380")

        Returns:
            마크다운 형식의 기업 분석 보고서
        """
        return await self.workflow.run(corp_code)

    async def generate_report_by_identifier(self, identifier: str) -> str:
        """종목 코드 또는 기업 코드로 분석 보고서를 생성.

        Args:
            identifier: 6자리 종목 코드 또는 8자리 기업 코드

        Returns:
            마크다운 형식의 기업 분석 보고서
        """
        # 종목 코드나 기업 코드 처리 로직
        dart_extractor = self.workflow.dart_extractor
        corp_code = None

        if identifier.isdigit():
            if len(identifier) == 6:
                # 종목 코드를 기업 코드로 변환
                corp_code = dart_extractor.get_corp_code_by_stock_code(identifier)
            elif len(identifier) == 8:
                # 이미 기업 코드
                corp_code = dart_extractor.find_corp_code(identifier)

        if not corp_code:
            return f"# 오류: 제공된 식별자('{identifier}')에 해당하는 기업을 찾을 수 없습니다."

        return await self.generate_report(corp_code)


def _format_est_dt(est_dt):
    """설립일을 읽기 쉬운 형식으로 포맷팅.

    Args:
        est_dt: 8자리 날짜 문자열 (예: "20100101")

    Returns:
        포맷팅된 날짜 문자열 (예: "2010년 01월 01일")
    """
    if not est_dt or len(est_dt) != 8:
        return est_dt
    return f"{est_dt[:4]}년 {est_dt[4:6]}월 {est_dt[6:]}일"


def _format_corp_cls(corp_cls):
    """기업 구분 코드를 한글 설명으로 변환.

    Args:
        corp_cls: 기업 구분 코드 ("Y", "K", "N", "E")

    Returns:
        기업 구분 설명 문자열
    """
    corp_cls_map = {
        "Y": "유가증권(KOSPI) 상장법인",
        "K": "코스닥(KOSDAQ) 상장법인",
        "N": "코넥스(KONEX) 상장법인",
        "E": "기타 법인",
    }
    return corp_cls_map.get(corp_cls, corp_cls)