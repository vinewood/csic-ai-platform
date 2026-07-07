"""API 配置管理路由"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import ApiConfig
from ..schemas import ApiConfigUpdate, MessageResponse
from ..config import set_api_config

router = APIRouter(prefix="/api/config", tags=["API配置"])


@router.get("/{provider}")
async def get_config(provider: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiConfig).where(ApiConfig.provider == provider))
    cfg = result.scalar_one_or_none()
    return cfg.config_json if cfg else {}


@router.put("/{provider}", response_model=MessageResponse)
async def update_config(provider: str, req: ApiConfigUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiConfig).where(ApiConfig.provider == provider))
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = ApiConfig(provider=provider, config_json=req.config_json)
        db.add(cfg)
    else:
        cfg.config_json = req.config_json
    # 同步到内存缓存
    if "key" in req.config_json and req.config_json["key"]:
        set_api_config(provider, req.config_json["key"])
    await db.commit()
    return MessageResponse(message=f"{provider} 配置已保存")
