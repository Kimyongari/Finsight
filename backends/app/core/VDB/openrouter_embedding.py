# -*- coding: utf-8 -*-
"""OpenRouter 임베딩 클라이언트 (BAAI/bge-m3).

OpenRouter의 `/embeddings` 엔드포인트를 사용하여 텍스트를 1024차원 벡터로
변환합니다. 기존 NaverCloudEmbeddings와 동일한 인터페이스(`embed_query`가
`{'embedding': [...]}`를 반환)를 유지하므로 호출부 수정 없이 교체 가능합니다.
"""

import os
import random
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "baai/bge-m3"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

# bge-m3는 8192 토큰까지 처리하지만, 한국어는 문자당 토큰 비율이 높아
# 안전 마진을 두고 문자 수로 자른다.
MAX_CHARS = 8000


class OpenRouterEmbeddings:
    """OpenRouter를 통해 bge-m3 임베딩을 생성한다."""

    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        self.model = model or os.getenv("EMBEDDING_MODEL_NAME", DEFAULT_MODEL)
        self._api_key = api_key or os.getenv("OPENROUTER_KEY")
        self._base_url = (base_url or os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self._url = f"{self._base_url}/embeddings"

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _truncate(text: str) -> str:
        return (text or "")[:MAX_CHARS]

    def _post(self, payload: dict, max_retries: int = 4) -> dict:
        """429/5xx에 대해 지수 백오프로 재시도하며 POST한다."""
        if not self._api_key:
            return {"err_msg": "OPENROUTER_KEY가 .env 파일에 설정되지 않았습니다."}

        last_err = None
        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(self._url, json=payload, headers=self._headers)
                if response.status_code == 200:
                    return response.json()
                if response.status_code in (408, 429) or response.status_code >= 500:
                    last_err = f"{response.status_code} {response.text[:200]}"
                    if attempt < max_retries:
                        wait = min(2 ** attempt + random.uniform(0.1, 0.6), 30)
                        print(f"[재시도] 임베딩 {response.status_code} 응답, {wait:.1f}초 후 재시도 "
                              f"({attempt + 1}/{max_retries})")
                        time.sleep(wait)
                        continue
                    return {"err_msg": last_err}
                return {"err_msg": f"{response.status_code} {response.text[:200]}"}

            except httpx.RequestError as e:
                last_err = str(e)
                if attempt < max_retries:
                    wait = min(2 ** attempt + random.uniform(0.1, 0.6), 30)
                    print(f"[재시도] 임베딩 네트워크 오류, {wait:.1f}초 후 재시도: {e}")
                    time.sleep(wait)
                    continue
                return {"err_msg": last_err}

        return {"err_msg": last_err or "알 수 없는 오류"}

    def embed_query(self, text: str) -> dict:
        """단일 텍스트를 임베딩한다.

        Returns:
            성공 시 `{'embedding': [float, ...]}`, 실패 시 `{'err_msg': str}`.
        """
        result = self._post({"model": self.model, "input": self._truncate(text)})
        if "err_msg" in result:
            return result
        try:
            return {"embedding": result["data"][0]["embedding"]}
        except (KeyError, IndexError) as e:
            return {"err_msg": f"임베딩 응답 형식 오류: {e}"}

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """여러 텍스트를 한 번의 요청으로 임베딩한다.

        Returns:
            입력 순서와 동일한 벡터 리스트. 실패한 항목은 빈 리스트.
        """
        if not texts:
            return []

        payload = {"model": self.model, "input": [self._truncate(t) for t in texts]}
        result = self._post(payload)
        if "err_msg" in result:
            print(f"[오류] 배치 임베딩 실패: {result['err_msg']}")
            return [[] for _ in texts]

        vectors = [[] for _ in texts]
        for item in result.get("data", []):
            idx = item.get("index", 0)
            if 0 <= idx < len(vectors):
                vectors[idx] = item.get("embedding", [])
        return vectors

    async def aembed_query(self, text: str, max_retries: int = 4) -> list[float]:
        """비동기 단일 임베딩. 실패 시 빈 리스트를 반환한다."""
        if not self._api_key:
            print("[오류] OPENROUTER_KEY가 .env 파일에 설정되지 않았습니다.")
            return []

        payload = {"model": self.model, "input": self._truncate(text)}
        import asyncio

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(self._url, json=payload, headers=self._headers)
                if response.status_code == 200:
                    return response.json()["data"][0]["embedding"]
                if response.status_code in (408, 429) or response.status_code >= 500:
                    if attempt < max_retries:
                        wait = min(2 ** attempt + random.uniform(0.1, 0.6), 30)
                        print(f"[재시도] 임베딩 {response.status_code} 응답, {wait:.1f}초 후 재시도")
                        await asyncio.sleep(wait)
                        continue
                print(f"[오류] 임베딩 HTTP {response.status_code}: {response.text[:200]}")
                return []

            except httpx.RequestError as e:
                if attempt < max_retries:
                    wait = min(2 ** attempt + random.uniform(0.1, 0.6), 30)
                    print(f"[재시도] 임베딩 네트워크 오류, {wait:.1f}초 후 재시도: {e}")
                    await asyncio.sleep(wait)
                    continue
                print(f"[오류] 임베딩 네트워크 오류: {e}")
                return []
            except (KeyError, IndexError) as e:
                print(f"[오류] 임베딩 응답 형식 오류: {e}")
                return []

        return []
