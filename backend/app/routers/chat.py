"""对话路由：直连 LLM API SSE 流式"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..schemas import ChatRequest
from ..auth import get_current_user
from ..services.dify_service import chat_stream, get_conversation_list, delete_conversation, create_conversation

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post("/stream")
async def chat_stream_endpoint(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """SSE 流式对话 —— 直接调用 LLM API"""
    user_id = str(current_user.get("id", "default"))
    conv_id = req.conversation_id or ""

    async def event_generator():
        async for chunk in chat_stream(
            query=req.query,
            model=req.model or "qwen",
            conversation_id=conv_id,
            user_id=user_id,
            temperature=req.temperature or 0.7,
            top_p=req.top_p or 0.9,
            max_tokens=req.max_tokens or 2048,
        ):
            if chunk:
                yield f"data: {json.dumps({'answer': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """获取对话列表"""
    user_id = str(current_user.get("id", "default"))
    return get_conversation_list(user_id)


@router.post("/conversations")
async def new_conversation(model: str = "qwen", name: str = "新对话", current_user: dict = Depends(get_current_user)):
    """新建对话"""
    user_id = str(current_user.get("id", "default"))
    cid = create_conversation(user_id, model, name)
    return {"id": cid, "name": name}


@router.delete("/conversations/{conv_id}")
async def remove_conversation(conv_id: str, current_user: dict = Depends(get_current_user)):
    """删除对话"""
    ok = delete_conversation(conv_id)
    if not ok:
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"message": "已删除"}


@router.get("/models")
async def list_models():
    return {
        "models": [
            {"id": "qwen",     "label": "千问",    "color": "#1677ff"},
            {"id": "zhipu",    "label": "智谱",    "color": "#5b4cc4"},
            {"id": "minimax",  "label": "MiniMax", "color": "#10b981"},
            {"id": "doubao",   "label": "豆包",    "color": "#8b5cf6"},
            {"id": "deepseek", "label": "DeepSeek","color": "#4a6cf7"},
            {"id": "kimi",     "label": "Kimi",    "color": "#f59e0b"},
        ]
    }
