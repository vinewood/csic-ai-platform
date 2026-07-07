"""对话路由：优先走 Dify AI 对话 + 知识库增强，fallback 直连 LLM"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..schemas import ChatRequest
from ..auth import get_current_user
from ..services.integrations import DifyService
from ..services.dify_service import chat_stream as direct_chat, get_conversation_list, create_conversation, delete_conversation

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post("/stream")
async def chat_stream_endpoint(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """SSE 流式对话 —— Dify AI 优先，fallback 直连 LLM"""
    user_id = str(current_user.get("id", "default"))
    conv_id = req.conversation_id or ""

    async def event_generator():
        try:
            # 先尝试 Dify 流式对话（支持知识库 RAG）
            done = False
            async for chunk in DifyService.chat_stream(
                query=req.query, user=user_id, conversation_id=conv_id
            ):
                if chunk:
                    yield f"data: {json.dumps({'content': chunk, 'model': 'dify'})}\n\n"
                    done = True

            if done:
                return
        except Exception:
            pass  # Dify 不可用，回退到直连

        # Fallback: 直连 LLM
        async for chunk in direct_chat(
            query=req.query, model=req.model or "qwen",
            conversation_id=conv_id, user_id=user_id,
            temperature=req.temperature or 0.7,
            top_p=req.top_p or 0.9, max_tokens=req.max_tokens or 2048,
        ):
            if chunk:
                yield f"data: {json.dumps({'content': chunk, 'model': req.model})}\n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/blocking")
async def chat_blocking(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """阻塞式对话"""
    try:
        result = await DifyService.chat_blocking(query=req.query, user=str(current_user.get("id", "default")))
        return result
    except Exception:
        raise HTTPException(status_code=502, detail="Dify 服务不可用")


@router.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """列出用户的对话历史"""
    user_id = str(current_user.get("id", "default"))
    return get_conversation_list(user_id)


@router.delete("/conversations/{conversation_id}")
async def del_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """删除对话"""
    user_id = str(current_user.get("id", "default"))
    await delete_conversation(conversation_id)
    return {"status": "ok"}
