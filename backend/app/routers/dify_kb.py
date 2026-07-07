"""Dify 全能力集成路由 — 对话/知识库/文档解析/视频分析"""

import json, os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from typing import Optional

from ..database import get_db, async_session
from ..models import KnowledgeBase, KnowledgeDoc, ApiConfig
from ..auth import get_current_user
from ..config import DIFY_BASE_URL, UPLOAD_DIR

router = APIRouter(prefix="/api/dify", tags=["Dify集成"])


# ---- Helpers ----

async def get_dify_key() -> str:
    """从 ApiConfig 表获取 Dify API Key"""
    async with async_session() as session:
        result = await session.execute(
            select(ApiConfig).where(ApiConfig.provider == "dify")
        )
        cfg = result.scalar_one_or_none()
        if cfg and cfg.config_json:
            return cfg.config_json.get("key", "")
    return ""


def _dify_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


# ========== 1. 服务状态 ==========

@router.get("/health")
async def dify_health():
    """检查 Dify 服务状态"""
    endpoints = [
        ("API", f"{DIFY_BASE_URL}/health"),
        ("Console", f"{DIFY_BASE_URL}/api/healthz"),
    ]
    results = {}
    for name, url in endpoints:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(url)
                results[name] = "ok" if r.status_code < 500 else "error"
        except Exception as e:
            results[name] = f"disconnected ({str(e)[:30]})"
    return {"status": "ok" if any("ok" in v for v in results.values()) else "error", **results}


# ========== 2. Dify 对话（带 RAG 知识库） ==========

@router.post("/chat")
async def dify_chat(
    query: str,
    user: str = "default",
    conversation_id: str = "",
    files: Optional[list] = None,
    current_user: dict = Depends(get_current_user),
):
    """通过 Dify API 进行对话（支持知识库 RAG）"""
    api_key = await get_dify_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置 Dify API Key")

    payload = {
        "query": query,
        "response_mode": "blocking",
        "user": user,
        "inputs": {},
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if files:
        payload["files"] = files

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{DIFY_BASE_URL}/v1/chat-messages",
                headers=_dify_headers(api_key),
                json=payload,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"Dify API {resp.status_code}", "detail": resp.text[:200]}
    except Exception as e:
        return {"error": str(e)}


# ========== 3. 知识库 CRUD ==========

@router.post("/datasets")
async def create_dataset(name: str, description: str = "", current_user: dict = Depends(get_current_user)):
    """在 Dify 中创建知识库"""
    api_key = await get_dify_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置 Dify API Key")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DIFY_BASE_URL}/v1/datasets",
            headers=_dify_headers(api_key),
            json={"name": name, "description": description},
        )
        if resp.status_code in (200, 201):
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:200])


@router.get("/datasets")
async def list_datasets(page: int = 1, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """列出 Dify 知识库"""
    api_key = await get_dify_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置 Dify API Key")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{DIFY_BASE_URL}/v1/datasets?page={page}&limit={limit}",
            headers=_dify_headers(api_key),
        )
        return resp.json() if resp.status_code == 200 else {"error": resp.text[:200]}


@router.post("/datasets/{dataset_id}/documents")
async def upload_document(
    dataset_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """上传文档到 Dify 知识库"""
    api_key = await get_dify_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置 Dify API Key")

    content = await file.read()
    files_payload = {"file": (file.filename or "doc", content, "application/octet-stream")}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{DIFY_BASE_URL}/v1/datasets/{dataset_id}/document/create_by_file",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files_payload,
        )
        return resp.json() if resp.status_code in (200, 201) else {"error": resp.text[:200]}


# ========== 4. 文档解析（OCR / 预览） ==========

@router.post("/parse-document")
async def parse_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """通过 Dify 解析文档内容"""
    api_key = await get_dify_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置 Dify API Key")

    content = await file.read()
    ext = os.path.splitext(file.filename or "doc")[1].lower()

    # 支持的文档类型
    supported = {".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".xlsx", ".pptx", ".html"}
    if ext not in supported:
        return {"error": f"不支持的文件格式: {ext}", "supported": list(supported)}

    files_payload = {"file": (file.filename or "doc", content, "application/octet-stream")}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{DIFY_BASE_URL}/v1/files/upload",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files_payload,
        )
        return resp.json() if resp.status_code in (200, 201) else {"error": resp.text[:200]}


# ========== 5. 同步本地知识库到 Dify ==========

@router.post("/sync-knowledge")
async def sync_knowledge_to_dify(
    kb_id: int = Query(..., description="本地知识库ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将本地知识库同步到 Dify"""
    api_key = await get_dify_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置 Dify API Key")

    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 在 Dify 中创建数据集
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DIFY_BASE_URL}/v1/datasets",
            headers=_dify_headers(api_key),
            json={"name": kb.name, "description": kb.description or ""},
        )
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=f"Dify 创建知识库失败: {resp.text[:200]}")
        dify_dataset = resp.json()

    # 上传文档
    docs_result = await db.execute(
        select(KnowledgeDoc).where(KnowledgeDoc.kb_id == kb_id)
    )
    docs = docs_result.scalars().all()
    uploaded = 0
    for doc in docs:
        if doc.filepath and os.path.exists(doc.filepath):
            with open(doc.filepath, "rb") as f:
                content = f.read()
            async with httpx.AsyncClient(timeout=120) as client2:
                doc_resp = await client2.post(
                    f"{DIFY_BASE_URL}/v1/datasets/{dify_dataset['id']}/document/create_by_file",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": (doc.filename or "doc", content, "application/octet-stream")},
                )
                if doc_resp.status_code in (200, 201):
                    uploaded += 1

    return {
        "message": f"知识库同步完成，上传 {uploaded}/{len(docs)} 个文档",
        "dify_dataset_id": dify_dataset.get("id", ""),
        "dify_dataset_name": dify_dataset.get("name", ""),
    }


# ========== 6. 视频分析（预留阿里云API对接） ==========

@router.post("/analyze-video")
async def analyze_video_with_dify(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    视频分析 — 当前使用 Dify 的文档解析能力进行预处理
    后续对接阿里云语音识别 API 实现完整转录
    """
    api_key = await get_dify_key()
    if not api_key:
        raise HTTPException(status_code=400, detail="请先配置 Dify API Key")

    content = await file.read()
    files_payload = {"file": (file.filename or "video.mp4", content, "video/mp4")}

    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{DIFY_BASE_URL}/v1/files/upload",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files_payload,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            # 返回文件ID，后续可对接阿里云 ASR
            return {
                "file_id": data.get("id", ""),
                "file_name": file.filename,
                "size": len(content),
                "note": "文件已上传到 Dify，如需语音转文字请配置阿里云 ASR API",
            }
        return {"error": resp.text[:200]}
