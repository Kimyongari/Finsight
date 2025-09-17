import asyncio
import os
from datetime import datetime, timedelta
from app.core.llm.llm import Midm
from app.core.financial_searchengine.dart_extractor import DartExtractor
from app.core.financial_searchengine.financial_statements_extractor import (
    financial_statements_extractor,
)
from app.core.web_search_agent.web_search import WebSearchTool
from app.core.chart_generator import generate_chart_html
from pykrx import stock
import re
import json


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

        return f"""*   **대표자명:** {ceo_nm}
*   **설립일:** {est_dt}
*   **주요 사업:** {induty_code}
*   **본사 주소:** {adres}
*   **홈페이지:** {hm_url}
*   **시장 구분:** {corp_cls} (종목코드: {stock_code})"""

    async def _categorize_news_list(self, company_name: str, news_list: list) -> list:
        """LLM을 사용하여 전체 뉴스 목록의 카테고리를 분류하고 관련성을 확인합니다."""
        categorize_prompt = f"""
        당신은 금융 뉴스 큐레이터입니다. 다음은 '{company_name}'에 대한 최신 뉴스 목록입니다.

        **지시사항:**
        1.  각 뉴스의 내용이 '{company_name}'과 직접적으로 관련된 것인지 판단하세요.
        2.  관련이 있다면, 아래 카테고리 중 가장 적절한 것으로 하나만 분류하세요.
            - 카테고리: [시장 및 경쟁], [R&D 및 기술], [생산 및 투자], [리스크 및 규제], [실적 및 재무]
        3.  만약 '{company_name}'과 직접적인 관련이 없는 뉴스라면, 카테고리를 반드시 'irrelevant'로 지정하세요.
        4.  결과를 반드시 아래의 JSON 형식으로 반환해야 합니다. 다른 설명 없이 JSON 배열만 반환하세요.

        **JSON 출력 형식:**
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

            categorized_list = None
            try:
                categorized_list = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r"[[.*]]", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    categorized_list = json.loads(json_str)
                else:
                    print(
                        f"오류: LLM 응답에서 JSON 배열을 찾을 수 없습니다. 응답: {response}"
                    )
                    return []

            for item in categorized_list:
                if 0 <= item["index"] < len(news_list):
                    news_list[item["index"]]["category"] = item["category"]
            return news_list

        except (json.JSONDecodeError, KeyError) as e:
            print(f"오류: 뉴스 분류 단계에서 LLM 응답 처리 실패 - {e}")
            return []

    async def _summarize_and_analyze_news(self, news_item: dict) -> str:
        """단일 뉴스 기사를 요약하고 분석합니다."""
        summary_prompt = f"""
        당신은 금융 애널리스트입니다. 다음 뉴스 기사를 분석하고 아래 형식에 맞춰 요약해주세요.

        **지시사항:**
        1.  주어진 기사의 핵심 내용을 2~3문장으로 간결하게 요약합니다.
        2.  해당 뉴스가 회사의 재무, 영업, 주가 등에 미칠 **단기적/장기적 영향**을 분석하고, 투자자 관점에서 어떤 의미가 있는지 **반드시 해석**해야 합니다.
        3.  결과는 아래 마크다운 형식을 **정확히, 글자 하나도 빠짐없이 준수하여** 작성하세요.
        4.  **절대로 `#`를 사용한 마크다운 헤더(예: `## 핵심 요약`)를 출력하면 안 됩니다.**

        **출력 형식:**
        - **핵심 요약:** (여기에 핵심 내용 요약)
        - **영향 분석:** (여기에 영향 분석)
        
        **출력 예시:**
        - **핵심 요약:** 삼성전자가 차세대 반도체 기술 개발에 성공하여, 향후 메모리 시장에서의 리더십을 더욱 공고히 할 것으로 보입니다.
        - **영향 분석:** 단기적으로는 주가에 긍정적 모멘텀으로 작용할 것이며, 장기적으로는 회사의 기술적 해자를 강화하고 경쟁사와의 격차를 벌리는 효과를 가져올 것입니다.
        """

        response = await self.llm.acall(
            system_prompt=summary_prompt,
            user_input=f"기사 전문:\n{news_item['content']}",
        )
        return response

    async def _generate_stock_chart(
        self, corp_code: str, stock_code: str, stock_name: str
    ) -> str:
        """
        주가 데이터를 준비하고 chart_generator를 호출하여 차트 HTML 파일을 생성한 후,
        마크다운 보고서에 삽입할 링크를 반환합니다.
        """
        try:
            # --- 데이터 준비 과정 ---
            today = datetime.now()
            start_date = (today - timedelta(days=365)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")

            df_stock = stock.get_market_ohlcv(start_date, end_date, stock_code)[
                ["종가"]
            ].rename(columns={"종가": stock_name})
            df_kospi = stock.get_index_ohlcv(start_date, end_date, "1001")[
                ["종가"]
            ].rename(columns={"종가": "KOSPI"})
            df_kosdaq = stock.get_index_ohlcv(start_date, end_date, "2001")[
                ["종가"]
            ].rename(columns={"종가": "KOSDAQ"})

            df_merged = df_stock.join(df_kospi, how="inner").join(
                df_kosdaq, how="inner"
            )
            df_normalized = (df_merged / df_merged.iloc[0]) * 100

            # --- chart_generator에 전달할 데이터 가공 ---
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

            # --- 차트 생성 및 저장 경로 설정 ---
            chart_dir = "charts"
            os.makedirs(chart_dir, exist_ok=True)
            chart_filepath = os.path.join(chart_dir, f"{corp_code}_chart1.html")

            await generate_chart_html(chart_data, file_path=chart_filepath)

            # --- 마크다운에 삽입할 링크 반환 ---
            return f"[{stock_name} 주가 비교 차트 보기]({chart_filepath})"

        except Exception as e:
            print(f"주가 차트 생성 중 오류 발생: {e}")
            return "<p>주가 비교 차트를 생성하는 데 실패했습니다.</p>"

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
        stock_code = company_info_dict.get("stock_code", "")

        # 비동기 작업들 병렬 실행
        stock_chart_task = self._generate_stock_chart(corp_code, stock_code, stock_name)

        # 2. 최신 뉴스 처리
        news_search_query = f"{stock_name} 관련 뉴스"
        web_search_tool = WebSearchTool(
            query=news_search_query, num_results=10, time_period_months=3
        )
        scraped_news = await web_search_tool.search_and_scrape()

        if not scraped_news:
            recent_news_summary = "최신 뉴스를 찾을 수 없습니다."
        else:
            categorized_news = await self._categorize_news_list(
                company_name, scraped_news
            )
            relevant_news = [
                news
                for news in categorized_news
                if news.get("category") != "irrelevant"
            ]

            selected_articles = []
            used_categories = set()
            if relevant_news:
                for news_item in relevant_news:
                    category = news_item.get("category")
                    if category and category not in used_categories:
                        selected_articles.append(news_item)
                        used_categories.add(category)

                if len(selected_articles) < 4:
                    selected_links = {article["link"] for article in selected_articles}
                    for news_item in relevant_news:
                        if len(selected_articles) >= 4:
                            break
                        if news_item["link"] not in selected_links:
                            selected_articles.append(news_item)
                            selected_links.add(news_item["link"])

            if not selected_articles:
                recent_news_summary = "주요 뉴스를 선택하는 데 실패했습니다."
            else:
                analysis_tasks = [
                    self._summarize_and_analyze_news(article)
                    for article in selected_articles
                ]
                analyzed_results = await asyncio.gather(*analysis_tasks)

                news_summary_parts = []
                for news_item, analysis_result in zip(
                    selected_articles, analyzed_results
                ):
                    title = news_item.get("title", "제목 없음")
                    link = news_item.get("link", "#")
                    date = news_item.get("publish_date", "날짜 미상")
                    category = news_item.get("category", "분류 안됨")

                    header = f"#### [{title}]({link}) ({date})"
                    body = f"- **카테고리:** [{category}]\n{analysis_result}"
                    news_summary_parts.append(f"{header}\n{body}")

                recent_news_summary = "\n\n".join(news_summary_parts)
                if not recent_news_summary:
                    recent_news_summary = "주요 뉴스를 요약하는 데 실패했습니다."

        # 3. 재무제표 정보
        financial_statement = self.financial_extractor.extract_statement(
            corp_code=corp_code
        )

        # 4. 차트 생성 결과 기다리기
        stock_chart_html = await stock_chart_task

        # 5. LLM을 이용한 종합 결론 생성
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
        conclusion_and_outlook = await self.llm.acall(
            conclusion_prompt, conclusion_context
        )

        # 6. 최종 마크다운 보고서 조립
        report = f"""
# {company_name} 기업 분석 보고서

## I. 기업 개요
{self._format_company_info(company_info_dict)}

## II. 재무 상황
{financial_statement}

## III. 핵심 투자지표 분석
{stock_chart_html}

## IV. 최근 주요 소식
{recent_news_summary}

## V. 종합 결론 및 전망
{conclusion_and_outlook}
"""
        return report.strip()

    async def generate_report_by_identifier(self, identifier: str) -> str:
        """
        종목 코드 또는 기업 코드를 기반으로 기업 분석 보고서를 생성합니다.
        """
        corp_code = None
        if identifier.isdigit():
            if len(identifier) == 6:
                corp_code = self.dart_extractor.get_corp_code_by_stock_code(identifier)
            elif len(identifier) == 8:
                corp_code = self.dart_extractor.find_corp_code(identifier)

        if not corp_code:
            return f"# 오류: 제공된 식별자('{identifier}')에 해당하는 기업을 찾을 수 없습니다."

        return await self.generate_report(corp_code)

    async def generate_report_by_corp_code(self, corp_code: str) -> str:
        """
        종목 코드를 기반으로 기업 분석 보고서를 생성합니다.
        """
        corp_code = self.dart_extractor.validate_corp_code(corp_code)
        if not corp_code:
            return f"# 오류: 종목 코드에 해당하는 기업을 찾을 수 없습니다 (corp_code: {corp_code})"

        return await self.generate_report(corp_code)
