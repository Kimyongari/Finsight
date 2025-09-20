from pydantic import BaseModel
from typing import List

class WebSearchRequest(BaseModel):
    query: str

class RAGRequest(BaseModel):
    query: str

class ReportRequest(BaseModel):
    corp_code: str

class KeywordRequest(BaseModel):
    keyword: str

class RegisterRequest(BaseModel):
    file_name: List[str]

class DeleteObjectsRequest(BaseModel):
    file_name: str

# ✅ 파일 다운로드 요청 모델
class FileDownloadRequest(BaseModel):
    file_name: str

# ✅ 파일 다운로드 요청 모델
class FilePathRequest(BaseModel):
    file_name: str
