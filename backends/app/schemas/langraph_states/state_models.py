from pydantic import BaseModel

class advanced_rag_state(BaseModel):
    user_question: str
    retrieved_documents :list[dict]
    answer : str
    references : list[dict]

class vanilla_rag_state(BaseModel):
    user_question: str
    retrieved_documents :list[dict]
    answer : str