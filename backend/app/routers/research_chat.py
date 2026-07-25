"""科研工作台独立对话路由"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..auth import get_current_user

router = APIRouter(prefix="/api/research-chat", tags=["科研对话"])

class ChatReq(BaseModel):
    query: str
    model: str = "deepseek"
    skill_id: str = ""
    conversation_id: str = ""

@router.post("/send")
async def send_message(req: ChatReq, current_user: dict = Depends(get_current_user)):
    """科研工作台 SSE 流式对话"""
    from ..database import async_session
    from ..models import ResearchConversation, ResearchMessage
    from sqlalchemy import select
    
    user_id = int(current_user.get("id", 1))
    query = req.query
    model = req.model or "deepseek"
    conv_id = req.conversation_id
    
    async def generate():
        import httpx
        from ..config import get_api_config
        from ..services.dify_service import MODEL_ENDPOINTS
        ep = MODEL_ENDPOINTS.get(model, MODEL_ENDPOINTS["deepseek"])
        if ep.get("route") == "deepseek":
            key = get_api_config("deepseek")
            label = "DeepSeek"
        else:
            key = get_api_config("bailian") or get_api_config("dashscope") or get_api_config("qwen")
            label = "百炼/DashScope"
        if not key:
            yield f"data: {json.dumps({'content':f'[错误] 未配置 {label} API Key，请到 系统管理 → API 配置 设置'})}\n\n"
            yield "data: [DONE]\n\n"; return
        
        full = ""
        new_cid = conv_id
        
        # 创建对话
        async with async_session() as db:
            if not conv_id or conv_id == "new":
                conv = ResearchConversation(user_id=user_id, title=query[:30], model=model)
                db.add(conv); await db.flush()
                new_cid = str(conv.id)
                yield f"data: {json.dumps({'conversation_id':new_cid})}\n\n"
            # 保存用户消息
            um = ResearchMessage(conversation_id=int(new_cid), role="user", content=query)
            db.add(um); await db.commit()
        
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                async with c.stream("POST", ep["url"],
                    headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                    json={"model":ep["model"],"messages":[{"role":"user","content":query}],"temperature":0.7,"stream":True}
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            d = line[6:]
                            if d == "[DONE]": break
                            try:
                                ch = json.loads(d)["choices"][0]["delta"].get("content","")
                                if ch: full += ch; yield f"data: {json.dumps({'content':ch})}\n\n"
                            except: pass
        except Exception as e:
            yield f"data: {json.dumps({'content':f'[错误] {e}'})}\n\n"
        
        # 保存AI回复
        if full.strip():
            async with async_session() as db:
                am = ResearchMessage(conversation_id=int(new_cid), role="assistant", content=full)
                db.add(am); await db.commit()
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

@router.get("/conversations")
async def list_convs(current_user: dict = Depends(get_current_user)):
    from ..models import ResearchConversation
    from ..database import async_session
    from sqlalchemy import select
    uid = int(current_user.get("id", 1))
    async with async_session() as db:
        r = await db.execute(select(ResearchConversation).where(ResearchConversation.user_id == uid).order_by(ResearchConversation.id.desc()).limit(50))
        return [{"id":c.id,"title":c.title,"model":c.model,"created_at":c.created_at.isoformat() if c.created_at else None} for c in r.scalars()]

@router.get("/conversations/{cid}/messages")
async def get_msgs(cid: int, current_user: dict = Depends(get_current_user)):
    from ..models import ResearchMessage
    from ..database import async_session
    from sqlalchemy import select
    async with async_session() as db:
        r = await db.execute(select(ResearchMessage).where(ResearchMessage.conversation_id == cid).order_by(ResearchMessage.id))
        return [{"id":m.id,"role":m.role,"content":m.content} for m in r.scalars()]

@router.put("/conversations/{cid}/rename")
async def rename_conv(cid: int, data: dict, current_user: dict = Depends(get_current_user)):
    from ..models import ResearchConversation
    from ..database import async_session
    async with async_session() as db:
        c = await db.get(ResearchConversation, cid)
        if c: c.title = data.get("title",c.title); await db.commit(); return {"status":"ok"}
        raise HTTPException(404)

@router.delete("/conversations/{cid}")
async def del_conv(cid: int, current_user: dict = Depends(get_current_user)):
    from ..models import ResearchConversation, ResearchMessage
    from ..database import async_session
    from sqlalchemy import delete as d
    async with async_session() as db:
        await db.execute(d(ResearchMessage).where(ResearchMessage.conversation_id == cid))
        await db.execute(d(ResearchConversation).where(ResearchConversation.id == cid))
        await db.commit()
        return {"status":"ok"}
