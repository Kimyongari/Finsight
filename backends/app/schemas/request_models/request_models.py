from pydantic import BaseModel


class WebSearchRequest(BaseModel):
    question: str

class RAGRequest(BaseModel):
    query: str

class ReportRequest(BaseModel):
    corp_code: str

class KeywordRequest(BaseModel):
    keyword: str

class RegisterRequest(BaseModel):
    file_name: str