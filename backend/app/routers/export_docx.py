"""文档导出路由 — docx 生成"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from ..auth import get_current_user
import io

router = APIRouter(prefix="/api/export", tags=["导出"])

class ExportRequest(BaseModel):
    conversation_id: int
    format: Optional[str] = "docx"

@router.post("/docx")
async def export_docx(req: ExportRequest, current_user: dict = Depends(get_current_user)):
    """导出对话为 docx 文件"""
    from ..database import async_session
    from ..models import Message, Conversation
    from sqlalchemy import select
    
    async with async_session() as db:
        conversation = await db.get(Conversation, req.conversation_id)
        if not conversation:
            return {"error": "对话不存在"}
        
        result = await db.execute(
            select(Message).where(Message.conversation_id == req.conversation_id).order_by(Message.id)
        )
        messages = result.scalars().all()
    
    # 生成 docx
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = Document()
    
    # 标题
    title = doc.add_heading(conversation.title or "对话记录", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f"模型: {conversation.model}  |  时间: {conversation.created_at}")
    doc.add_paragraph("")
    
    for msg in messages:
        if msg.role == "user":
            p = doc.add_paragraph()
            run = p.add_run("👤 用户：")
            run.bold = True
            run.font.color.rgb = RGBColor(0x16, 0x77, 0xFF)
            doc.add_paragraph(msg.content or "")
        else:
            p = doc.add_paragraph()
            run = p.add_run("🤖 AI：")
            run.bold = True
            run.font.color.rgb = RGBColor(0x10, 0xB9, 0x81)
            doc.add_paragraph(msg.content or "")
        doc.add_paragraph("")
    
    # 输出到内存流
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    filename = f"{conversation.title or '对话'}.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
