from pydantic import BaseModel

class RAGResponse(BaseModel):
    answer: str
    success:bool
    retrieved_documents: list[dict]

class StatementResponse(BaseModel):
    statement: str
    success:bool

class CorplistResponse(BaseModel):
    data: list[dict]
    success: bool
    err_msg: str

class FileUploadResponse(BaseModel):
    success: bool
    file_path: str
    message: str