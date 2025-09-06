
import asyncio
from datetime import datetime
from app.core.llm.llm import Midm
from app.core.financial_searchengine.dart_extractor import DartExtractor
from app.core.financial_searchengine.financial_statements_extractor import financial_statements_extractor
from app.core.web_search_agent.web_search import WebSearchTool

def _format_est_dt(est_dt):
    if not est_dt or len(est_dt) != 8:
        return est_dt
    return f"{est_dt[:4]}년 {est_dt[4:6]}월 {est_dt[6:]}일"

def _format_corp_cls(corp_cls):
    corp_cls_map = {
        'Y': '유가증권(KOSPI) 상장법인',
        'K': '코스닥(KOSDAQ) 상장법인',
        'N': '코넥스(KONEX) 상장법인',
        'E': '기타 법인'
    }
    return corp_cls_map.get(corp_cls, corp_cls)

class ReportService:
    def __init__(self):
        self.llm = Midm()
        self.dart_extractor = DartExtractor()
        self.financial_extractor = financial_statements_extractor()

    def _format_company_info(self, company_info_dict: dict) -> str:
        ceo_nm = company_info_dict.get("ceo_nm", "")
        est_dt = _format_est_dt(company_info_dict.get("est_dt", ""))
        induty_code = company_info_dict.get("induty_code", "")
        adres = company_info_dict.get("adres", "")
        hm_url = company_info_dict.get("hm_url", "")
        corp_cls = _format_corp_cls(company_info_dict.get("corp_cls", ""))
        stock_code = company_info_dict.get("stock_code", "")

        return f'''*   **대표자명:** {ceo_nm}
*   **설립일:** {est_dt}
*   **주요 사업:** {induty_code}
*   **본사 주소:** {adres}
*   **홈페이지:** {hm_url}
*   **시장 구분:** {corp_cls} (종목코드: {stock_code})'''

    async def generate_report(self, corp_code: str) -> str:
        """
        기업 코드를 기반으로 기업 분석 보고서를 생성합니다.
        """
        # 1. DART에서 기업 정보 가져오기
        company_info_dict = self.dart_extractor.get_company_info(corp_code)
        if not company_info_dict or company_info_dict.get("status") != "000":
            return f"# 오류: 기업 정보를 찾을 수 없습니다 (corp_code: {corp_code})"
        
        company_name = company_info_dict.get("corp_name", "알 수 없음")
        stock_name = company_info_dict.get("stock_name", company_name)

        # 2. 최신 뉴스 검색 및 요약
        news_search_query = f"{stock_name} 최신 뉴스"
        web_search_tool = WebSearchTool(query=news_search_query, num_results=5)
        scraped_news = await web_search_tool.search_and_scrape()
        
        today = datetime.now().strftime("%Y-%m-%d")
        news_summary_prompt = f"""
        당신은 금융 뉴스 큐레이터입니다. 다음은 {company_name}에 대한 최신 뉴스 기사 목록입니다.
        
        **지시사항:**
        1.  오직 `{company_name}`에 대한 뉴스만 선택하세요.
        2.  최신 뉴스를 선택하세요. 오늘 날짜: {today}
        3.  선택한 뉴스 중에서 **서로 주제가 다른 주요 뉴스 4개**를 고르세요. (예: 신제품 출시, 실적 발표, 공장 증설 등)
        4.  각 뉴스의 제목은 `###` 마크다운 제목 형식으로 작성하고, **제공된** 해당 뉴스의 URL을 [] 안에, 작성일을 () 안에 포함하세요. (예: `### [뉴스 제목](제공된 URL) (날짜)`)
        5.  각 뉴스 내용은 5문장으로 핵심 내용만 요약하여 제목 아래에 작성하세요.
        6.  서론이나 결론 없이, 바로 첫 번째 뉴스 요약부터 시작하세요.

        예시:
        ### [뉴스1 제목](뉴스1 URL) (날짜)
        뉴스1 내용 요약

        ### [뉴스2 제목](뉴스2 URL) (날짜)
        뉴스2 내용 요약
        """
        news_context = "\n\n".join([f"제목: {n['title']}\nURL: {n['link']}\n내용: {n['content']}" for n in scraped_news])
        recent_news_summary = await self.llm.acall(news_summary_prompt, f"뉴스 기사 목록:\n{news_context}")

        # 3. 재무제표 정보
        financial_statement = self.financial_extractor.extract_statement(corp_code=corp_code)

        # 4. LLM을 이용한 종합 결론 생성
        company_info_for_prompt = self._format_company_info(company_info_dict)

        conclusion_prompt = """
        당신은 투자 전문가입니다. 주어진 기업 정보를 바탕으로, 이 기업에 대한 최종 결론과 향후 전망을 작성해주세요.
        
        **출력 형식 지시사항:**
        - 오직 `### 결론`과 `### 전망` 두 개의 제목만 사용하세요.
        - 각 제목 아래에는 `-`를 이용한 리스트 형식으로 4개의 핵심 사항을 요약하여 작성하세요.
        - 다른 제목, 소제목, 서론, 맺음말 등은 절대 추가하지 마세요.
        
        예시:
        ### 결론
        - 결론 핵심 사항 1
        - 결론 핵심 사항 2
        - 결론 핵심 사항 3
        - 결론 핵심 사항 4
        
        ### 전망
        - 전망 핵심 사항 1
        - 전망 핵심 사항 2
        - 전망 핵심 사항 3
        - 전망 핵심 사항 4
        """
        conclusion_context = f"기업 개요:\n{company_info_for_prompt}\n\n재무 상황:\n{financial_statement}\n\n최근 주요 소식:\n{recent_news_summary}"
        conclusion_and_outlook = await self.llm.acall(conclusion_prompt, conclusion_context)


        # 5. 최종 마크다운 보고서 조립
        report = f"""
# {company_name} 기업 분석 보고서

## I. 기업 개요
{self._format_company_info(company_info_dict)}

## II. 재무 상황
{financial_statement}

## III. 최근 주요 소식
{recent_news_summary}

## IV. 종합 결론 및 전망
{conclusion_and_outlook}
"""
        return report.strip()

    async def generate_report_by_stock_code(self, stock_code: str) -> str:
        """
        종목 코드를 기반으로 기업 분석 보고서를 생성합니다.
        """
        corp_code = self.dart_extractor.get_corp_code_by_stock_code(stock_code)
        if not corp_code:
            return f"# 오류: 종목 코드에 해당하는 기업을 찾을 수 없습니다 (stock_code: {stock_code})"
        
        return await self.generate_report(corp_code)
