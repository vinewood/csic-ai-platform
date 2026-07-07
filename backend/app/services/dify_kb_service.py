"""
Dify API 集成服务
对接本地部署的 Dify 实例，提供知识库 RAG 和 LLM 路由
"""

import json
import httpx
from typing import AsyncGenerator, Optional
from ..config import DIFY_BASE_URL

DIFY_API_URL = DIFY_BASE_URL or "http://localhost:5001"


async def dify_chat_stream(
    query: str,
    api_key: str,
    user_id: str = "default",
    conversation_id: str = "",
    files: Optional[list] = None,
) -> AsyncGenerator[str, None]:
    """通过 Dify API 进行流式对话（支持知识库 RAG）"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "response_mode": "streaming",
        "user": user_id,
        "inputs": {},
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if files:
        payload["files"] = files

    url = f"{DIFY_API_URL}/v1/chat-messages"
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    yield f"\n\n[Dify API 错误: {resp.status_code}]"
                    return
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            yield data.get("answer", "")
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n\n[Dify 连接错误: {str(e)}]"


async def dify_create_knowledge_base(name: str, description: str = "") -> dict:
    """通过 Dify API 创建知识库"""
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
    payload = {"name": name, "description": description}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{DIFY_API_URL}/v1/datasets", headers=headers, json=payload)
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.text}


async def dify_upload_document(dataset_id: str, file_path: str, file_name: str) -> dict:
    """上传文档到 Dify 知识库"""
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "application/octet-stream")}
            resp = await client.post(
                f"{DIFY_API_URL}/v1/datasets/{dataset_id}/document/create_by_file",
                headers=headers,
                files=files,
            )
        if resp.status_code == 200:
            return resp.json()
        return {"error": resp.text}


async def dify_search_knowledge(query: str, dataset_id: str, top_k: int = 5) -> list:
    """搜索 Dify 知识库"""
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
    payload = {"query": query, "top_k": top_k}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{DIFY_API_URL}/v1/datasets/{dataset_id}/retrieve",
            headers=headers,
            json=payload,
        )
        if resp.status_code == 200:
            return resp.json().get("records", [])
        return []


# 懒加载 DIFY_API_KEY（首次调用时从数据库加载）
DIFY_API_KEY = ""
_loaded = False


async def ensure_dify_key():
    global DIFY_API_KEY, _loaded
    if not _loaded:
        from ..config import get_api_config
        DIFY_API_KEY = get_api_config("dify") or ""
        _loaded = True
