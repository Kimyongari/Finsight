from pydantic import BaseModel

class RAGResponse(BaseModel):
    answer: str
    success:bool

class StatementResponse(BaseModel):
    statement: str
    success:bool

class CorplistResponse(BaseModel):
    data: list[dict]
    success: bool
    err_msg: str