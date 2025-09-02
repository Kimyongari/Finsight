import os
import httpx
import numpy as np
from dotenv import load_dotenv

load_dotenv()

NAVER_CLOVA_API_KEY = os.getenv("NAVER_CLOVA_API_KEY")
NAVER_CLOUD_API_HOST = os.getenv("NAVERCLOUD_HOST")
NAVER_EMBEDDING_URI = "/v1/api-tools/embedding/v2"

async def get_naver_embedding(text: str) -> list[float]:
    """Naver Cloud Embedding API를 호출하여 텍스트의 임베딩 벡터를 반환합니다."""
    if not NAVER_CLOVA_API_KEY:
        raise ValueError("NAVER_CLOVA_API_KEY가 .env 파일에 설정되지 않았습니다.")

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": NAVER_CLOVA_API_KEY,
    }
    payload = {"text": text}
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
        except httpx.RequestError as e:
            print(f"[오류] Naver Embedding API 요청 중 오류 발생: {e}")
            return []
        except (KeyError, IndexError) as e:
            print(f"[오류] Naver Embedding API 응답 형식 오류: {e}")
            return []

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """두 벡터 간의 코사인 유사도를 계산합니다."""
    if not v1 or not v2:
        return 0.0
    v1_arr = np.array(v1)
    v2_arr = np.array(v2)
    return np.dot(v1_arr, v2_arr) / (np.linalg.norm(v1_arr) * np.linalg.norm(v2_arr))
