import os
from typing import List

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from ..schemas.request_models.request_models import FileDownloadRequest, FilePathRequest
from pydantic import BaseModel
from pathlib import Path

router = APIRouter()

ROUTER_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.abspath(os.path.join(ROUTER_DIR, "..", "..", "pdfs"))


@router.post("/upload-pdf/", tags=["File Upload"])
async def upload_pdf(files: List[UploadFile] = File(...)):
    os.makedirs(PDF_DIR, exist_ok=True)
    
    saved_file_paths = []

    # 여러 파일 업로드 처리
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
            
    return {
        "success": True,
        "file_paths": saved_file_paths,
        "message": f"Successfully uploaded {len(saved_file_paths)} files."
    }


@router.post("/download-pdf/", tags=["File Download"])
async def download_pdf(request: FileDownloadRequest):
    """
    프론트에서 file_name을 JSON으로 보내면 서버에 저장된 PDF 파일을 찾아 반환합니다.
    """
    file_path = os.path.join(PDF_DIR, request.file_name)

    # 파일 존재 여부 확인
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{request.file_name}' not found on server."
        )

    # PDF 파일을 스트리밍 방식으로 반환
    return FileResponse(
        path=file_path,
        filename=request.file_name,
        media_type="application/pdf"
    )

@router.post("/get-file-url/", tags=["File URL"])
async def get_file_url(request: FilePathRequest):
    """
    file_name을 입력받아 접근 가능한 URL 반환
    """
    # 안전하게 파일명만 추출
    safe_file_name = Path(request.file_name).name  

    # 최종 파일 경로
    file_path = os.path.join(PDF_DIR, safe_file_name)

    # 파일 존재 여부 확인
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{safe_file_name}' not found on server."
        )

    # 접근 가능한 URL 반환
    file_url = f"/pdfs/{safe_file_name}"
    return {
        "success": True,
        "file_url": file_url,
        "message": f"Access URL for '{safe_file_name}'"
    }