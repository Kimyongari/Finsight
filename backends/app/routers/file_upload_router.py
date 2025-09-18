import os
import uuid  # 👈 1. 고유 ID 생성을 위해 uuid 모듈 추가
from typing import List  # 👈 2. 여러 파일을 받기 위해 List 타입 추가

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile

# ... (FileUploadResponse 모델 정의는 그대로 사용) ...

router = APIRouter()

ROUTER_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.abspath(os.path.join(ROUTER_DIR, "..", "..", "pdfs"))

# 👈 3. 프론트엔드와 맞추기 위해 파라미터 이름을 'files'로 변경하고, 타입을 List[UploadFile]로 지정
@router.post("/upload-pdf/", tags=["File Upload"])
async def upload_pdf(files: List[UploadFile] = File(...)):
    """
    여러 개의 PDF 파일을 업로드하여 서버의 'pdfs' 디렉토리에 고유한 이름으로 저장합니다.
    """
    os.makedirs(PDF_DIR, exist_ok=True)
    
    saved_file_paths = []

    # 👈 4. 여러 파일을 처리하기 위해 for 루프 사용
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {file.filename}. Only PDF files are allowed."
            )

        # 👈 5. 안전한 파일명 생성 (UUID + 원본 확장자)
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(PDF_DIR, safe_filename)

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
            
    # 👈 6. 모든 파일 업로드 성공 후 종합적인 응답 반환
    response = {
        "success": True,
        "file_paths": saved_file_paths,
        "message": f"Successfully uploaded {len(saved_file_paths)} files."
    }
    return response