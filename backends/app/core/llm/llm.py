import os
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Type, TypeVar, Optional
import json

load_dotenv()

class Midm:
    def __init__(self):# 클라이언트 초기화
        self.sync_client = OpenAI(
            api_key=os.environ.get("RUNPOD_API_KEY"),
            base_url=os.environ.get("RUNPOD_BASE_URL"),
        )
        self.async_client = AsyncOpenAI(
            api_key=os.environ.get("RUNPOD_API_KEY"),
            base_url=os.environ.get("RUNPOD_BASE_URL"),
        )

    def call(self, system_prompt:str = "당신은 유용한 어시스턴트입니다.", user_input:str = "안녕? 너에 대해 소개해줘."):
        try:
            response = self.sync_client.chat.completions.create(
                model="K-intelligence/Midm-2.0-Base-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None

    async def acall(self, system_prompt:str, user_input:str):
        try:
            response = await self.async_client.chat.completions.create(
                model="K-intelligence/Midm-2.0-Base-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
                timeout=300.0
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None


class SK:
    def __init__(self):# 클라이언트 초기화
        self.sync_client = OpenAI(
            api_key=os.environ.get("SK_API_KEY"),
            base_url=os.environ.get("SK_BASE_URL"),
        )
        self.async_client = AsyncOpenAI(
            api_key=os.environ.get("SK_API_KEY"),
            base_url=os.environ.get("SK_BASE_URL"),
        )

    def call(self, system_prompt:str = "당신은 유용한 어시스턴트입니다.", user_input:str = "안녕? 너에 대해 소개해줘."):
        try:
            response = self.sync_client.chat.completions.create(
                model="skt/A.X-4.0-Light",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None

    async def acall(self, system_prompt:str, user_input:str):
        try:
            response = await self.async_client.chat.completions.create(
                model="skt/A.X-4.0-Light",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
                timeout=300.0
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None


class LG:
    def __init__(self):# 클라이언트 초기화
        self.sync_client = OpenAI(
            api_key=os.environ.get("LG_API_KEY"),
            base_url=os.environ.get("LG_BASE_URL"),
        )
        self.async_client = AsyncOpenAI(
            api_key=os.environ.get("LG_API_KEY"),
            base_url=os.environ.get("LG_BASE_URL"),
        )

    def call(self, system_prompt:str = "당신은 유용한 어시스턴트입니다.", user_input:str = "안녕? 너에 대해 소개해줘."):
        try:
            response = self.sync_client.chat.completions.create(
                model="LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None

    async def acall(self, system_prompt:str, user_input:str):
        try:
            response = await self.async_client.chat.completions.create(
                model="LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
                timeout=300.0
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None


class Gemini:
    def __init__(self):# 클라이언트 초기화
        self.sync_client = OpenAI(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            base_url=os.environ.get("GOOGLE_BASE_URL"),
        )
        self.async_client = AsyncOpenAI(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            base_url=os.environ.get("GOOGLE_BASE_URL"),
        )

    def call(self, system_prompt:str = "당신은 유용한 어시스턴트입니다.", user_input:str = "안녕? 너에 대해 소개해줘."):
        try:
            response = self.sync_client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None

    async def acall(self, system_prompt:str, user_input:str):
        try:
            response = await self.async_client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
                timeout=300.0
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None

class OpenRouterLLM:
    def __init__(self):# 클라이언트 초기화
        self.sync_client = OpenAI(
            api_key=os.environ.get("OPENROUTER_KEY"),
            base_url=os.environ.get("OPENROUTER_BASE_URL"),
        )
        self.async_client = AsyncOpenAI(
            api_key=os.environ.get("OPENROUTER_KEY"),
            base_url=os.environ.get("OPENROUTER_BASE_URL"),
        )
        self.model = os.environ.get("MODEL", 'google/gemini-2.5-flash-preview-09-2025')

    def call(self, system_prompt:str = "당신은 유용한 어시스턴트입니다.", user_input:str = "안녕? 너에 대해 소개해줘."):
        try:
            response = self.sync_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None

    async def acall(self, system_prompt:str, user_input:str):
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role" : "user",
                        "content" : user_input
                    }
                ],
                temperature=0.7,
                timeout=300.0
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            print(f"LLM API 호출 중 오류 발생: {type(e).__name__} - {e}")
            return None

    async def acall_structured(self, response_model=None, system_prompt: str="사용자의 질문에 친절히 답변하세요.", user_input: str="안녕?") -> Optional:
        """
        Pydantic 모델(response_model)을 받아 해당 스키마에 맞는 객체를 반환합니다.
        """
        if not response_model:
            raise ValueError("response_model은 필수입니다.")
        try:
            # 1. Pydantic 모델에서 JSON 스키마 추출
            schema_json = json.dumps(response_model.model_json_schema(), ensure_ascii=False, indent=2)

            # 2. 시스템 프롬프트에 스키마 강제 지시 추가
            # (Gemini/GPT 계열은 시스템 프롬프트에 스키마를 명시하는 것이 가장 정확합니다)
            structured_prompt = (
                f"{system_prompt}\n\n"
                f"### IMPORTANT OUTPUT INSTRUCTION ###\n"
                f"You MUST return the result as a valid JSON object strictly following this schema:\n"
                f"{schema_json}"
            )

            # 3. API 호출 (JSON 모드 활성화)
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": structured_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                # JSON 모드를 지원하는 모델인 경우 필수 (대부분 최신 모델 지원)
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # 4. JSON 문자열을 Pydantic 객체로 변환 및 검증
            return response_model.model_validate_json(content)

        except Exception as e:
            print(f"Structured Output 생성 실패: {type(e).__name__} - {e}")
            return None