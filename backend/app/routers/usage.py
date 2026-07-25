"""用量统计路由 — 从数据库实时查询"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models import User, Conversation, Message
from ..auth import get_admin_user

router = APIRouter(prefix="/api/usage", tags=["用量统计"],
    dependencies=[Depends(get_admin_user)])  # v3.1.2 路由级鉴权


@router.get("/stats")
async def get_usage_stats(db: AsyncSession = Depends(get_db)):
    """获取系统用量统计（实时数据库查询）"""
    
    # 活跃用户数
    user_count_r = await db.execute(select(func.count(User.id)))
    user_count = user_count_r.scalar() or 0
    
    # 总对话数
    conv_r = await db.execute(select(func.count(Conversation.id)))
    conv_count = conv_r.scalar() or 0
    
    # 总消息数
    msg_r = await db.execute(select(func.count(Message.id)))
    msg_count = msg_r.scalar() or 0
    
    # 本月对话（created_at 在本月）
    from datetime import datetime
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_r = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.created_at >= month_start)
    )
    this_month = this_month_r.scalar() or 0
    
    # 本月消息
    this_month_msg_r = await db.execute(
        select(func.count(Message.id)).where(Message.created_at >= month_start)
    )
    this_month_msg = this_month_msg_r.scalar() or 0
    
    # 日均对话 = 本月对话 / 今天天数
    day_of_month = now.day
    avg_daily = round(this_month / day_of_month, 1) if day_of_month > 0 else 0
    
    # Token 估算（每条消息大约 500 tokens）
    est_tokens = this_month_msg * 500
    
    def fmt_tokens(n):
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000: return f"{n/1_000:.1f}K"
        return str(n)
    
    return {
        "stats": [
            {"label": "本月对话", "value": str(this_month), "key": "month_conv"},
            {"label": "Token用量", "value": fmt_tokens(est_tokens), "key": "tokens"},
            {"label": "活跃用户", "value": str(user_count), "key": "users"},
            {"label": "日均对话", "value": str(avg_daily), "key": "daily"},
        ],
        "details": {
            "total_users": user_count,
            "total_conversations": conv_count,
            "total_messages": msg_count,
            "this_month_conversations": this_month,
            "this_month_messages": this_month_msg,
        }
    }


@router.get("/daily")
async def get_daily_usage(db: AsyncSession = Depends(get_db)):
    """获取最近7天每日用量"""
    from datetime import datetime, timedelta
    now = datetime.now()
    days = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count_r = await db.execute(
            select(func.count(Message.id)).where(
                Message.created_at >= day_start,
                Message.created_at < day_end
            )
        )
        count = count_r.scalar() or 0
        days.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "messages": count,
            "tokens": count * 500,
        })
    return {"daily": days}
