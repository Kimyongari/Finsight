import os
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import random

load_dotenv()

class NewsSearchTool:
    """네이버 뉴스 검색 및 스크래핑 도구."""

    # User-Agent 풀 - 다양한 브라우저와 OS 조합
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",

        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",

        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",

        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ]

    def __init__(self, query: str, num_results: int = 5, time_period_months: int = 3):
        self.query = query
        self.num_results = num_results
        self.time_period_months = time_period_months
        self.api_key = os.getenv("SEARCHAPI_KEY")
        self.base_url = "https://www.searchapi.io/api/v1/search"

    def _get_time_filter(self) -> str:
        """검색 기간에 따른 Naver 검색 시간 필터를 생성합니다."""
        if self.time_period_months <= 1:
            return "1m"
        elif self.time_period_months <= 3:
            return "3m"
        elif self.time_period_months <= 6:
            return "6m"
        elif self.time_period_months <= 12:
            return "1y"
        else:
            return "all"

    async def _fetch_news_results(self, num_to_fetch: int) -> list:
        """SerpAPI를 호출하여 네이버 뉴스 검색 결과를 비동기적으로 가져옵니다."""
        if not self.api_key:
            # print("[오류] SERPAPI_API_KEY가 .env 파일에 설정되지 않았습니다.")
            # raise ValueError("SERPAPI_API_KEY가 .env 파일에 설정되지 않았습니다.")

            print("[오류] SERARCHAPI_KEY가 .env 파일에 설정되지 않았습니다.")
            raise ValueError("SEARCHAPI_KEY가 .env 파일에 설정되지 않았습니다.")

        # 네이버 뉴스 검색을 위한 파라미터
        params = {
            "engine": "google_news",
            "q": self.query,
            "api_key": self.api_key,
            "period": self._get_time_filter(),  # 시간 필터
            "sort_by": "most_recent",  # 최신순 정렬
            "num": num_to_fetch
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=10.0)
                response.raise_for_status()
                results = response.json()
                return results.get("organic_results", [])
        except httpx.RequestError as e:
            print(f"[오류] SerpAPI 요청 중 오류 발생: {e}")
            return []
        except Exception as e:
            print(f"[오류] SerpAPI 결과 처리 중 오류 발생: {e}")
            return []

    async def _scrape_page(self, url: str) -> str:
        """주어진 URL의 웹 페이지를 스크래핑하여 본문 텍스트를 추출합니다."""
        try:
            # 랜덤한 User-Agent 선택
            user_agent = random.choice(self.USER_AGENTS)

            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }

            # SSL 설정 조정 - 더 유연한 검증
            async with httpx.AsyncClient(
                follow_redirects=True,
                verify=False,  # SSL 검증 비활성화
                timeout=15.0   # 타임아웃 증가
            ) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            # 네이버 뉴스 및 일반 뉴스 사이트 선택자
            selectors = [
                "#dic_area",  # 네이버 뉴스
                "#newsct_article",  # 네이버 뉴스 (구버전)
                "#article_body",  # 일반 뉴스 사이트
                ".article_view",  # 일반 뉴스 사이트
                "#article-view-content-div",  # 일반 뉴스 사이트
                "#contents",  # 일반 뉴스 사이트
                ".content",  # 일반 뉴스 사이트
                ".news_end"  # 네이버 뉴스 (일부)
            ]

            content_html = None
            for selector in selectors:
                content_html = soup.select_one(selector)
                if content_html:
                    break

            text_content = content_html.get_text() if content_html else soup.get_text()

            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = "\n".join(chunk for chunk in chunks if chunk)[:4000]
            return content
        except Exception as e:
            print(f"[오류] 스크래핑 실패: {url}, 오류: {e}")
            return ""

    def _format_date(self, naver_date: str) -> str:
        """네이버 뉴스 날짜 형식을 표준화합니다."""
        if not naver_date:
            return ""

        # 네이버 뉴스는 "1시간 전", "3일 전" 등의 형식이나 "2025.01.15" 형식 사용
        if "전" in naver_date:
            return naver_date
        elif "." in naver_date and len(naver_date.replace(".", "")) >= 8:
            # "2025.01.15" -> "2025. 1. 15."
            parts = naver_date.split(".")
            if len(parts) >= 3:
                return f"{parts[0]}. {int(parts[1])}. {int(parts[2])}."

        return naver_date

    async def search_and_scrape(self) -> list[dict]:
        """네이버에서 뉴스 검색 후 각 결과 페이지를 스크래핑하여 문서 목록을 반환합니다."""
        num_to_fetch = self.num_results + 5  # 스크래핑 실패 대비 여유분
        news_results = await self._fetch_news_results(num_to_fetch)

        if not news_results:
            return []

        tasks = [self._scrape_page(result.get("link", "")) for result in news_results]
        scraped_contents = await asyncio.gather(*tasks)

        documents = []
        for result, content in zip(news_results, scraped_contents):
            if content and result.get("link"):
                # 네이버 뉴스 결과 구조에 맞게 데이터 추출
                news_info = result.get("news_info", {})
                publish_date = self._format_date(news_info.get("news_date", ""))

                documents.append({
                    "title": result.get("title", ""),
                    "link": result.get("link"),
                    "snippet": result.get("snippet", ""),
                    "publish_date": publish_date,
                    "content": content,
                    "press_name": news_info.get("press_name", ""),  # 언론사 정보 추가
                })

            if len(documents) == self.num_results:
                break

        return documents