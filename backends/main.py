from fastapi import FastAPI
from app.routers import rag_router, financial_router, web_agent_router, report_router, file_upload_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Financial Agent API",
    description="An API utilizing RAG, Financial, and Web Agent services.",
    version="1.0.0",
)

# Include routers
app.include_router(rag_router.router, prefix="/rag", tags=["RAG Service"])
app.include_router(financial_router.router, prefix="/financial", tags=["Financial Service"])
app.include_router(web_agent_router.router, prefix="/web-agent", tags=["Web Agent Service"])
app.include_router(report_router.router, prefix="/report", tags=["Report Generation Service"])
app.include_router(file_upload_router.router, prefix="/files", tags=["File Upload"])

origins = [
    "http://127.0.0.1:5173", # 프론트엔드 주소 (개발 환경에 맞게 변경)
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the main API."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
