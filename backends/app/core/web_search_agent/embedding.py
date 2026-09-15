"""웹 검색 문서 필터링용 임베딩 유틸리티.

OpenRouter의 bge-m3 모델로 임베딩을 생성하고 코사인 유사도를 계산합니다.
"""

import asyncio
import os
import random

import httpx
import numpy as np
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "baai/bge-m3")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
EMBEDDING_URL = f"{OPENROUTER_BASE_URL}/embeddings"

# bge-m3의 입력 한도(8192 토큰)에 여유를 둔 문자 수 상한
MAX_CHARS = 8000


async def _post_embeddings(payload: dict, max_retries: int = 4) -> dict | None:
    """429/5xx에 대해 지수 백오프로 재시도하며 임베딩 API를 호출한다."""
    if not OPENROUTER_KEY:
        raise ValueError("OPENROUTER_KEY가 .env 파일에 설정되지 않았습니다.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(EMBEDDING_URL, json=payload, headers=headers)

            if response.status_code == 200:
                return response.json()

            if response.status_code in (408, 429) or response.status_code >= 500:
                if attempt < max_retries:
                    wait = min(2 ** attempt + random.uniform(0.1, 0.5), 30)
                    print(f"[재시도] 임베딩 {response.status_code} 응답, {wait:.1f}초 후 재시도 "
                          f"(시도 {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(wait)
                    continue

            print(f"[오류] 임베딩 HTTP {response.status_code}: {response.text[:200]}")
            return None

        except httpx.RequestError as e:
            if attempt < max_retries:
                wait = min(2 ** attempt + random.uniform(0.1, 1.0), 30)
                print(f"[재시도] 네트워크 오류, {wait:.1f}초 후 재시도: {e}")
                await asyncio.sleep(wait)
                continue
            print(f"[오류] 네트워크 오류 (최대 재시도 초과): {e}")
            return None

    return None


async def get_embedding(text: str) -> list[float]:
    """텍스트 하나의 임베딩 벡터를 반환한다. 실패 시 빈 리스트."""
    data = await _post_embeddings({
        "model": EMBEDDING_MODEL_NAME,
        "input": (text or "")[:MAX_CHARS],
    })
    if not data:
        return []
    try:
        return data["data"][0]["embedding"]
    except (KeyError, IndexError) as e:
        print(f"[오류] 임베딩 응답 형식 오류: {e}")
        return []


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """여러 텍스트를 한 번의 요청으로 임베딩한다.

    Returns:
        입력 순서와 같은 벡터 리스트. 실패한 항목은 빈 리스트.
    """
    if not texts:
        return []

    data = await _post_embeddings({
        "model": EMBEDDING_MODEL_NAME,
        "input": [(t or "")[:MAX_CHARS] for t in texts],
    })
    if not data:
        return [[] for _ in texts]

    vectors: list[list[float]] = [[] for _ in texts]
    for item in data.get("data", []):
        idx = item.get("index", 0)
        if 0 <= idx < len(vectors):
            vectors[idx] = item.get("embedding", [])
    return vectors


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """두 벡터 간의 코사인 유사도를 계산합니다."""
    if not v1 or not v2:
        return 0.0
    v1_arr = np.array(v1)
    v2_arr = np.array(v2)
    denom = np.linalg.norm(v1_arr) * np.linalg.norm(v2_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(v1_arr, v2_arr) / denom)
