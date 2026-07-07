"""RSS 新闻源管理 + 定时抓取"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import RssSource, NewsArticle
from ..schemas import RssSourceCreate, RssSourceOut, MessageResponse
from ..auth import get_current_user
from ..services.rss_service import fetch_rss, RSSHUB_URL, fetch_from_rsshub

router = APIRouter(prefix="/api/rss", tags=["RSS管理"])


@router.get("/sources", response_model=list[RssSourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RssSource).order_by(RssSource.id))
    return result.scalars().all()


@router.post("/sources", response_model=MessageResponse)
async def create_source(req: RssSourceCreate, db: AsyncSession = Depends(get_db)):
    source = RssSource(name=req.name, url=req.url, category=req.category, ai_enabled=req.ai_enabled)
    db.add(source)
    await db.commit()
    return MessageResponse(message="新闻源已添加")


@router.put("/sources/{source_id}", response_model=MessageResponse)
async def update_source(source_id: int, req: RssSourceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RssSource).where(RssSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="源不存在")
    source.name = req.name
    source.url = req.url
    source.category = req.category
    source.ai_enabled = req.ai_enabled
    await db.commit()
    return MessageResponse(message="已更新")


@router.delete("/sources/{source_id}", response_model=MessageResponse)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RssSource).where(RssSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="源不存在")
    await db.delete(source)
    await db.commit()
    return MessageResponse(message="已删除")


@router.post("/fetch")
async def fetch_all_rss(db: AsyncSession = Depends(get_db)):
    """手动触发 RSS 抓取"""
    result = await db.execute(select(RssSource).where(RssSource.active == True))
    sources = result.scalars().all()
    count = 0
    for src in sources:
        articles = await fetch_rss(src.url)
        for art in articles[:10]:
            existing = await db.execute(
                select(NewsArticle).where(NewsArticle.url == art.get("link", ""))
            )
            if existing.scalar_one_or_none():
                continue
            article = NewsArticle(
                source_id=src.id,
                title=art.get("title", ""),
                url=art.get("link", ""),
                summary=art.get("summary", ""),
                category=src.category,
            )
            db.add(article)
            count += 1
    await db.commit()
    return MessageResponse(message=f"抓取完成，新增 {count} 条")


@router.get("/articles")
async def list_articles(
    category: str = "",
    date: str = "",
    db: AsyncSession = Depends(get_db),
):
    query = select(NewsArticle).order_by(NewsArticle.created_at.desc())
    if category:
        query = query.where(NewsArticle.category == category)
    result = await db.execute(query.limit(100))
    articles = result.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "summary": a.ai_summary or a.summary,
            "category": a.category,
            "time": a.published.strftime("%H:%M") if a.published else "",
        }
        for a in articles
    ]
