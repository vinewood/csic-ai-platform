"""API 配置管理路由

安全基线（v3.1.2）：
- 全路由 admin 鉴权（此前无鉴权，任意人可读取全部 API Key）
- GET 不回传真实 key，只回 has_key 状态
- PUT 收到空/掩码 key 时保留原值
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import ApiConfig
from ..schemas import ApiConfigUpdate, MessageResponse
from ..config import set_api_config
from ..auth import get_admin_user

router = APIRouter(
    prefix="/api/config",
    tags=["API配置"],
    dependencies=[Depends(get_admin_user)],   # 路由级鉴权：仅管理员
)


@router.get("/{provider}")
async def get_config(provider: str, db: AsyncSession = Depends(get_db)):
    """读取配置（真实 key 不回传，仅返回 has_key 状态）"""
    result = await db.execute(select(ApiConfig).where(ApiConfig.provider == provider))
    cfg = result.scalar_one_or_none()
    if not cfg or not cfg.config_json:
        return {}
    safe = {k: v for k, v in cfg.config_json.items() if k != "key"}
    safe["key"] = ""
    safe["has_key"] = bool(cfg.config_json.get("key"))
    return safe


@router.put("/{provider}", response_model=MessageResponse)
async def update_config(provider: str, req: ApiConfigUpdate, db: AsyncSession = Depends(get_db)):
    """保存配置（空/掩码 key 保留原值，防止展示态覆盖真实密钥）"""
    result = await db.execute(select(ApiConfig).where(ApiConfig.provider == provider))
    cfg = result.scalar_one_or_none()
    incoming = dict(req.config_json or {})
    new_key = incoming.get("key", "")

    if cfg and (not new_key or "***" in str(new_key)):
        # 保留已有真实 key，仅更新其余字段
        incoming["key"] = (cfg.config_json or {}).get("key", "")

    if not cfg:
        cfg = ApiConfig(provider=provider, config_json=incoming)
        db.add(cfg)
    else:
        cfg.config_json = incoming
    # 同步到内存缓存
    if incoming.get("key"):
        set_api_config(provider, incoming["key"])
    await db.commit()
    return MessageResponse(message=f"{provider} 配置已保存")
