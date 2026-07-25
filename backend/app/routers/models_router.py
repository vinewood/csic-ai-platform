"""模型管理路由 — CRUD API 配置（与 api_configs 表共用）

安全基线（v3.1.2）：
- 全路由 admin 鉴权（路由级 dependencies，此前完全裸奔泄露密钥）
- GET 永不回传真实 key，只回 has_key 状态（铁律：key 只允许存在本地/服务器）
- PUT 收到空 key 或掩码 key 时保留原值，避免前端展示态覆盖真实密钥
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import ApiConfig
from ..schemas import MessageResponse
from ..config import set_api_config
from ..auth import get_admin_user

router = APIRouter(
    prefix="/api/models",
    tags=["模型管理"],
    dependencies=[Depends(get_admin_user)],   # 路由级鉴权：仅管理员
)


def _is_masked(key: str) -> bool:
    """判断是否为掩码/空 key（掩码值或空值不应覆盖真实密钥）"""
    return not key or "***" in key


@router.get("")
async def list_models(db: AsyncSession = Depends(get_db)):
    """列出所有已配置的模型（不回传真实 key）"""
    result = await db.execute(select(ApiConfig))
    cfgs = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.provider,
            "provider": c.provider,
            "key": "",                                   # 铁律：真实 key 不出服务器
            "has_key": bool((c.config_json or {}).get("key")),
            "status": "active" if (c.config_json or {}).get("key", "") else "inactive"
        }
        for c in cfgs
    ]


@router.post("", response_model=MessageResponse)
async def add_model(req: dict, db: AsyncSession = Depends(get_db)):
    """新增模型配置"""
    provider = req.get("name") or req.get("provider", "")
    if not provider:
        raise HTTPException(status_code=400, detail="请提供模型名称")

    result = await db.execute(select(ApiConfig).where(ApiConfig.provider == provider))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"模型 {provider} 已存在")

    cfg_json = {
        "key": req.get("key", ""),
        "models": [req.get("name", provider)],
        "baseUrl": req.get("base_url", "")
    }
    cfg = ApiConfig(provider=provider, config_json=cfg_json)
    db.add(cfg)

    if cfg_json["key"]:
        set_api_config(provider, cfg_json["key"])

    await db.commit()
    return MessageResponse(message="模型已添加")


@router.put("/{model_id}", response_model=MessageResponse)
async def update_model(model_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    """更新模型配置（空/掩码 key 保留原值）"""
    result = await db.execute(select(ApiConfig).where(ApiConfig.id == model_id))
    cfg = result.scalar_one_or_none()
    if not cfg:
        # Try by provider name
        result = await db.execute(select(ApiConfig).where(ApiConfig.provider == str(model_id)))
        cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="模型不存在")

    cfg_json = cfg.config_json or {}
    if "key" in req and not _is_masked(req["key"]):
        cfg_json["key"] = req["key"]          # 仅真实新 key 才覆盖
    if "name" in req: cfg.provider = req["name"]
    if "base_url" in req: cfg_json["baseUrl"] = req["base_url"]
    cfg.config_json = cfg_json

    if cfg_json.get("key"):
        set_api_config(cfg.provider, cfg_json["key"])

    await db.commit()
    return MessageResponse(message="模型已更新")


@router.delete("/{model_id}", response_model=MessageResponse)
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """删除模型配置"""
    result = await db.execute(select(ApiConfig).where(ApiConfig.id == model_id))
    cfg = result.scalar_one_or_none()
    if not cfg:
        result = await db.execute(select(ApiConfig).where(ApiConfig.provider == str(model_id)))
        cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="模型不存在")

    await db.delete(cfg)
    await db.commit()
    return MessageResponse(message="模型已删除")
