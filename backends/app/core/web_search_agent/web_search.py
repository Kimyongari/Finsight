import os
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import asyncio

load_dotenv()

class WebSearchTool:
    """웹 검색 및 스크래핑 도구."""

    def __init__(self, query: str, num_results: int = 5):
        self.query = query
        self.num_results = num_results
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search.json"

    async def _fetch_search_results(self, num_to_fetch: int) -> list:
        """SerpAPI를 호출하여 검색 결과를 비동기적으로 가져옵니다."""
        if not self.api_key:
            print("[오류] SERPAPI_API_KEY가 .env 파일에 설정되지 않았습니다.")
            raise ValueError("SERPAPI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        params = {
            "engine": "naver",
            "where": "news", # 검색 대상: 네이버 뉴스
            "q": self.query,
            "api_key": self.api_key,
            "num": num_to_fetch,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=10.0)
                response.raise_for_status()
                results = response.json()
                return results.get("news_results", [])
        except httpx.RequestError as e:
            print(f"[오류] SerpAPI 요청 중 오류 발생: {e}")
            return []
        except Exception as e:
            print(f"[오류] SerpAPI 결과 처리 중 오류 발생: {e}")
            return []

    async def _scrape_page(self, url: str) -> str:
        """주어진 URL의 웹 페이지를 스크래핑하여 본문 텍스트를 추출합니다."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, timeout=15.0)
                response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = "\n".join(chunk for chunk in chunks if chunk)[:10000]
            return content
        except Exception as e:
            print(f"[오류] 스크래핑 실패: {url}, 오류: {e}")
            return ""

    async def search_and_scrape(self) -> list[dict]:
        """웹을 검색하고 각 결과 페이지를 스크래핑하여 문서 목록을 반환합니다."""
        num_to_fetch = self.num_results + 5  # 여유분으로 5개 더 가져오기
        search_results = await self._fetch_search_results(num_to_fetch)
        
        if not search_results:
            return []
        
        tasks = [self._scrape_page(r.get("naver_url") or r.get("link", "")) for r in search_results]
        scraped_contents = await asyncio.gather(*tasks)

        documents = []
        for r, c in zip(search_results, scraped_contents):
            if c:
                documents.append(
                    {
                        "title": r.get("title", ""),
                        "link": r.get("naver_url") or r.get("link", ""),
                        "snippet": r.get("snippet", ""),
                        "content": c,
                    }
                )
            if len(documents) == self.num_results:
                break
        
        return documents
