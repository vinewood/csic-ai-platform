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
# https://ws-eg0sswldqhhc6qko.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
BAILIAN_BASE = "https://ws-eg0sswldqhhc6qko.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
BAILIAN_KEY = "***REMOVED-BAILIAN-KEY***"

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
    # DeepSeek — 独立 API
    "deepseek":       {"url": "https://api.deepseek.com/chat/completions", "model": "deepseek-chat", "route": "deepseek"},
}

# 聊天历史记录（内存中，重启丢失——生产应换 Redis）
chat_histories: dict[str, list[dict]] = {}
conversation_store: dict[str, dict] = {}
conv_id_counter: int = 0


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
        api_key = BAILIAN_KEY

    # 构造消息
    history = chat_histories.get(conversation_id or user_id, [])
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

                            # qwen 格式
                            if model == "qwen":
                                if data.get("output", {}).get("choices"):
                                    delta = data["output"]["choices"][0]["message"]["content"]
                                    if delta:
                                        full_content += delta
                                        yield delta

                            # minimax 格式
                            elif model == "minimax":
                                if data.get("choices"):
                                    delta = data["choices"][0].get("delta", {}).get("content", "")
                                    if delta:
                                        full_content += delta
                                        yield delta

                            # OpenAI 格式
                            else:
                                if data.get("choices"):
                                    delta = data["choices"][0].get("delta", {}).get("content", "")
                                    if delta:
                                        full_content += delta
                                        yield delta
                        except json.JSONDecodeError:
                            continue

                # 保存到历史
                cid = conversation_id or user_id
                if cid not in chat_histories:
                    chat_histories[cid] = []
                chat_histories[cid].append({"role": "user", "content": query})
                chat_histories[cid].append({"role": "assistant", "content": full_content})
                # 只保留最近 20 轮
                if len(chat_histories[cid]) > 40:
                    chat_histories[cid] = chat_histories[cid][-40:]

        except Exception as e:
            yield f"\n\n[连接错误: {str(e)}]"


def get_conversation_list(user_id: str) -> list[dict]:
    """获取对话列表"""
    result = []
    for cid, conv in conversation_store.items():
        if conv.get("user_id") == user_id:
            result.append({
                "id": cid,
                "name": conv.get("name", "新对话"),
                "model": conv.get("model", "qwen"),
                "created_at": conv.get("created_at", ""),
            })
    return result


def create_conversation(user_id: str, model: str, name: str = "新对话") -> str:
    """创建新对话"""
    global conv_id_counter
    conv_id_counter += 1
    cid = f"conv_{conv_id_counter}"
    conversation_store[cid] = {
        "id": cid,
        "user_id": user_id,
        "name": name,
        "model": model,
        "created_at": "",
    }
    return cid


def delete_conversation(conv_id: str) -> bool:
    """删除对话"""
    if conv_id in conversation_store:
        del conversation_store[conv_id]
        if conv_id in chat_histories:
            del chat_histories[conv_id]
        return True
    return False
