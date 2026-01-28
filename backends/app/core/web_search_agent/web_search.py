import os
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
import re
import random

load_dotenv()

class WebSearchTool:
    """웹 검색 및 스크래핑 도구."""

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
        """검색 기간에 따른 Google 검색 시간 필터를 생성합니다."""
        if self.time_period_months <= 1:
            return "after:1m"
        elif self.time_period_months <= 3:
            return "after:3m"
        elif self.time_period_months <= 6:
            return "after:6m"
        elif self.time_period_months <= 12:
            return "after:1y"
        else:
            return ""

    async def _fetch_search_results(self, num_to_fetch: int) -> list:
        """SerpAPI를 호출하여 검색 결과를 비동기적으로 가져옵니다."""
        if not self.api_key:
            # print("[오류] SERPAPI_API_KEY가 .env 파일에 설정되지 않았습니다.")
            # raise ValueError("SERPAPI_API_KEY가 .env 파일에 설정되지 않았습니다.")

            print("[오류] SERARCHAPI_KEY가 .env 파일에 설정되지 않았습니다.")
            raise ValueError("SEARCHAPI_KEY가 .env 파일에 설정되지 않았습니다.")

        # 최신 검색 결과를 위한 시간 필터 추가
        time_filter = self._get_time_filter()
        search_query = f"{self.query} {time_filter}" if time_filter else self.query


        params = {
            "engine": "google",
            "q": search_query,
            "api_key": self.api_key,
            "num": num_to_fetch,
            "gl": "kr",  # 한국 검색 결과
            "hl": "ko"   # 한국어 인터페이스
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
            
            selectors = ["#article_body", "#dic_area", "#newsct_article", ".article_view", "#article-view-content-div", "#contents", ".content"]
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

    async def search_and_scrape(self) -> list[dict]:
        """Google에서 검색 후 각 결과 페이지를 스크래핑하여 문서 목록을 반환합니다."""
        num_to_fetch = self.num_results + 5  # 스크래핑 실패 대비 여유분
        search_results = await self._fetch_search_results(num_to_fetch)
        
        if not search_results:
            return []
        
        tasks = [self._scrape_page(r.get("link", "")) for r in search_results]
        scraped_contents = await asyncio.gather(*tasks)

        documents = []
        for r, c in zip(search_results, scraped_contents):
            if c and r.get("link"):
                documents.append(
                    {
                        "title": r.get("title", ""),
                        "link": r.get("link"),
                        "snippet": r.get("snippet", ""),
                        "publish_date": r.get("date", ""),
                        "content": c,
                    }
                )
            if len(documents) == self.num_results:
                break
        
        return documents
