"""统一集成服务 — Dify/RSSHub/gpt_academic/ASR 全部通过开源项目实现"""

import httpx
import asyncio
import json
import os
from typing import Optional, AsyncGenerator

DIFY_URL = "http://127.0.0.1:5001"
RSSHUB_URL = "http://127.0.0.1:1200"
ACADEMIC_URL = "http://127.0.0.1:8765"

# ---- Dify 全能力服务 ----

class DifyService:
    """Dify 集成：对话/知识库/文件解析/视频分析/工作流"""

    @staticmethod
    async def chat_stream(query: str, user: str = "admin", conversation_id: str = "") -> AsyncGenerator[str, None]:
        """流式对话（SSE），完全由 Dify 处理"""
        api_key = _get_dify_key()
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{DIFY_URL}/v1/chat-messages",
                json={
                    "inputs": {},
                    "query": query,
                    "response_mode": "streaming",
                    "user": user,
                    "conversation_id": conversation_id,
                },
                headers={"Authorization": f"Bearer {api_key}"}
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("event") == "message":
                                yield data.get("answer", "")
                        except json.JSONDecodeError:
                            pass

    @staticmethod
    async def chat_blocking(query: str, user: str = "admin") -> dict:
        """阻塞式对话"""
        api_key = _get_dify_key()
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{DIFY_URL}/v1/chat-messages",
                json={"inputs": {}, "query": query, "response_mode": "blocking", "user": user},
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return resp.json()

    @staticmethod
    async def upload_file(file_path: str, user: str = "admin") -> dict:
        """上传文件到 Dify 解析（PDF/DOCX/TXT/图片）"""
        api_key = _get_dify_key()
        async with httpx.AsyncClient(timeout=60) as client:
            with open(file_path, "rb") as f:
                resp = await client.post(
                    f"{DIFY_URL}/v1/files/upload",
                    files={"file": (os.path.basename(file_path), f)},
                    data={"user": user},
                    headers={"Authorization": f"Bearer {api_key}"}
                )
            return resp.json()

    @staticmethod
    async def create_dataset(name: str) -> dict:
        """创建知识库"""
        api_key = _get_dify_key()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{DIFY_URL}/v1/datasets",
                json={"name": name},
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return resp.json()

    @staticmethod
    async def add_document(dataset_id: str, file_path: str) -> dict:
        """上传文档到知识库"""
        api_key = _get_dify_key()
        upload_id = os.path.basename(file_path)
        async with httpx.AsyncClient(timeout=120) as client:
            # Step 1: upload file
            with open(file_path, "rb") as f:
                resp = await client.post(
                    f"{DIFY_URL}/v1/files/upload",
                    files={"file": (upload_id, f)},
                    data={"user": "admin"},
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                file_info = resp.json()

            # Step 2: create document
            if file_info.get("id"):
                resp = await client.post(
                    f"{DIFY_URL}/v1/datasets/{dataset_id}/document/create-by-file",
                    json={
                        "file_id": file_info["id"],
                        "indexing_technique": "high_quality",
                        "process_rule": {"mode": "automatic"}
                    },
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                return resp.json()
            return file_info

    @staticmethod
    async def search_knowledge(query: str, dataset_ids: list[str] = None) -> dict:
        """搜索知识库"""
        api_key = _get_dify_key()
        if not dataset_ids:
            datasets = await _list_datasets(api_key)
            dataset_ids = [d["id"] for d in datasets.get("data", [])[:1]]
        if not dataset_ids:
            return {"records": []}

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{DIFY_URL}/v1/datasets/{dataset_ids[0]}/retrieve",
                json={"query": query, "retrieval_model": {"top_k": 5}},
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return resp.json()

    @staticmethod
    async def list_datasets(page: int = 1, limit: int = 20) -> dict:
        """列出所有知识库"""
        api_key = _get_dify_key()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{DIFY_URL}/v1/datasets?page={page}&limit={limit}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return resp.json()

    @staticmethod
    async def delete_dataset(dataset_id: str) -> dict:
        """删除知识库"""
        api_key = _get_dify_key()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(
                f"{DIFY_URL}/v1/datasets/{dataset_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return resp.json()

    @staticmethod
    async def audio_to_text(file_path: str) -> dict:
        """Dify 音频转文字（使用 Dify 的音频能力）"""
        api_key = _get_dify_key()
        async with httpx.AsyncClient(timeout=120) as client:
            with open(file_path, "rb") as f:
                resp = await client.post(
                    f"{DIFY_URL}/v1/audio-to-text",
                    files={"file": (os.path.basename(file_path), f)},
                    data={"user": "admin"},
                    headers={"Authorization": f"Bearer {api_key}"}
                )
            return resp.json()


# ---- RSSHub 服务 ----

class RSSHubService:
    """RSS 订阅通过本地 RSSHub 实例"""

    @staticmethod
    async def fetch(route: str, params: dict = None) -> dict:
        """从 RSSHub 获取数据，route 如 /xinhua/news"""
        if not params:
            params = {}
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{RSSHUB_URL}{route}", params=params)
                return {"status": "ok", "data": resp.text[:5000]}
            except Exception:
                return {"status": "offline", "data": "", "error": "RSSHub 未启动"}

    @staticmethod
    async def fetch_json(route: str, params: dict = None) -> dict:
        """从 RSSHub 获取 JSON 数据"""
        if not params:
            params = {}
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{RSSHUB_URL}{route}", params=params)
                return resp.json()
            except Exception:
                return {"status": "offline"}


# ---- gpt_academic 服务 ----

class AcademicService:
    """科研辅助通过 gpt_academic 引擎"""

    @staticmethod
    async def generate_topics(direction: str, count: int = 4) -> dict:
        """生成科研选题"""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{ACADEMIC_URL}/api/generate_topics",
                    json={"direction": direction, "count": count}
                )
                return resp.json()
        except Exception:
            return {"status": "offline", "message": "gpt_academic 未启动请启用 DeepSeek 回退"}


# ---- 阿里云 ASR 服务 ----

class ASRService:
    """语音识别 — 阿里云百炼 Paraformer"""

    @staticmethod
    async def transcribe_file(file_path: str) -> dict:
        """转写音频文件为文字"""
        try:
            import dashscope
            from dashscope.audio.asr import Recognition
            from http import HTTPStatus

            result = Recognition(model="paraformer-realtime-v2", format="wav", sample_rate=16000).call(file_path)
            if result.status_code == HTTPStatus.OK:
                return {"status": "ok", "text": result.get_sentence().get("text", "")}
            return {"status": "error", "message": result.message}
        except Exception as e:
            return {"status": "offline", "message": str(e)}


# ---- 内部工具 ----

def _get_dify_key() -> str:
    """从数据库或环境变量获取 Dify API Key"""
    try:
        # 尝试从环境变量
        key = os.getenv("DIFY_API_KEY")
        if key:
            return key
        # 从 SQLite 读取
        import sqlite3
        conn = sqlite3.connect("data/csic.db")
        row = conn.execute("SELECT value FROM api_configs WHERE provider='dify' LIMIT 1").fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return "***REMOVED-DIFY-KEY***"


async def _list_datasets(key: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{DIFY_URL}/v1/datasets", headers={"Authorization": f"Bearer {key}"})
        return resp.json()
