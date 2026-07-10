"""模型管理路由 — CRUD API 配置（与 api_configs 表共用）"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import ApiConfig
from ..schemas import MessageResponse
from ..config import set_api_config

router = APIRouter(prefix="/api/models", tags=["模型管理"])


@router.get("")
async def list_models(db: AsyncSession = Depends(get_db)):
    """列出所有已配置的模型"""
    result = await db.execute(select(ApiConfig))
    cfgs = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.provider,
            "provider": c.provider,
            "key": c.config_json.get("key", "") if c.config_json else "",
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
    """更新模型配置"""
    result = await db.execute(select(ApiConfig).where(ApiConfig.id == model_id))
    cfg = result.scalar_one_or_none()
    if not cfg:
        # Try by provider name
        result = await db.execute(select(ApiConfig).where(ApiConfig.provider == str(model_id)))
        cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    cfg_json = cfg.config_json or {}
    if "key" in req: cfg_json["key"] = req["key"]
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
