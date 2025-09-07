from pydantic import BaseModel

class RAGResponse(BaseModel):
    answer: str
    success:bool

