import os
from typing import List 

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile

# ... (FileUploadResponse 모델 정의는 그대로 사용) ...

router = APIRouter()

ROUTER_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.abspath(os.path.join(ROUTER_DIR, "..", "..", "pdfs"))

@router.post("/upload-pdf/", tags=["File Upload"])
async def upload_pdf(files: List[UploadFile] = File(...)):
    os.makedirs(PDF_DIR, exist_ok=True)
    
    saved_file_paths = []

    # 여러 파일을 처리
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {file.filename}. Only PDF files are allowed."
            )

        file_path = os.path.join(PDF_DIR, file.filename)

        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            saved_file_paths.append(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"There was an error uploading the file {file.filename}: {e}"
            )
            
    # 모든 파일 업로드 성공 후 종합적인 응답 반환
    response = {
        "success": True,
        "file_paths": saved_file_paths,
        "message": f"Successfully uploaded {len(saved_file_paths)} files."
    }
    return response