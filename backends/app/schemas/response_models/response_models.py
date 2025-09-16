from pydantic import BaseModel

class RAGResponse(BaseModel):
    answer: str
    success:bool

class StatementResponse(BaseModel):
    statement: str
    success:bool