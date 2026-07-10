"""Dify 全能力集成路由 — 数据集代理/知识库/文档/对话"""

import json, os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from typing import Optional

from ..database import get_db
from ..models import KnowledgeBase, KnowledgeDoc, ApiConfig
from ..auth import get_current_user
from ..config import DIFY_BASE_URL

router = APIRouter(prefix="/api/dify", tags=["Dify集成"])


# ---- Dify 控制台代理 ----
# 后端统一管理 Dify 访问令牌，前端无需关心 Dify 登录

_dify_token = {"token": "", "expires": 0}

async def _ensure_dify_token() -> str:
    """获取有效的 Dify 控制台访问令牌（自动登录）"""
    import time
    if _dify_token["token"] and time.time() < _dify_token["expires"]:
        return _dify_token["token"]

    resp = await _dify_post("/console/api/login", {
        "email": "admin@csic.cn",
        "password": "***REMOVED-PASSWORD***"
    })
    token = resp.get("access_token", "")
    if token:
        _dify_token["token"] = token
        _dify_token["expires"] = time.time() + 3600  # 1小时
        return token
    return ""


async def _dify_get(path: str, token: str = "") -> dict:
    """Dify GET 请求"""
    t = token or await _ensure_dify_token()
    headers = {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"http://127.0.0.1:5001{path}", headers=headers)
        return r.json() if r.status_code < 400 else {"error": r.text[:200]}


async def _dify_post(path: str, body: dict) -> dict:
    """Dify POST 请求"""
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"http://127.0.0.1:5001{path}", json=body,
            headers={"Content-Type": "application/json"})
        return r.json() if r.status_code < 400 else {"error": r.text[:200]}

async def _dify_req(method: str, path: str, token: str, body=None, files=None) -> dict:
    """通用 Dify API 请求（带token）"""
    headers = {"Authorization": f"Bearer {token}"}
    if not files:
        headers["Content-Type"] = "application/json"
    async with httpx.AsyncClient(timeout=120) as c:
        if method == "GET":
            r = await c.get(f"{DIFY_BASE_URL}{path}", headers=headers)
        elif method == "POST" and files:
            r = await c.post(f"{DIFY_BASE_URL}{path}", headers=headers, files=files)
        else:
            r = await c.post(f"{DIFY_BASE_URL}{path}", headers=headers, json=body or {})
        return r.json() if r.status_code < 400 else {"error": r.text[:200]}


# ========== 1. 数据集列表（从 Dify 控制台代理） ==========

@router.get("/datasets")
async def list_datasets(page: int = 1, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """从 Dify 获取数据集列表"""
    result = await _dify_get(f"/console/api/datasets?page={page}&limit={limit}")
    return result


# ========== 2. 创建数据集 ==========

@router.post("/datasets/create")
async def create_dataset(
    name: str = Query(...), description: str = Query(""),
    current_user: dict = Depends(get_current_user)
):
    """通过 Dify 控制台 API 创建数据集"""
    token = await _ensure_dify_token()
    if not token:
        raise HTTPException(status_code=502, detail="无法连接到 Dify")
    result = await _dify_post("/console/api/datasets", {
        "name": name, "description": description,
    })
    return result


# ========== 3. 上传文档到数据集 ==========

@router.post("/datasets/{dataset_id}/upload")
async def upload_to_dataset(
    dataset_id: str, file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """上传文档到 Dify 数据集"""
    token = await _ensure_dify_token()
    if not token:
        raise HTTPException(status_code=502, detail="无法连接到 Dify")
    
    content = await file.read()
    files = {"file": (file.filename or "doc", content, "application/octet-stream")}
    data = {"data_source": {"type": "upload_file"}}

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            f"http://127.0.0.1:5001/console/api/datasets/{dataset_id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            data=data, files=files,
        )
        return r.json() if r.status_code < 400 else {"error": r.text[:200]}


# ========== 4. Dify 对话（带知识库 RAG） ==========

@router.post("/chat")
async def dify_rag_chat(
    query: str = Query(...), dataset_id: str = Query(""),
    user: str = "default", conversation_id: str = "",
    current_user: dict = Depends(get_current_user),
):
    """通过 Dify API 进行 RAG 对话"""
    token = await _ensure_dify_token()
    if not token:
        raise HTTPException(status_code=502, detail="无法连接到 Dify")

    body = {
        "query": query, "response_mode": "blocking", "user": user, "inputs": {}
    }
    if conversation_id:
        body["conversation_id"] = conversation_id
    if dataset_id:
        body["inputs"]["dataset_id"] = dataset_id

    result = await _dify_post("/console/api/chat-messages", body)
    return result


# ========== 5. 教学/科研可用数据集列表（简洁版） ==========

@router.get("/datasets/list")
async def list_datasets_simple(current_user: dict = Depends(get_current_user)):
    """返回数据集简要列表，供教学/科研工作台选择"""
    result = await _dify_get(f"/console/api/datasets?page=1&limit=50")
    if result.get("data"):
        return [{"id": d["id"], "name": d["name"], "count": d.get("document_count", 0)} for d in result["data"]]
    return []


# ========== 6. 健康检查 ==========

@router.get("/health")
async def dify_health():
    """检查 Dify 服务状态"""
    results = {}
    for name, url in [("API", f"{DIFY_BASE_URL}/health"), ("Console", f"http://127.0.0.1:5001/health")]:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(url)
                results[name] = "ok" if r.status_code < 500 else "error"
        except:
            results[name] = "offline"
    return {"status": "ok" if any(v == "ok" for v in results.values()) else "error", **results}

