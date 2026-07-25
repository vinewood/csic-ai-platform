"""邮箱配置路由 + 测试发送"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import EmailConfig
from ..schemas import EmailConfigOut, EmailConfigUpdate, MessageResponse
from ..services.email_service import send_test_email
from ..auth import get_admin_user

router = APIRouter(prefix="/api/email", tags=["邮箱配置"],
    dependencies=[Depends(get_admin_user)])  # v3.1.2 路由级鉴权


@router.get("/config", response_model=EmailConfigOut)
async def get_email_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = EmailConfig()
        db.add(cfg)
        await db.commit()
    return EmailConfigOut(
        smtp_host=cfg.smtp_host or "",
        smtp_port=cfg.smtp_port or 465,
        smtp_user=cfg.smtp_user or "",
        from_addr=cfg.from_addr or "",
        to_addr=cfg.to_addr or "",
        send_time=cfg.send_time or "08:00",
        auto_send=cfg.auto_send or False,
    )


@router.put("/config", response_model=MessageResponse)
async def update_email_config(req: EmailConfigUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = EmailConfig()
        db.add(cfg)
    if req.smtp_host is not None: cfg.smtp_host = req.smtp_host
    if req.smtp_port is not None: cfg.smtp_port = req.smtp_port
    if req.smtp_user is not None: cfg.smtp_user = req.smtp_user
    if req.smtp_pass is not None: cfg.smtp_pass = req.smtp_pass
    if req.from_addr is not None: cfg.from_addr = req.from_addr
    if req.to_addr is not None: cfg.to_addr = req.to_addr
    if req.send_time is not None: cfg.send_time = req.send_time
    if req.auto_send is not None: cfg.auto_send = req.auto_send
    await db.commit()
    return MessageResponse(message="邮箱配置已保存")


@router.post("/test")
async def test_email(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if not cfg or not cfg.smtp_host:
        raise HTTPException(status_code=400, detail="请先配置邮箱")
    ok = await send_test_email(cfg)
    if ok:
        return MessageResponse(message="测试邮件发送成功")
    raise HTTPException(status_code=500, detail="发送失败，请检查配置")
