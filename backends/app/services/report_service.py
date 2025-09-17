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

    def _extract_json_from_response(self, response: str, expected_type: str = "array") -> dict | list | None:
        """
        LLM 응답에서 JSON을 추출하는 공통 함수
        """
        try:
            parsed = json.loads(response)
            if expected_type == "array" and isinstance(parsed, list):
                return parsed
            elif expected_type == "object" and isinstance(parsed, dict):
                return parsed
            return parsed
        except json.JSONDecodeError:
            # 마크다운 코드 블록이나 일반 텍스트에서 JSON 추출 시도
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
                    return []

            for item in categorized_list:
                if 0 <= item.get("index", -1) < len(news_list):
                    news_list[item["index"]]["category"] = item["category"]
            return news_list

        except (KeyError, TypeError) as e:
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

        unique_articles = []
        processed_titles = []
        title_word_sets = []
        
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
                if union > 0 and (intersection / union) > 0.6:
                    is_similar = True
                    break
                    
            if not is_similar:
                unique_articles.append(news_item)
                processed_titles.append(title)
                title_word_sets.append(current_words)


        # 3단계: 카테고리별로 분류 (관련성 검증 제거)
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

        # 최대 4개의 서로 다른 카테고리에서 각각 1개씩 선택
        selected_categories = categories_with_articles[:num_to_select]

        for category in selected_categories:
            if articles_by_category[category]:
                selected_article = articles_by_category[category][0]
                final_selection.append(selected_article)

        # 4개 미만인 경우, 남은 기사 중에서 추가 선택 (다른 카테고리 우선)
        if len(final_selection) < num_to_select:
            remaining_articles = []
            for category in available_categories:
                if category not in selected_categories:
                    remaining_articles.extend(articles_by_category[category])

            # 선택된 카테고리에서 추가 기사가 있다면 그것도 포함
            for category in selected_categories:
                remaining_articles.extend(articles_by_category[category][1:])

            needed = num_to_select - len(final_selection)
            final_selection.extend(remaining_articles[:needed])

        return final_selection

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

            df_stock = stock.get_market_ohlcv(start_date, end_date, stock_code)[["종가"]].rename(columns={"종가": stock_name})
            df_kospi = stock.get_index_ohlcv(start_date, end_date, "1001")[["종가"]].rename(columns={"종가": "KOSPI"})
            df_kosdaq = stock.get_index_ohlcv(start_date, end_date, "2001")[["종가"]].rename(columns={"종가": "KOSDAQ"})

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
        news_search_query = f"{company_name} 최신 뉴스"
        web_search_tool = WebSearchTool(
            query=news_search_query, num_results=20, time_period_months=3
        )
        scraped_news = await web_search_tool.search_and_scrape()

        if not scraped_news:
            recent_news_summary = "최신 뉴스를 찾을 수 없습니다."
        else:
            selected_articles = await self._select_and_verify_news(
                company_name, stock_name, scraped_news
            )

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
                    summary = analysis_result.get("summary", "요약 없음")
                    analysis = analysis_result.get("analysis", "분석 없음")

                    header = f"#### [{title}]({link}) ({date})"
                    body = f"- **카테고리:** [{category}]\n- **핵심 요약:** {summary}\n- **영향 분석:** {analysis}"
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