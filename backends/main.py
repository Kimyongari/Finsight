from fastapi import FastAPI
from app.routers import rag_router, financial_router, web_agent_router
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


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the main API."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
