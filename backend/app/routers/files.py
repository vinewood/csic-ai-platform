"""文件上传路由"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse

from ..config import UPLOAD_DIR
from ..auth import get_current_user

router = APIRouter(prefix="/api/files", tags=["文件"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    ext = os.path.splitext(file.filename or "file")[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"filename": filename, "original": file.filename, "size": len(content), "url": f"/api/files/{filename}"}


@router.get("/{filename}")
async def get_file(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return {"error": "文件不存在"}
    return FileResponse(path)
