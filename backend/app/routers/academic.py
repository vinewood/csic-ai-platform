"""学术搜索代理路由（AMiner + 维普）"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from ..database import get_db
from ..models import ApiConfig
from ..schemas import MessageResponse

router = APIRouter(prefix="/api/academic", tags=["学术搜索"])


async def get_api_config(db: AsyncSession, provider: str) -> dict:
    result = await db.execute(select(ApiConfig).where(ApiConfig.provider == provider))
    cfg = result.scalar_one_or_none()
    if not cfg or not cfg.config_json.get("key"):
        raise HTTPException(status_code=400, detail=f"请先配置 {provider} API")
    return cfg.config_json


@router.post("/aminer/search")
async def aminer_search(query: str = "", db: AsyncSession = Depends(get_db)):
    cfg = await get_api_config(db, "aminer")
    url = f"{cfg.get('baseUrl', 'https://api.aminer.cn')}/api/search/scholar"
    headers = {"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=headers, json={"query": query or "machine learning", "size": 10})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="AMiner 查询失败")
        return resp.json()


@router.post("/vip/search")
async def vip_search(query: str = "", db: AsyncSession = Depends(get_db)):
    cfg = await get_api_config(db, "vip")
    url = f"{cfg.get('endpoint', 'https://openapi.cqvip.com')}/api/v3/search"
    headers = {"Authorization": f"Bearer {cfg['key']}"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers, params={"q": query, "count": 10})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="维普查询失败")
        return resp.json()
