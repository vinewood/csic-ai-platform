"""邮件发送服务"""

import aiosmtplib
from email.message import EmailMessage

from ..models import EmailConfig


async def send_email(cfg: EmailConfig, subject: str, html: str) -> bool:
    """发送 HTML 邮件"""
    if not cfg.smtp_host or not cfg.to_addr:
        return False
    msg = EmailMessage()
    msg["From"] = cfg.from_addr or cfg.smtp_user
    msg["To"] = cfg.to_addr
    msg["Subject"] = subject
    msg.set_content(html, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=cfg.smtp_host,
            port=cfg.smtp_port or 465,
            username=cfg.smtp_user,
            password=cfg.smtp_pass,
            use_tls=(cfg.smtp_port == 465),
        )
        return True
    except Exception:
        return False


async def send_test_email(cfg: EmailConfig) -> bool:
    """发送测试邮件"""
    html = "<h2>中船党校 AI 平台</h2><p>这是一封测试邮件，配置正确。</p>"
    return await send_email(cfg, "【中船党校】邮件配置测试", html)


async def send_daily_digest(cfg: EmailConfig, articles_html: str) -> bool:
    """发送每日资讯日报"""
    html = f"""
    <h2>中船党校 · 每日资讯</h2>
    <p>AI 智能整理的最新资讯，点击标题阅读原文。</p>
    {articles_html}
    <hr><p style="color:#94a3b8;font-size:12px;">由中船党校 AI 平台自动生成</p>
    """
    return await send_email(cfg, "【中船党校】每日资讯", html)
