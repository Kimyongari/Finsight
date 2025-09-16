
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
        당신은 금융 애널리스트입니다. 다음은 '{company_name}'에 대한 최신 뉴스 기사 목록입니다.

        **지시사항:**
        1.  '{company_name}'과 직접 관련된 뉴스 중에서, **서로 다른 주제의 주요 뉴스 3~4개**를 선별하세요. (예: 기술 개발, 시장 경쟁, 생산/투자, 실적, 리스크 등)
        2.  각 뉴스를 다음 카테고리 중 가장 적절한 것으로 분류하세요: [시장 및 경쟁], [R&D 및 기술], [생산 및 투자], [리스크 및 규제], [실적 및 재무].
        3.  각 뉴스에 대해 아래의 마크다운 형식을 **정확히 준수하여** 내용을 작성하세요.
            - 뉴스 제목은 `####`를 사용하고, **제공된** URL과 작성일을 포함해야 합니다.
            - **핵심 요약:** 뉴스의 핵심 내용을 2~3문장으로 간결하게 요약합니다.
            - **영향 분석:** 해당 뉴스가 회사의 재무, 영업, 주가 등에 미칠 **단기적/장기적 영향**을 분석하고, 투자자 관점에서 어떤 의미가 있는지 **반드시 해석**해야 합니다.

        **출력 형식 (서론, 결론 없이 바로 첫 뉴스로 시작):**
        #### [뉴스 제목 1](URL 1) (날짜)
        - **카테고리:** [분류된 카테고리]
        - **핵심 요약:** (뉴스의 핵심 내용 요약)
        - **영향 분석:** (단기/장기적 영향 및 투자 관점에서의 의미 분석)

        #### [뉴스 제목 2](URL 2) (날짜)
        - **카테고리:** [분류된 카테고리]
        - **핵심 요약:** (뉴스 내용 요약)
        - **영향 분석:** (단기/장기적 영향 및 투자 관점에서의 의미 분석)
        """
        news_context = ''
        for i in scraped_news:
            context ="\n\n".join(f"제목: {i['title']}\nURL: {i['link']}\n내용: {i['content']}")
            if not len(news_context + context + "\n\n") > 12000:
                news_context += context + "\n\n"
            else:
                break
        recent_news_summary = await self.llm.acall(system_prompt=news_summary_prompt, user_input=f"뉴스 기사 목록:\n{news_context}")

        # 3. 재무제표 정보
        financial_statement = self.financial_extractor.extract_statement(corp_code=corp_code)

        # 4. LLM을 이용한 종합 결론 생성
        company_info_for_prompt = self._format_company_info(company_info_dict)

        conclusion_prompt = f"""
        당신은 월스트리트의 저명한 애널리스트입니다. 주어진 기업의 재무제표, 최신 뉴스, 기업 개요를 종합하여 깊이 있는 분석과 전망을 제공해주세요.

        **분석 과정 (이 과정에 따라 생각하고 최종 결과만 출력):**
        1.  **재무 건전성 분석:** 제공된 재무제표를 바탕으로 다음 핵심 재무 비율의 현재 상태와 의미를 해석합니다.
            - **안정성:** 유동비율(유동자산/유동부채), 부채비율(부채총계/자본총계)
            - **수익성:** 매출총이익률, 영업이익률. 영업손실이 지속될 경우, 그 원인을 분석.
        2.  **SWOT 분석:** 분석한 모든 정보(기업 개요, 재무, 뉴스)를 바탕으로 회사의 강점(Strengths), 약점(Weaknesses), 기회(Opportunities), 위협(Threats)을 각각 2가지씩 도출합니다.
        3.  **종합 의견 및 투자 전략 도출:** 위의 재무 분석과 SWOT 분석 결과를 종합하여 최종 결론과 투자 전략을 작성합니다.

        **최종 출력 형식 (아래 형식을 엄격하게 준수하세요. 다른 설명이나 제목 없이 바로 시작):**

        ### 재무 건전성 분석
        - **안정성:** 유동비율과 부채비율을 통해 본 회사의 단기 지급 능력과 재무 구조 안정성은 [양호/보통/주의 필요] 수준입니다. (구체적인 수치나 근거 제시)
        - **수익성:** 현재 영업이익률은 [플러스/마이너스] 상태로, [매출원가 부담, 판관비 증가 등]의 원인으로 수익성 개선이 [필요한/진행중인] 상황입니다. (구체적인 수치나 근거 제시)
        - **현금흐름:** 영업활동 현금흐름이 [플러스/마이너스]를 기록하여 [긍정적/부정적]이며, 대규모 투자로 인해 투자활동 현금흐름 유출이 지속되고 있습니다.

        ### SWOT 분석 및 전략 제언
        | 구분 | 핵심 내용 |
        | :--- | :--- |
        | **강점 (Strengths)** | (분석된 강점 1)<br>(분석된 강점 2) |
        | **약점 (Weaknesses)** | (분석된 약점 1)<br>(분석된 약점 2) |
        | **기회 (Opportunities)**| (분석된 기회 1)<br>(분석된 기회 2) |
        | **위협 (Threats)** | (분석된 위협 1)<br>(분석된 위협 2) |

        ### 종합 의견 및 투자 포인트
        - **종합 의견:** {company_name}은(는) [약점]에도 불구하고 [강점]과 [기회]를 바탕으로 성장이 기대되는 기업입니다. 다만, [위협] 요인에 대한 지속적인 관리가 필요합니다.
        - **핵심 성장 동력:** (기회 요인을 바탕으로 회사의 미래 성장을 이끌 핵심 동력 구체적으로 분석)
        - **주요 리스크:** (위협 및 약점 요인을 바탕으로 투자 시 반드시 고려해야 할 핵심 리스크 구체적으로 분석)
        - **향후 모니터링 포인트:** 투자자들은 향후 [수익성 개선 여부, 신규 수주, 공장 가동률 등]을 핵심적으로 모니터링해야 합니다.
        """
        conclusion_context = f"기업명: {company_name}\n\n기업 개요:\n{company_info_for_prompt}\n\n재무 상황:\n{financial_statement}\n\n최근 주요 소식:\n{recent_news_summary}"
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

    async def generate_report_by_corp_code(self, corp_code: str) -> str:
        """
        종목 코드를 기반으로 기업 분석 보고서를 생성합니다.
        """
        corp_code = self.dart_extractor.validate_corp_code(corp_code)
        if not corp_code:
            return f"# 오류: 종목 코드에 해당하는 기업을 찾을 수 없습니다 (corp_code: {corp_code})"
        
        return await self.generate_report(corp_code)
