from pydantic import BaseModel

class advanced_rag_state(BaseModel):
    user_question: str
    retrieved_documents :list[dict]
    answer : str
    references : list[dict]

class vanilla_rag_state(BaseModel):
    user_question: str
    retrieved_documents :list[dict]
    answer : str

class report_workflow_state(BaseModel):
    """기업 분석 보고서 생성 워크플로우의 상태 모델.

    Attributes:
        corp_code: 8자리 기업 코드 (예: "00126380")
        company_info: DART에서 추출한 기업 기본 정보
        financial_statement: 재무제표 원문 데이터
        news_data: 웹에서 수집한 원본 뉴스 데이터
        analyzed_news: 분류/요약/분석된 뉴스 데이터
        financial_features: 재무제표에서 추출한 주요 지표
        profitability_ratios: 계산된 수익성 비율 데이터
        stock_chart_html: 주가 비교 차트 HTML 링크
        financial_chart_html: 재무 지표 차트 HTML 링크
        profitability_chart_html: 수익성 지표 차트 HTML 링크
        conclusion: LLM이 생성한 종합 결론
        final_report: 완성된 마크다운 보고서
    """
    corp_code: str
    company_info: dict = {}
    financial_statement: str = ""
    news_data: list = []
    analyzed_news: list = []
    financial_features: dict = {}
    profitability_ratios: dict = {}
    stock_chart_html: str = ""
    financial_chart_html: str = ""
    profitability_chart_html: str = ""
    conclusion: str = ""
    final_report: str = ""