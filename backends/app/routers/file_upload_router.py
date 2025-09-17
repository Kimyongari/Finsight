from fastapi import APIRouter, UploadFile, File, HTTPException
from ..schemas.response_models.response_models import FileUploadResponse

import aiofiles
import os
from typing import List

router = APIRouter()

# 이 파일의 위치를 기준으로 backends/pdfs 디렉토리의 상대 경로를 설정합니다.
# 이렇게 하면 어떤 위치에서 서버를 실행하더라도 항상 올바른 경로를 참조할 수 있습니다.
ROUTER_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.abspath(os.path.join(ROUTER_DIR, "..", "..", "pdfs"))

@router.post("/upload-pdf/", tags=["File Upload"])
async def upload_pdf(file: UploadFile = File(...)) -> FileUploadResponse:
    """
    PDF 파일을 업로드하여 서버의 'pdfs' 디렉토리에 저장합니다.
    """
    # 디렉토리가 존재하지 않으면 생성
    os.makedirs(PDF_DIR, exist_ok=True)
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    file_path = os.path.join(PDF_DIR, file.filename)

    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()  # 파일을 읽음
            await out_file.write(content)  # 파일에 씀
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"There was an error uploading the file: {e}")
    response = FileUploadResponse(success = True, file_path= file_path, message=f"Successfully uploaded {file.filename}")
    return response

    