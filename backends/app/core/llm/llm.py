import os
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

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
            print(f"오류가 발생했습니다: {e}")
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
            print(f"오류가 발생했습니다: {e}")
            return None
