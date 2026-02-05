import asyncio
import os
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, START, END
from app.core.llm.llm import OpenRouterLLM, SK, LG, Gemini
from app.core.financial_searchengine.dart_extractor import DartExtractor
from app.core.financial_searchengine.financial_statements_extractor import (
    financial_statements_extractor,
)
from app.core.web_search_agent.news_search import NewsSearchTool
from app.core.chart_generator import generate_chart_html
from app.schemas.langraph_states.state_models import report_workflow_state
from pykrx import stock
import re
import json
import markdown
from dotenv import load_dotenv
load_dotenv()

class report_workflow:
    """LangGraph 기반 기업 분석 보고서 생성 워크플로우.

    기업 코드를 입력받아 기업 정보, 재무 데이터, 뉴스 분석, 차트 생성,
    종합 결론까지 포함한 완전한 분석 보고서를 HTML 형식으로 생성합니다.
    """

    def __init__(self, llm_type:str = None):
        load_dotenv()
        if llm_type == "SK":
            self.llm = SK()
        elif llm_type == "LG":
            self.llm = LG()
        elif llm_type == 'Gemini':
            self.llm = Gemini()
        else:
            self.llm = OpenRouterLLM()
        self.dart_extractor = DartExtractor()
        self.financial_extractor = financial_statements_extractor()
        self.workflow = self.setup()

    def company_info_extractor(self, state: report_workflow_state) -> report_workflow_state:
        """DART API에서 기업 기본 정보를 추출.

        Args:
            state: corp_code를 포함한 워크플로우 상태

        Returns:
            company_info가 업데이트된 상태
        """
        corp_code = state.corp_code
        company_info_dict = self.dart_extractor.get_company_info(corp_code)

        if not company_info_dict or company_info_dict.get("status") != "000":
            return {"company_info": {"error": f"기업 정보를 찾을 수 없습니다 (corp_code: {corp_code})"}}

        return {"company_info": company_info_dict}

    async def news_collector(self, state: report_workflow_state) -> report_workflow_state:
        """웹 검색으로 기업 관련 최신 뉴스를 수집.

        Args:
            state: company_info를 포함한 워크플로우 상태

        Returns:
            news_data가 업데이트된 상태
        """
        company_info = state.company_info
        if "error" in company_info:
            return {"news_data": []}

        company_name = company_info.get("corp_name", "알 수 없음")
        news_search_query = f"{company_name} 최신 뉴스"
        print(f"[DEBUG] 뉴스 검색 쿼리: {news_search_query}")

        news_search_tool = NewsSearchTool(
            query=news_search_query, num_results=20, time_period_months=3
        )
        scraped_news = await news_search_tool.search_and_scrape()

        print(f"[DEBUG] 수집된 뉴스 개수: {len(scraped_news) if scraped_news else 0}")
        if scraped_news:
            for i, news in enumerate(scraped_news[:3]):  # 처음 3개만 로그 출력
                print(f"[DEBUG] 뉴스 {i+1}: {news.get('title', '제목없음')} | 날짜: {news.get('publish_date', '날짜없음')}")

        return {"news_data": scraped_news if scraped_news else []}

    def financial_extractor_node(self, state: report_workflow_state) -> report_workflow_state:
        """DART API에서 재무제표 데이터를 추출.

        Args:
            state: corp_code를 포함한 워크플로우 상태

        Returns:
            financial_statement과 financial_statement_html이 업데이트된 상태
        """
        corp_code = state.corp_code
        financial_statement = self.financial_extractor.extract_statement(corp_code=corp_code, mode='markdown')
        financial_statement_html = self.financial_extractor.extract_statement(corp_code=corp_code, mode='html')
        return {
            "financial_statement": financial_statement,
            "financial_statement_html": financial_statement_html
        }

    async def news_analyzer(self, state: report_workflow_state) -> report_workflow_state:
        """수집된 뉴스를 분류, 선별, 요약 및 영향 분석.

        Args:
            state: company_info와 news_data를 포함한 워크플로우 상태

        Returns:
            analyzed_news가 업데이트된 상태
        """
        company_info = state.company_info
        news_data = state.news_data

        if "error" in company_info or not news_data:
            return {"analyzed_news": []}

        company_name = company_info.get("corp_name", "알 수 없음")
        stock_name = company_info.get("stock_name", company_name)

        # 뉴스 선택 및 분석
        selected_articles = await self._select_and_verify_news(company_name, stock_name, news_data)

        if not selected_articles:
            return {"analyzed_news": []}

        # 뉴스 요약 및 분석
        analysis_tasks = [
            self._summarize_and_analyze_news(article) for article in selected_articles
        ]
        analyzed_results = await asyncio.gather(*analysis_tasks)

        # 분석 결과 포맷팅
        analyzed_news = []
        for news_item, analysis_result in zip(selected_articles, analyzed_results):
            analyzed_news.append({
                "title": news_item.get("title", "제목 없음"),
                "link": news_item.get("link", "#"),
                "date": news_item.get("publish_date", "날짜 미상"),
                "category": news_item.get("category", "분류 안됨"),
                "summary": analysis_result.get("summary", "요약 없음"),
                "analysis": analysis_result.get("analysis", "분석 없음"),
            })

        return {"analyzed_news": analyzed_news}

    async def feature_extractor(self, state: report_workflow_state) -> report_workflow_state:
        """재무제표에서 주요 지표와 수익성 비율을 추출.

        Args:
            state: financial_statement를 포함한 워크플로우 상태

        Returns:
            financial_features와 profitability_ratios가 업데이트된 상태
        """
        financial_statement = state.financial_statement

        # 재무 피처 추출
        financial_features = await self._extract_financial_features(financial_statement)

        # 수익성 지표 추출
        profitability_ratios = await self._extract_profitability_ratios(financial_statement)

        return {
            "financial_features": financial_features,
            "profitability_ratios": profitability_ratios
        }

    async def chart_generator(self, state: report_workflow_state) -> report_workflow_state:
        """주가, 재무지표, 수익성 차트를 병렬 생성.

        Args:
            state: company_info, financial_features, profitability_ratios를 포함한 상태

        Returns:
            세 개의 chart_html 필드가 업데이트된 상태
        """
        company_info = state.company_info
        financial_features = state.financial_features
        profitability_ratios = state.profitability_ratios

        if "error" in company_info:
            return {
                "stock_chart_html": "<p>차트 생성 실패</p>",
                "financial_chart_html": "<p>차트 생성 실패</p>",
                "profitability_chart_html": "<p>차트 생성 실패</p>"
            }

        corp_code = state.corp_code
        company_name = company_info.get("corp_name", "알 수 없음")
        stock_code = company_info.get("stock_code", "")
        stock_name = company_info.get("stock_name", company_name)

        # 3개 차트 병렬 생성
        stock_chart_task = self._generate_stock_chart(corp_code, stock_code, stock_name)
        financial_chart_task = self._generate_financial_chart(corp_code, company_name, financial_features)
        profitability_chart_task = self._generate_profitability_chart(corp_code, company_name, profitability_ratios)

        stock_chart_html, financial_chart_html, profitability_chart_html = await asyncio.gather(
            stock_chart_task, financial_chart_task, profitability_chart_task
        )

        return {
            "stock_chart_html": stock_chart_html,
            "financial_chart_html": financial_chart_html,
            "profitability_chart_html": profitability_chart_html
        }

    async def conclusion_generator(self, state: report_workflow_state) -> report_workflow_state:
        """수집된 모든 데이터를 바탕으로 LLM이 종합 결론을 생성.

        Args:
            state: company_info, financial_statement, analyzed_news를 포함한 상태

        Returns:
            conclusion이 업데이트된 상태
        """
        company_info = state.company_info
        financial_statement = state.financial_statement
        analyzed_news = state.analyzed_news

        if "error" in company_info:
            return {"conclusion": "기업 정보 오류로 인해 결론을 생성할 수 없습니다."}

        company_name = company_info.get("corp_name", "알 수 없음")
        company_info_for_prompt = self._format_company_info(company_info)

        # 뉴스 요약 생성
        news_summary_parts = []
        for news_item in analyzed_news:
            header = f"#### [{news_item['title']}]({news_item['link']}) ({news_item['date']})"
            body = f"- **카테고리:** [{news_item['category']}]\n- **핵심 요약:** {news_item['summary']}\n- **영향 분석:** {news_item['analysis']}"
            news_summary_parts.append(f"{header}\n{body}")

        recent_news_summary = "\n\n".join(news_summary_parts) if news_summary_parts else "최신 뉴스를 찾을 수 없습니다."

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
        #### 강점 (Strengths):
        - (분석된 강점 1)
        - (분석된 강점 2)

        #### 약점 (Weaknesses):
        - (분석된 약점 1)
        - (분석된 약점 2)

        #### 기회 (Opportunities):
        - (분석된 기회 1)
        - (분석된 기회 2)

        #### 위협 (Threats):
        - (분석된 위협 1)
        - (분석된 위협 2)

        ### 종합 의견 및 투자 포인트
        - **종합 의견:** {company_name}은(는) [약점]에도 불구하고 [강점]과 [기회]를 바탕으로 성장이 기대되는 기업입니다. 다만, [위협] 요인에 대한 지속적인 관리가 필요합니다.
        - **핵심 성장 동력:** (기회 요인을 바탕으로 회사의 미래 성장을 이끌 핵심 동력 구체적으로 분석)
        - **주요 리스크:** (위협 및 약점 요인을 바탕으로 투자 시 반드시 고려해야 할 핵심 리스크 구체적으로 분석)
        - **향후 모니터링 포인트:** 투자자들은 향후 [수익성 개선 여부, 신규 수주, 공장 가동률 등]을 핵심적으로 모니터링해야 합니다.
        """

        conclusion_context = f"기업명: {company_name}\n\n기업 개요:\n{company_info_for_prompt}\n\n재무 상황:\n{financial_statement}\n\n최근 주요 소식:\n{recent_news_summary}"
        conclusion = await self.llm.acall(conclusion_prompt, conclusion_context)

        return {"conclusion": conclusion}

    def report_assembler(self, state: report_workflow_state) -> report_workflow_state:
        """모든 구성 요소를 조립하여 최종 HTML 보고서를 생성.

        Args:
            state: 모든 구성 요소가 포함된 완전한 워크플로우 상태

        Returns:
            final_report가 업데이트된 상태
        """
        company_info = state.company_info

        if "error" in company_info:
            final_report = f"<h1>오류: {company_info['error']}</h1>"
            return {"final_report": final_report}

        company_name = company_info.get("corp_name", "알 수 없음")
        company_info_formatted = self._format_company_info(company_info)
        financial_statement_html = state.financial_statement_html
        stock_chart_html = state.stock_chart_html
        financial_chart_html = state.financial_chart_html
        profitability_chart_html = state.profitability_chart_html
        conclusion = state.conclusion

        # 분석된 뉴스 포맷팅
        analyzed_news = state.analyzed_news
        news_summary_parts = []
        for news_item in analyzed_news:
            header = f"#### [{news_item['title']}]({news_item['link']})"
            body = f"- **카테고리:** [{news_item['category']}]\n- **핵심 요약:** {news_item['summary']}\n- **영향 분석:** {news_item['analysis']}"
            news_summary_parts.append(f"{header}\n{body}")

        recent_news_summary = "\n\n".join(news_summary_parts) if news_summary_parts else "최신 뉴스를 찾을 수 없습니다."

        # 마크다운 템플릿 생성 (플레이스홀더 포함)
        markdown_template = f"""
# {company_name} 기업 분석 보고서

## I. 기업 개요
{company_info_formatted}

## II. 재무 제표
{{FINANCIAL_STATEMENT_PLACEHOLDER}}

## III. 핵심 투자지표 분석

### 손익계산서 동기간 비교
{{FINANCIAL_CHART_PLACEHOLDER}}

### 수익성 지표 추이 분석
{{PROFITABILITY_CHART_PLACEHOLDER}}

## IV. 최근 주요 소식
{recent_news_summary}

## V. 종합 결론 및 전망
{conclusion}
"""

        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(markdown_template.strip())

        # 플레이스홀더를 실제 HTML 데이터로 치환
        html_content = html_content.replace("{FINANCIAL_STATEMENT_PLACEHOLDER}", financial_statement_html)
        html_content = html_content.replace("{STOCK_CHART_PLACEHOLDER}", stock_chart_html)
        html_content = html_content.replace("{FINANCIAL_CHART_PLACEHOLDER}", financial_chart_html)
        html_content = html_content.replace("{PROFITABILITY_CHART_PLACEHOLDER}", profitability_chart_html)

        return {"final_report": html_content}

    def setup(self):
        """LangGraph 노드와 엣지를 정의하여 워크플로우를 구성.

        Returns:
            컴파일된 LangGraph 워크플로우
        """
        workflow = StateGraph(report_workflow_state)

        # 노드 추가
        workflow.add_node("company_info_extractor", self.company_info_extractor)
        workflow.add_node("news_collector", self.news_collector)
        workflow.add_node("financial_extractor", self.financial_extractor_node)
        workflow.add_node("news_analyzer", self.news_analyzer)
        workflow.add_node("feature_extractor", self.feature_extractor)
        workflow.add_node("chart_generator", self.chart_generator)
        workflow.add_node("conclusion_generator", self.conclusion_generator)
        workflow.add_node("report_assembler", self.report_assembler)

        # 엣지 연결
        workflow.add_edge(START, "company_info_extractor")
        workflow.add_edge("company_info_extractor", "news_collector")
        workflow.add_edge("company_info_extractor", "financial_extractor")
        workflow.add_edge("news_collector", "news_analyzer")
        workflow.add_edge("financial_extractor", "feature_extractor")
        workflow.add_edge("news_analyzer", "chart_generator")
        workflow.add_edge("feature_extractor", "chart_generator")
        workflow.add_edge("chart_generator", "conclusion_generator")
        workflow.add_edge("conclusion_generator", "report_assembler")
        workflow.add_edge("report_assembler", END)

        return workflow.compile()

    async def run(self, corp_code: str) -> str:
        """기업 코드로 전체 리포트 생성 워크플로우를 실행.

        Args:
            corp_code: 8자리 기업 코드 (ex: "00126380")

        Returns:
            HTML 형식의 기업 분석 보고서
        """
        input_state = report_workflow_state(
            corp_code=corp_code,
            company_info={},
            financial_statement="",
            financial_statement_html="",
            news_data=[],
            analyzed_news=[],
            financial_features={},
            profitability_ratios={},
            stock_chart_html="",
            financial_chart_html="",
            profitability_chart_html="",
            conclusion="",
            final_report=""
        )

        result = await self.workflow.ainvoke(input=input_state)
        return result["final_report"]

    # 기존 ReportService의 헬퍼 메서드들 (필요한 것들만 포함)
    def _format_company_info(self, company_info_dict: dict) -> str:
        """기업 정보를 마크다운 형식으로 포맷팅.

        Args:
            company_info_dict: DART에서 추출한 기업 정보

        Returns:
            마크다운 형식의 기업 개요
        """
        def _format_est_dt(est_dt):
            if not est_dt or len(est_dt) != 8:
                return est_dt
            return f"{est_dt[:4]}년 {est_dt[4:6]}월 {est_dt[6:]}일"

        def _format_corp_cls(corp_cls):
            corp_cls_map = {
                "Y": "유가증권(KOSPI) 상장법인",
                "K": "코스닥(KOSDAQ) 상장법인",
                "N": "코넥스(KONEX) 상장법인",
                "E": "기타 법인",
            }
            return corp_cls_map.get(corp_cls, corp_cls)

        ceo_nm = company_info_dict.get("ceo_nm", "")
        est_dt = _format_est_dt(company_info_dict.get("est_dt", ""))
        induty_code = company_info_dict.get("induty_code", "")
        adres = company_info_dict.get("adres", "")
        hm_url = company_info_dict.get("hm_url", "")
        corp_cls = _format_corp_cls(company_info_dict.get("corp_cls", ""))
        stock_code = company_info_dict.get("stock_code", "")

        return f"""*   **대표자명:** {ceo_nm}
*   **설립일:** {est_dt}
*   **주요 사업:** {induty_code}
*   **본사 주소:** {adres}
*   **홈페이지:** {hm_url}
*   **시장 구분:** {corp_cls} (종목코드: {stock_code})"""

    def _extract_json_from_response(self, response: str, expected_type: str = "array") -> dict | list | None:
        """LLM 텍스트 응답에서 JSON 데이터를 파싱.

        Args:
            response: LLM이 생성한 텍스트 응답
            expected_type: 기대하는 JSON 타입 ("array" 또는 "object")

        Returns:
            파싱된 JSON 데이터 또는 None
        """
        try:
            parsed = json.loads(response)
            if expected_type == "array" and isinstance(parsed, list):
                return parsed
            elif expected_type == "object" and isinstance(parsed, dict):
                return parsed
            return parsed
        except json.JSONDecodeError:
            if expected_type == "array":
                json_match = re.search(r"(?s)```json\s*(\[.*?\])\s*```|(\[.*?\])", response)
            else:
                json_match = re.search(r"(?s)```json\s*(\{.*\})\s*```|(\{.*\})", response)

            if json_match:
                json_str = json_match.group(1) or json_match.group(2)
                try:
                    parsed = json.loads(json_str)
                    return parsed
                except json.JSONDecodeError:
                    pass
            return None

    async def _categorize_news_list(self, company_name: str, news_list: list) -> list:
        """LLM을 사용하여 전체 뉴스 목록의 카테고리를 분류하고 관련성을 확인합니다."""
        print(f"[DEBUG] 카테고리 분류 시작 - 뉴스 개수: {len(news_list)}")

        categorize_prompt = f"""
        당신은 금융 뉴스 큐레이터입니다. 다음은 '{company_name}'에 대한 최신 뉴스 목록입니다.

        **지시사항:**
        1.  각 뉴스의 내용이 '{company_name}'과 직접적으로 관련된 것인지 판단하세요.
        2.  관련이 있다면, 아래 5개 카테고리 중 하나로 분류하세요.
        - **[시장 및 경쟁]**: 시장 점유율, 경쟁사와의 경쟁, 신규 시장 진출, 업계 순위, 브랜드 평가
        - **[R&D 및 기술]**: 신기술 개발, 특허 출원/등록, 연구개발 투자, 기술 혁신, 신제품 기술 사양, 소프트웨어 업데이트
        - **[생산 및 투자]**: 공장 건설/확장, 설비 투자, 생산능력 증설, 인력 채용, 자본 투자 발표
        - **[리스크 및 규제]**: 정부 규제 변화, 법적 소송, 환경 이슈, 공급망 리스크, 정치적 리스크, 무역 분쟁
        - **[실적 및 재무]**: 매출/영업이익 발표, 분기 실적, 재무제표, 배당, 신용등급, 목표주가 조정

        3.  '{company_name}'과 직접적인 관련이 없다면, 'irrelevant'로 분류하세요.

        **출력 형식*:*
        결과를 반드시 아래의 JSON 형식으로 반환해야 합니다. 다른 설명 없이 JSON 배열만 반환하세요.
        [
            {{"index": 0, "category": "(분류된 카테고리 또는 irrelevant)"}},
            {{"index": 1, "category": "(분류된 카테고리 또는 irrelevant)"}},
            ...
        ]"""

        input_text = "뉴스 목록:\n"
        for i, news in enumerate(news_list):
            input_text += f"{i}. 제목: {news['title']}\n   요약: {news['snippet']}\n\n"

        try:
            response = await self.llm.acall(
                system_prompt=categorize_prompt, user_input=input_text
            )

            categorized_list = self._extract_json_from_response(response, "array")
            if not categorized_list:
                print(f"[DEBUG] 카테고리 분류 실패 - JSON 파싱 오류")
                return []

            relevant_count = 0
            irrelevant_count = 0
            for item in categorized_list:
                if 0 <= item.get("index", -1) < len(news_list):
                    category = item["category"]
                    news_list[item["index"]]["category"] = category
                    if category == "irrelevant":
                        irrelevant_count += 1
                    else:
                        relevant_count += 1

            print(f"[DEBUG] 카테고리 분류 완료 - 관련뉴스: {relevant_count}, 무관뉴스: {irrelevant_count}")
            return news_list

        except (KeyError, TypeError) as e:
            print(f"[DEBUG] 카테고리 분류 중 오류: {e}")
            return []

    async def _summarize_and_analyze_news(self, news_item: dict) -> dict:
        """단일 뉴스 기사를 요약하고 분석하여 딕셔너리로 반환합니다."""
        summary_prompt = f"""
        당신은 금융 애널리스트입니다. 다음 뉴스 기사를 분석하고 아래 JSON 형식에 맞춰 요약해주세요.

        **지시사항:**
        1.  주어진 기사의 핵심 내용을 3문장으로 간결하게 요약합니다.
        2.  해당 뉴스가 회사의 재무, 영업, 주가 등에 미칠 **단기적/장기적 영향**을 분석하고, 투자자 관점에서 어떤 의미가 있는지 **반드시 해석**해야 합니다.
        3.  결과를 반드시 아래의 JSON 형식으로 반환해야 합니다. 다른 설명 없이 JSON 객체만 반환하세요.

        **JSON 출력 형식:**
        {{
            "summary": "(여기에 핵심 내용 요약)",
            "analysis": "(여기에 영향 분석)"
        }} """

        user_input = (
            f"제목: {news_item.get('title', '')}\n\n"
            f"요약: {news_item.get('snippet', '')}\n\n"
            f"기사 전문:\n{news_item.get('content', '')}"
        )
        response = await self.llm.acall(
            system_prompt=summary_prompt,
            user_input=user_input,
        )

        try:
            result = self._extract_json_from_response(response, "object")
            if result and isinstance(result, dict):
                return result
            else:
                return {
                    "summary": "요약 생성 실패",
                    "analysis": "영향 분석 실패",
                }
        except (KeyError, TypeError) as e:
            return {
                "summary": "요약 처리 실패",
                "analysis": "영향 분석 처리 실패",
            }

    async def _select_and_verify_news(
        self, company_name: str, stock_name: str, news_list: list, num_to_select: int = 4
    ) -> list:
        """
        뉴스 목록을 필터링, 분류, 선택하고 최종적으로 관련성을 검증하여
        다양하고 관련성 높은 뉴스 기사 목록을 반환합니다.
        """
        # 1단계: 1차 분류 (제목과 요약 기반)
        categorized_news = await self._categorize_news_list(company_name, news_list)

        # 2단계: 관련 없는 뉴스 및 제목 유사 기사 제거
        relevant_news = [
            n for n in categorized_news if n.get("category") != "irrelevant"
        ]
        print(f"[DEBUG] 관련 뉴스 필터링 후: {len(relevant_news)}개")

        unique_articles = []
        processed_titles = []
        title_word_sets = []
        removed_similar_count = 0

        for news_item in relevant_news:
            title = news_item.get("title", "")
            if not title:
                continue

            current_words = set(title.split())
            if not current_words:
                continue

            is_similar = False
            for existing_words in title_word_sets:
                intersection = len(current_words.intersection(existing_words))
                union = len(current_words.union(existing_words))
                if union > 0 and (intersection / union) > 0.7:
                    is_similar = True
                    removed_similar_count += 1
                    print(f"[DEBUG] 유사 제목으로 제거: {title[:50]}...")
                    break

            if not is_similar:
                unique_articles.append(news_item)
                processed_titles.append(title)
                title_word_sets.append(current_words)

        print(f"[DEBUG] 제목 유사도 필터링 후: {len(unique_articles)}개 (제거된 개수: {removed_similar_count})")

        # 3단계: 카테고리별로 분류
        available_categories = ["시장 및 경쟁", "R&D 및 기술", "생산 및 투자", "리스크 및 규제", "실적 및 재무"]
        articles_by_category = {cat: [] for cat in available_categories}

        for news_item in unique_articles:
            category = news_item.get("category", "")
            # 대괄호 제거 및 공백 정리
            cleaned_category = category.strip().strip('[]').strip()

            if cleaned_category in available_categories:
                articles_by_category[cleaned_category].append(news_item)
                news_item["category"] = cleaned_category  # 정리된 카테고리로 업데이트

        # 4단계: 다양한 카테고리의 뉴스를 선택하기 위한 로직
        final_selection = []

        # 기사가 있는 카테고리만 필터링
        categories_with_articles = [cat for cat in available_categories
                                  if articles_by_category[cat]]

        print(f"[DEBUG] 카테고리별 기사 분포:")
        for cat in available_categories:
            count = len(articles_by_category[cat])
            if count > 0:
                print(f"[DEBUG]   {cat}: {count}개")

        # 최대 4개의 서로 다른 카테고리에서 각각 1개씩 선택
        selected_categories = categories_with_articles[:num_to_select]
        print(f"[DEBUG] 선택된 카테고리: {selected_categories}")

        for category in selected_categories:
            if articles_by_category[category]:
                selected_article = articles_by_category[category][0]
                final_selection.append(selected_article)
                print(f"[DEBUG] 카테고리 '{category}'에서 선택: {selected_article.get('title', '제목없음')[:50]}...")

        # 4개 미만인 경우, 남은 기사 중에서 추가 선택
        if len(final_selection) < num_to_select:
            remaining_articles = []
            for category in available_categories:
                if category not in selected_categories:
                    remaining_articles.extend(articles_by_category[category])

            # 선택된 카테고리에서 추가 기사가 있다면 그것도 포함
            for category in selected_categories:
                remaining_articles.extend(articles_by_category[category][1:])

            needed = num_to_select - len(final_selection)
            print(f"[DEBUG] 추가로 {needed}개 기사 필요, 후보: {len(remaining_articles)}개")
            final_selection.extend(remaining_articles[:needed])

        print(f"[DEBUG] 최종 선택된 뉴스 개수: {len(final_selection)}")
        return final_selection

    async def _extract_financial_features(self, financial_statement: str) -> dict:
        """재무제표에서 유의미한 피처를 추출합니다."""
        feature_extraction_prompt = """
        당신은 재무 분석 전문가입니다. 주어진 재무제표에서 손익계산서의 누적 데이터만을 사용하여 동기간 비교 차트를 생성하기 위한 지표를 추출해주세요.

        **핵심 지시사항:**
        1. **실제 기간 정확 추출**: 재무제표에 나타난 실제 기수를 정확히 읽어서 사용하세요.
        2. **손익계산서의 "누적" 컬럼 데이터만 선택**: 3개월, 분기별 데이터는 제외하고 오직 누적 데이터만 사용
        3. **동일 기간 비교**: 전년 동기간과 올해 동기간의 누적 실적만 비교
        4. **재무상태표 데이터 제외**: 자산총계, 자본총계 등 재무상태표 항목은 선택하지 마세요
        5. **손익 지표만 선택**: 매출액, 매출총이익, 영업이익, 당기순이익 등 손익계산서 항목만 선택
        6. **최대 4개 지표**: 규모가 비슷하고 의미 있는 비교가 가능한 지표들로 제한
        7. **정확한 단위 추출**: 재무제표에 명시된 단위 정보를 정확히 추출하여 기록하세요
        8. **기간 표기 통일**: 추출한 실제 기간을 "제 N기 반기" 또는 "제 N기" 형식으로 정리

        **지표명 사용 절대 원칙:**
        **⚠️ 중요: 재무제표에 나타난 지표 명칭을 그대로 사용하세요. 임의로 매핑하거나 변경하면 안 됩니다.**

        **JSON 출력 형식:**
        {
            "features": [
                {
                    "name": "재무제표의_실제_지표명",
                    "category": "수익|수익성|순이익|기타손익",
                    "unit": "실제_추출된_단위",
                    "data": [
                        {"period": "실제_기간_1", "value": 실제값1},
                        {"period": "실제_기간_2", "value": 실제값2}
                    ]
                }
            ]
        }
        """

        try:
            response = await self.llm.acall(
                system_prompt=feature_extraction_prompt, user_input=financial_statement
            )

            result = self._extract_json_from_response(response, "object")
            if result and "features" in result:
                return result
            else:
                return {"features": []}
        except Exception as e:
            print(f"재무 피처 추출 실패: {e}")
            return {"features": []}

    async def _extract_profitability_ratios(self, financial_statement: str) -> dict:
        """재무제표에서 수익성 지표를 추출하고 비율을 계산합니다."""
        profitability_extraction_prompt = """
        당신은 재무 분석 전문가입니다. 주어진 재무제표에서 수익성 지표 계산을 위한 손익계산서 데이터를 추출해주세요.

        **핵심 지시사항:**
        1. **실제 기간 정확 추출**: 재무제표에 나타난 실제 기수를 정확히 읽어서 사용하세요.
        2. **기간 표기 형식**: 기간을 "제 N기 반기" 또는 "제 N기" 형식으로 출력하세요.
        3. **손익계산서의 "누적" 컬럼 데이터만 선택**: 3개월, 분기별 데이터는 제외하고 오직 누적 데이터만 사용
        4. **동일 기간 비교**: 전년 동기간과 올해 동기간의 누적 실적만 비교
        5. **필수 지표 추출**: 다음 4개 지표를 반드시 추출해야 합니다:
           - 매출액 (분모로 사용)
           - 매출총이익 (매출액 - 매출원가)
           - 영업이익
           - 순이익 (당기순이익, 반기순이익 등 최종 순이익)

        **지표명 사용 절대 원칙:**
        **⚠️ 중요: 재무제표에 나타난 지표 명칭을 그대로 사용하세요.**

        **JSON 출력 형식:**
        {
            "profitability_data": [
                {
                    "period": "제 N기 반기",
                    "revenue": 매출액_값,
                    "gross_profit": 매출총이익_값,
                    "operating_profit": 영업이익_값,
                    "net_profit": 순이익_값,
                    "revenue_name": "재무제표의_실제_매출액_명칭",
                    "gross_profit_name": "재무제표의_실제_매출총이익_명칭",
                    "operating_profit_name": "재무제표의_실제_영업이익_명칭",
                    "net_profit_name": "재무제표의_실제_순이익_명칭"
                }
            ],
            "unit": "실제_추출된_단위"
        }
        """

        try:
            response = await self.llm.acall(
                system_prompt=profitability_extraction_prompt, user_input=financial_statement
            )

            result = self._extract_json_from_response(response, "object")
            if result and "profitability_data" in result:
                # 수익성 비율 계산
                calculated_ratios = self._calculate_profitability_ratios(result)
                return calculated_ratios
            else:
                return {"profitability_ratios": []}
        except Exception as e:
            print(f"수익성 지표 추출 실패: {e}")
            return {"profitability_ratios": []}

    def _calculate_profitability_ratios(self, profitability_data: dict) -> dict:
        """추출된 재무 데이터를 기반으로 수익성 비율을 계산합니다."""
        try:
            data_list = profitability_data.get("profitability_data", [])
            unit = profitability_data.get("unit", "백만원")

            if not data_list:
                return {"profitability_ratios": []}

            calculated_ratios = []

            for data in data_list:
                period = data.get("period", "")
                revenue = data.get("revenue", 0)
                gross_profit = data.get("gross_profit", 0)
                operating_profit = data.get("operating_profit", 0)
                net_profit = data.get("net_profit", 0)

                # 실제 지표명 가져오기
                gross_profit_name = data.get("gross_profit_name", "매출총이익")
                operating_profit_name = data.get("operating_profit_name", "영업이익")
                net_profit_name = data.get("net_profit_name", "순이익")

                if revenue == 0:
                    # 매출액이 0이면 비율 계산 불가
                    calculated_ratios.append({
                        "period": period,
                        "gross_profit_ratio": 0,
                        "operating_profit_ratio": 0,
                        "net_profit_ratio": 0,
                        "gross_profit_name": gross_profit_name,
                        "operating_profit_name": operating_profit_name,
                        "net_profit_name": net_profit_name,
                        "raw_data": {
                            "revenue": revenue,
                            "gross_profit": gross_profit,
                            "operating_profit": operating_profit,
                            "net_profit": net_profit
                        }
                    })
                else:
                    # 수익성 비율 계산 (%, 소수점 1자리)
                    gross_profit_ratio = round((gross_profit / revenue) * 100, 1)
                    operating_profit_ratio = round((operating_profit / revenue) * 100, 1)
                    net_profit_ratio = round((net_profit / revenue) * 100, 1)

                    calculated_ratios.append({
                        "period": period,
                        "gross_profit_ratio": gross_profit_ratio,
                        "operating_profit_ratio": operating_profit_ratio,
                        "net_profit_ratio": net_profit_ratio,
                        "gross_profit_name": gross_profit_name,
                        "operating_profit_name": operating_profit_name,
                        "net_profit_name": net_profit_name,
                        "raw_data": {
                            "revenue": revenue,
                            "gross_profit": gross_profit,
                            "operating_profit": operating_profit,
                            "net_profit": net_profit
                        }
                    })

            return {
                "profitability_ratios": calculated_ratios,
                "unit": unit
            }

        except Exception as e:
            print(f"수익성 비율 계산 실패: {e}")
            return {"profitability_ratios": []}

    async def _generate_stock_chart(self, corp_code: str, stock_code: str, stock_name: str) -> str:
        """주가 데이터를 준비하고 chart_generator를 호출하여 차트 HTML 파일을 생성합니다."""
        try:
            # 데이터 준비 과정
            today = datetime.now()
            start_date = (today - timedelta(days=365)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")

            df_stock = stock.get_market_ohlcv(start_date, end_date, stock_code)[["종가"]].rename(columns={"종가": stock_name})
            df_kospi = stock.get_index_ohlcv(start_date, end_date, "1001")[["종가"]].rename(columns={"종가": "KOSPI"})
            df_kosdaq = stock.get_index_ohlcv(start_date, end_date, "2001")[["종가"]].rename(columns={"종가": "KOSDAQ"})

            df_merged = df_stock.join(df_kospi, how="inner").join(df_kosdaq, how="inner")
            df_normalized = (df_merged / df_merged.iloc[0]) * 100

            # chart_generator에 전달할 데이터 가공
            chart_data = {
                "title": f"{stock_name} 주가와 주요 지수 비교 (최근 1년)",
                "x_values": df_normalized.index.strftime("%Y-%m-%d").tolist(),
                "traces": [
                    {
                        "name": stock_name,
                        "y_values": df_normalized[stock_name].tolist(),
                        "custom_data": df_merged[stock_name].tolist(),
                    },
                    {
                        "name": "KOSPI",
                        "y_values": df_normalized["KOSPI"].tolist(),
                        "custom_data": df_merged["KOSPI"].tolist(),
                    },
                    {
                        "name": "KOSDAQ",
                        "y_values": df_normalized["KOSDAQ"].tolist(),
                        "custom_data": df_merged["KOSDAQ"].tolist(),
                    },
                ],
            }

            # 차트 생성하여 HTML 문자열 반환
            chart_html = await generate_chart_html(chart_data)
            return chart_html

        except Exception as e:
            print('주가 비교 차트 생성 중 오류 발생:',e)
            # import traceback
            # traceback.print_exc()
            return ""

    async def _generate_financial_chart(self, corp_code: str, company_name: str, financial_features: dict) -> str:
        """재무 피처를 사용하여 chart_generator를 호출하여 차트 HTML 파일을 생성합니다."""
        try:
            features = financial_features.get("features", [])
            if not features or len(features) == 0:
                return "<p>재무 데이터 차트를 생성할 데이터가 없습니다.</p>"

            # 모든 피처에서 공통 기간 추출 및 검증
            all_periods = set()
            for feature in features:
                for data_point in feature.get("data", []):
                    all_periods.add(data_point.get("period", ""))

            if len(all_periods) < 2:
                return "<p>비교할 기간이 부족하여 차트를 생성할 수 없습니다.</p>"

            # 기간을 정렬 (연도순으로 정렬)
            def period_sort_key(period):
                try:
                    parts = period.split()
                    if len(parts) >= 2 and parts[1].replace('기', '').isdigit():
                        return int(parts[1].replace('기', ''))
                    return 0
                except:
                    return 0

            sorted_periods = sorted(list(all_periods), key=period_sort_key)

            # 데이터 검증 및 정리 (부분 데이터도 허용)
            valid_features = self._validate_and_clean_features(features, sorted_periods)

            if not valid_features:
                return "<p>유효한 재무 데이터가 없어 차트를 생성할 수 없습니다.</p>"

            # 듀얼 차트 생성 (막대그래프와 선그래프 토글 가능)
            chart_data = self._create_dual_chart(company_name, valid_features, sorted_periods)

            # 차트 생성하여 HTML 문자열 반환
            chart_html = await generate_chart_html(chart_data)
            return chart_html

        except Exception as e:
            print(f"재무 차트 생성 실패: {e}")
            return "<p>재무 데이터 차트를 생성하는 데 실패했습니다.</p>"

    async def _generate_profitability_chart(self, corp_code: str, company_name: str, profitability_data: dict) -> str:
        """수익성 비율 데이터를 사용하여 차트 HTML 파일을 생성합니다."""
        try:
            ratios = profitability_data.get("profitability_ratios", [])
            if not ratios or len(ratios) == 0:
                return "<p>수익성 지표 차트를 생성할 데이터가 없습니다.</p>"

            # 모든 비율에서 공통 기간 추출
            all_periods = set()
            for ratio in ratios:
                all_periods.add(ratio.get("period", ""))

            if len(all_periods) < 2:
                return "<p>비교할 기간이 부족하여 수익성 차트를 생성할 수 없습니다.</p>"

            # 기간을 정렬 (과거→현재 순으로 정렬)
            def period_sort_key(period):
                try:
                    parts = period.split()
                    if len(parts) >= 2 and parts[1].replace('기', '').isdigit():
                        return int(parts[1].replace('기', ''))
                    elif '~' in period:
                        year_part = period.split('~')[0].strip().split('.')[0]
                        return int(year_part) if year_part.isdigit() else 0
                    return 0
                except:
                    return 0

            sorted_periods = sorted(list(all_periods), key=period_sort_key)

            # 수익성 차트 데이터 생성
            chart_data = self._create_profitability_chart_data(company_name, ratios, sorted_periods)

            # 차트 생성하여 HTML 문자열 반환
            chart_html = await generate_chart_html(chart_data)
            return chart_html

        except Exception as e:
            print(f"수익성 차트 생성 실패: {e}")
            return "<p>수익성 지표 차트를 생성하는 데 실패했습니다.</p>"

    def _validate_and_clean_features(self, features: list, periods: list) -> list:
        """피처 데이터를 검증하고 정리합니다. 부분 데이터도 허용합니다."""
        cleaned_features = []

        for feature in features:
            feature_data = feature.get("data", [])
            if not feature_data:
                continue

            period_to_value = {data["period"]: data["value"] for data in feature_data}

            # 최소 2개 기간 중 1개 이상의 데이터가 있으면 허용
            valid_data_count = sum(1 for period in periods if period_to_value.get(period) is not None)

            if valid_data_count >= 1:  # 최소 1개 기간에 데이터가 있으면 허용
                # 누락된 데이터는 0으로 채움
                cleaned_data = []
                for period in periods:
                    value = period_to_value.get(period, 0)
                    cleaned_data.append({"period": period, "value": value})

                cleaned_feature = feature.copy()
                cleaned_feature["data"] = cleaned_data
                cleaned_features.append(cleaned_feature)

        return cleaned_features

    def _create_dual_chart(self, company_name: str, features: list, periods: list) -> dict:
        """막대그래프(증감률)와 선그래프(기간별 비교)를 토글할 수 있는 듀얼 차트 데이터를 생성합니다."""
        if len(periods) < 2 or not features:
            return {"chart_type": "line", "x_values": [], "traces": []}

        # 막대그래프 데이터 생성 (증감률)
        bar_data = self._create_bar_chart_data(company_name, features, periods)

        # 선그래프 데이터 생성 (기간별 비교)
        line_data = self._create_line_chart_data(company_name, features, periods)

        return {
            "title": f"{company_name} 손익계산서 비교 분석",
            "chart_type": "dual",
            "bar_data": bar_data,
            "line_data": line_data
        }

    def _create_bar_chart_data(self, company_name: str, features: list, periods: list) -> dict:
        """듀얼 차트용 막대그래프 데이터를 생성합니다."""
        chart_data = {
            "x_values": [],
            "traces": []
        }

        # 지표별 증감률 계산
        indicator_names = []
        growth_rates = []
        base_values = []
        current_values = []

        for feature in features[:4]:
            feature_name = feature.get("name", "")
            period_to_value = {data["period"]: data["value"] for data in feature.get("data", [])}

            # 기준값(이전 기간)과 현재값 계산
            base_value = period_to_value.get(periods[0], 0)
            current_value = period_to_value.get(periods[-1], 0)

            if base_value == 0:
                continue

            growth_rate = ((current_value - base_value) / base_value) * 100

            indicator_names.append(feature_name)
            growth_rates.append(round(growth_rate, 1))
            base_values.append(base_value)
            current_values.append(current_value)

        chart_data["x_values"] = indicator_names

        # 막대그래프용 trace 생성
        if growth_rates:
            # 단위 정보도 포함
            custom_data_with_units = []
            for i in range(len(growth_rates)):
                feature = features[i] if i < len(features) else {}
                unit = feature.get("unit", "백만원")

                custom_data_with_units.append({
                    "base": base_values[i],
                    "current": current_values[i],
                    "growth": growth_rates[i],
                    "base_period": periods[0],
                    "current_period": periods[-1],
                    "unit": unit
                })

            chart_data["traces"].append({
                "name": f"{periods[0]} → {periods[-1]} 증감률",
                "y_values": growth_rates,
                "custom_data": custom_data_with_units
            })

        return chart_data

    def _create_line_chart_data(self, company_name: str, features: list, periods: list) -> dict:
        """듀얼 차트용 선그래프 데이터를 생성합니다."""
        chart_data = {
            "x_values": periods,
            "traces": []
        }

        for feature in features[:4]:
            feature_name = feature.get("name", "")
            unit = feature.get("unit", "")
            period_to_value = {data["period"]: data["value"] for data in feature.get("data", [])}

            y_values = [period_to_value.get(period, 0) for period in periods]

            # 단위 정규화 적용
            normalized_values = []
            original_values = []
            normalized_unit = "억원"

            for val in y_values:
                normalized_val, norm_unit = self._normalize_unit_and_value(val, unit)
                normalized_values.append(normalized_val)
                original_values.append(val)
                normalized_unit = norm_unit

            # 호버용 커스텀 데이터 생성
            custom_data = [
                {
                    "original": original_values[i],
                    "display": normalized_values[i],
                    "original_unit": unit,
                    "display_unit": normalized_unit
                }
                for i in range(len(normalized_values))
            ]

            chart_data["traces"].append({
                "name": f"{feature_name} ({normalized_unit})",
                "y_values": normalized_values,
                "custom_data": custom_data
            })

        return chart_data

    def _create_profitability_chart_data(self, company_name: str, ratios: list, periods: list) -> dict:
        """수익성 비율 데이터를 꺾은선 그래프 형태로 변환합니다."""
        chart_data = {
            "title": f"{company_name} 수익성 지표 추이",
            "x_values": periods,
            "traces": [],
            "chart_type": "profitability"
        }

        # 기간별 데이터를 정리
        period_to_data = {}
        indicator_names = {}

        for ratio in ratios:
            period = ratio.get("period", "")
            if period in periods:
                period_to_data[period] = {
                    "gross_profit_ratio": ratio.get("gross_profit_ratio", 0),
                    "operating_profit_ratio": ratio.get("operating_profit_ratio", 0),
                    "net_profit_ratio": ratio.get("net_profit_ratio", 0),
                    "raw_data": ratio.get("raw_data", {})
                }
                # 실제 지표명 저장 (첫 번째 데이터에서)
                if not indicator_names:
                    indicator_names = {
                        "gross_profit_name": ratio.get("gross_profit_name", "매출총이익"),
                        "operating_profit_name": ratio.get("operating_profit_name", "영업이익"),
                        "net_profit_name": ratio.get("net_profit_name", "순이익")
                    }

        # 3개의 수익성 지표별로 trace 생성
        indicators = [
            {
                "key": "gross_profit_ratio",
                "name": f"{indicator_names.get('gross_profit_name', '매출총이익')}률",
                "color_hint": "gross_profit"
            },
            {
                "key": "operating_profit_ratio",
                "name": f"{indicator_names.get('operating_profit_name', '영업이익')}률",
                "color_hint": "operating_profit"
            },
            {
                "key": "net_profit_ratio",
                "name": f"{indicator_names.get('net_profit_name', '순이익')}률",
                "color_hint": "net_profit"
            }
        ]

        for indicator in indicators:
            y_values = []
            custom_data = []

            for period in periods:
                period_data = period_to_data.get(period, {})
                ratio_value = period_data.get(indicator["key"], 0)
                raw_data = period_data.get("raw_data", {})

                y_values.append(ratio_value)
                custom_data.append({
                    "ratio": ratio_value,
                    "period": period,
                    "revenue": raw_data.get("revenue", 0),
                    "profit": raw_data.get(indicator["key"].replace("_ratio", ""), 0),
                    "indicator_name": indicator["name"]
                })

            chart_data["traces"].append({
                "name": f"{indicator['name']} (%)",
                "y_values": y_values,
                "custom_data": custom_data
            })

        return chart_data

    def _normalize_unit_and_value(self, value: float, unit: str) -> tuple:
        """단위와 값을 정규화하여 일관된 형태로 변환합니다."""
        if not unit:
            # 단위가 없으면 값의 크기로 추정
            if value >= 1000000:  # 100만 이상
                return value / 100, "억원"
            else:
                return value, "원"

        # 단위 정규화
        unit = unit.strip().lower()
        if "백만원" in unit or "백만" in unit:
            return value / 100, "억원"  # 백만원 → 억원으로 변환
        elif "억원" in unit or "억" in unit:
            return value, "억원"
        elif "천원" in unit or "천" in unit:
            return value / 100000, "억원"  # 천원 → 억원으로 변환
        elif "원" in unit:
            return value / 100000000, "억원"  # 원 → 억원으로 변환
        else:
            # 기본적으로 백만원으로 가정
            return value / 100, "억원"