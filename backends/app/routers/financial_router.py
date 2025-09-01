from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def get_financial_status():
    return {"message": "Financial router is active"}

@router.post("/statement")
async def get_financial_statement(request: dict):
    # This is a placeholder for your financial service logic
    company_code = request.get("company_code", "")
    return {"response": f"Fetching statement for company: {company_code}", "status": "dummy response"}
