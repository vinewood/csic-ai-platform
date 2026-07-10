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
    """阻塞式对话 — 直连 DeepSeek LLM"""
    query = req.query
    user_id = str(current_user.get("id", "default"))
    
    try:
        from ..services.dify_service import chat_stream
        full = ""
        async for chunk in chat_stream(query=query, model=req.model or "deepseek", user_id=user_id):
            full += chunk
        if full.strip():
            return {"result": full, "model": req.model or "deepseek"}
    except Exception as e:
        pass
    
    # Last resort: call our academic engine
    try:
        from ..services.academic_service import AcademicEngine
        result = await AcademicEngine.chat(query)
        if result and "请先配置" not in result:
            return {"result": result, "model": "deepseek"}
    except Exception:
        pass
    
    raise HTTPException(status_code=502, detail="所有 AI 服务暂不可用，请检查 DeepSeek API Key 配置")


@router.post("/dify-chat")
async def dify_chat_stream(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """SSE 流式对话 — 直连 LLM，保存对话历史"""
    query = req.query
    user_id = str(current_user.get("id", "default"))
    model = req.model or "deepseek"
    
    # 检查是否有技能挂载
    skill_prompt = ""
    if getattr(req, 'skill_id', None):
        try:
            from ..models import Skill
            from ..database import async_session
            from sqlalchemy import select
            async with async_session() as s:
                result = await s.execute(select(Skill).where(Skill.id == req.skill_id))
                skill = result.scalar_one_or_none()
                if skill and skill.prompt:
                    skill_prompt = skill.prompt
        except Exception:
            pass
    
    async def generate():
        from ..services.dify_service import chat_stream
        from ..models import Message, Conversation
        from ..database import async_session
        from sqlalchemy import select
        
        full_response = ""
        conversation_id = req.conversation_id or ""
        thinking = False
        
        async with async_session() as db:
            # 创建或获取对话
            if not conversation_id or conversation_id == "new":
                conv = Conversation(user_id=int(user_id), title=query[:30], model=model)
                db.add(conv)
                await db.flush()
                conversation_id = str(conv.id)
                thinking = True
                yield f"data: {json.dumps({'type':'meta','conversation_id':conversation_id})}\n\n"
            
            # 保存用户消息
            user_msg = Message(conversation_id=int(conversation_id), role="user", content=query)
            db.add(user_msg)
            await db.commit()
        
        try:
            async for chunk in chat_stream(
                query=query, model=model, user_id=user_id,
                conversation_id=conversation_id
            ):
                if chunk:
                    full_response += chunk
                    # 跳过系统提示
                    if "[请先配置" in chunk:
                        full_response = chunk
                        yield f"data: {json.dumps({'content':chunk})}\n\n"
                        break
                    yield f"data: {json.dumps({'content':chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'content':f'[错误] {e}'})}\n\n"
        
        # 保存 AI 回复
        if full_response.strip():
            async with async_session() as db:
                ai_msg = Message(conversation_id=int(conversation_id), role="assistant", content=full_response)
                db.add(ai_msg)
                await db.commit()
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """列出用户的对话历史"""
    from ..models import Conversation
    from ..database import async_session
    from sqlalchemy import select
    user_id = int(current_user.get("id", 1))
    async with async_session() as db:
        result = await db.execute(
            select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.id.desc()).limit(50)
        )
        convs = result.scalars().all()
        return [
            {"id": c.id, "title": c.title, "model": c.model, "created_at": c.created_at.isoformat() if c.created_at else None}
            for c in convs
        ]

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int, current_user: dict = Depends(get_current_user)):
    """获取对话消息"""
    from ..models import Message
    from ..database import async_session
    from sqlalchemy import select
    async with async_session() as db:
        result = await db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
        )
        msgs = result.scalars().all()
        return [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in msgs
        ]


@router.delete("/conversations/{conversation_id}")
async def del_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """删除对话"""
    user_id = str(current_user.get("id", "default"))
    await delete_conversation(conversation_id)
    return {"status": "ok"}
