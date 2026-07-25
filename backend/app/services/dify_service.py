"""
LLM API 直连服务 —— 替代 Dify
直接调用各家大模型 HTTP API，无需 Dify 容器
"""

import json
import os
import httpx
from typing import AsyncGenerator, Optional
from ..config import get_api_config


# 模型 API 配置模板 — 百炼 OpenAI 兼容统一路由
# 铁律：任何 API Key 只允许存在本地/服务器（api_configs 表），禁止硬编码进源码
BAILIAN_BASE = "https://ws-eg0sswldqhhc6qko.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"

MODEL_ENDPOINTS = {
    # 千问 3.7 — 百炼
    "qwen-plus":      {"url": f"{BAILIAN_BASE}/chat/completions", "model": "qwen3.7-plus", "route": "bailian"},
    "qwen-max":       {"url": f"{BAILIAN_BASE}/chat/completions", "model": "qwen3.7-max", "route": "bailian"},
    "qwen-turbo":     {"url": f"{BAILIAN_BASE}/chat/completions", "model": "qwen3.6-flash", "route": "bailian"},
    "qwen-coder-plus":{"url": f"{BAILIAN_BASE}/chat/completions", "model": "qwen3.7-plus", "route": "bailian"},
    "qwen":           {"url": f"{BAILIAN_BASE}/chat/completions", "model": "qwen3.7-plus", "route": "bailian"},
    # 第三方 — 百炼
    "glm-4":          {"url": f"{BAILIAN_BASE}/chat/completions", "model": "glm-5.2", "route": "bailian"},
    "zhipu":          {"url": f"{BAILIAN_BASE}/chat/completions", "model": "glm-5.2", "route": "bailian"},
    "kimi":           {"url": f"{BAILIAN_BASE}/chat/completions", "model": "kimi-k2.7-code", "route": "bailian"},
    "minimax":        {"url": f"{BAILIAN_BASE}/chat/completions", "model": "MiniMax-M2.5", "route": "bailian"},
    # DeepSeek — 独立 API（该账号仅支持 deepseek-v4-pro / deepseek-v4-flash）
    "deepseek":       {"url": "https://api.deepseek.com/chat/completions", "model": "deepseek-v4-pro", "route": "deepseek"},
}

# 对话历史统一走 DB 单轨（v3.2.0）：内存字典 chat_histories/conversation_store 已废弃删除
# 历史在 chat_stream 内按需从 messages 表读取，对话的增删改查全部落 DB


async def _load_history(conversation_id: str, model: str, current_query: str) -> list[dict]:
    """从 DB 加载对话历史（最近 12 轮以内）

    多模型对比会话中同一轮有多条 assistant（每个模型一条），
    为保证单模型上下文连贯，assistant 只取当前模型（或未标记模型的旧数据）。
    末尾若与当前 query 相同的 user 消息（chat.py 已提前落库）则剔除，避免重复。
    """
    if not conversation_id or not conversation_id.isdigit():
        return []
    try:
        from ..database import async_session
        from ..models import Message
        from sqlalchemy import select
        async with async_session() as s:
            rows = (await s.execute(
                select(Message).where(Message.conversation_id == int(conversation_id))
                .order_by(Message.id.desc()).limit(40)
            )).scalars().all()
        msgs = []
        for m in reversed(rows):  # 恢复时间正序
            if m.role == "assistant" and m.model and m.model != model:
                continue  # 跳过其他模型的回答
            msgs.append({"role": m.role, "content": m.content})
        if msgs and msgs[-1]["role"] == "user" and msgs[-1]["content"] == current_query:
            msgs = msgs[:-1]
        return msgs[-24:]
    except Exception:
        return []


async def chat_stream(
    query: str,
    model: str = "deepseek",
    conversation_id: str = "",
    user_id: str = "default",
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 2048,
) -> AsyncGenerator[str, None]:
    """直接调用 LLM API，SSE 流式返回"""
    endpoint = MODEL_ENDPOINTS.get(model, MODEL_ENDPOINTS["deepseek"])
    
    # DeepSeek 独立 Key，其余走百炼统一 Key
    if endpoint.get("route") == "deepseek":
        api_key = get_api_config("deepseek") or os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            yield f"\n\n[DeepSeek V4 Pro 需独立 API Key：系统管理 → API 配置 → DeepSeek]"
            return
    else:
        # 百炼统一路由：key 从 api_configs 表读取（provider 优先级 bailian > dashscope > qwen）
        api_key = get_api_config("bailian") or get_api_config("dashscope") or get_api_config("qwen")
        if not api_key:
            yield f"\n\n[百炼 API Key 未配置：系统管理 → API 配置 → DashScope/百炼]"
            return

    # 构造消息（历史从 DB 单轨读取）
    history = await _load_history(conversation_id, model, query)
    messages = history + [{"role": "user", "content": query}]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # OpenAI 兼容格式
    payload = {
        "model": endpoint["model"],
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", endpoint["url"], headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    error_text = await resp.aread()
                    yield f"\n\n[API 错误 {resp.status_code}: {error_text.decode()[:200]}]"
                    return

                full_content = ""
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            # 百炼 compatible-mode 与 DeepSeek 均为 OpenAI 流式格式，统一解析
                            if data.get("choices"):
                                delta = data["choices"][0].get("delta", {}).get("content", "")
                                if delta:
                                    full_content += delta
                                    yield delta
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            yield f"\n\n[连接错误: {str(e)}]"


async def delete_conversation(conv_id: str) -> bool:
    """删除对话及其全部消息（DB 单轨）"""
    if not conv_id or not str(conv_id).isdigit():
        return False
    try:
        from ..database import async_session
        from ..models import Conversation, Message
        from sqlalchemy import delete
        async with async_session() as s:
            await s.execute(delete(Message).where(Message.conversation_id == int(conv_id)))
            await s.execute(delete(Conversation).where(Conversation.id == int(conv_id)))
            await s.commit()
        return True
    except Exception:
        return False
