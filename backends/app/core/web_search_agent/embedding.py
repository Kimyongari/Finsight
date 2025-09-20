import os
import httpx
import numpy as np
import asyncio
import random
from dotenv import load_dotenv

load_dotenv()

NAVER_CLOVA_API_KEY = os.getenv("NAVER_CLOVA_API_KEY")
NAVER_CLOUD_API_HOST = os.getenv("NAVERCLOUD_HOST")
NAVER_EMBEDDING_URI = "/v1/api-tools/embedding/v2"

async def get_naver_embedding(text: str, max_retries: int = 5) -> list[float]:
    """Naver Cloud Embedding API를 호출하여 텍스트의 임베딩 벡터를 반환합니다.

    Rate limiting 대응을 위한 exponential backoff 재시도 로직 포함.
    """
    if not NAVER_CLOVA_API_KEY:
        raise ValueError("NAVER_CLOVA_API_KEY가 .env 파일에 설정되지 않았습니다.")

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": NAVER_CLOVA_API_KEY,
    }
    payload = {"text": text}

    for attempt in range(max_retries + 1):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{NAVER_CLOUD_API_HOST}{NAVER_EMBEDDING_URI}",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("result", {}).get("embedding", [])

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    if attempt < max_retries:
                        # Retry-After 헤더 확인
                        retry_after = e.response.headers.get("Retry-After")
                        if retry_after:
                            wait_time = int(retry_after)
                        else:
                            # Exponential backoff with jitter
                            base_delay = 2 ** attempt  # 1, 2, 4, 8, 16초
                            jitter = random.uniform(0.1, 0.5) * base_delay  # 10-50% 지터
                            wait_time = min(base_delay + jitter, 64)  # 최대 64초

                        print(f"[재시도] Rate limit 감지, {wait_time:.1f}초 후 재시도 (시도 {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"[오류] 최대 재시도 횟수 초과 (429 오류): {e}")
                        return []
                else:
                    print(f"[오류] HTTP 오류 {e.response.status_code}: {e}")
                    return []

            except httpx.RequestError as e:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0.1, 1.0)
                    print(f"[재시도] 네트워크 오류, {wait_time:.1f}초 후 재시도: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"[오류] 네트워크 오류 (최대 재시도 초과): {e}")
                    return []

            except (KeyError, IndexError) as e:
                print(f"[오류] Naver Embedding API 응답 형식 오류: {e}")
                return []

    return []

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """두 벡터 간의 코사인 유사도를 계산합니다."""
    if not v1 or not v2:
        return 0.0
    v1_arr = np.array(v1)
    v2_arr = np.array(v2)
    return np.dot(v1_arr, v2_arr) / (np.linalg.norm(v1_arr) * np.linalg.norm(v2_arr))
