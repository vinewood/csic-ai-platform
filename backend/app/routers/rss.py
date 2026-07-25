"""RSS 新闻源管理 + 定时抓取"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import RssSource, NewsArticle
from ..schemas import RssSourceCreate, RssSourceOut, MessageResponse
from ..auth import get_current_user
from ..services.rss_service import fetch_rss, RSSHUB_URL, fetch_from_rsshub

router = APIRouter(prefix="/api/rss", tags=["RSS管理"],
    dependencies=[Depends(get_current_user)])  # v3.1.2 路由级鉴权


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


async def _fetch_all_sources(sources) -> list:
    """并发抓取全部启用的 RSS 源（每源独立超时与容错），返回 [(source, articles), ...]

    修复历史 bug：旧实现 17 个源串行抓取，任一失效源挂起即叠加超时（nginx 504）。
    """
    import asyncio

    async def _one(src):
        try:
            return src, await fetch_rss(src.url)
        except Exception:
            return src, []

    results = await asyncio.gather(*[_one(s) for s in sources])
    return results


@router.post("/fetch")
async def fetch_all_rss(db: AsyncSession = Depends(get_db)):
    """手动触发 RSS 抓取"""
    result = await db.execute(select(RssSource).where(RssSource.active == True))
    sources = result.scalars().all()
    count = 0
    for src, articles in await _fetch_all_sources(sources):
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
    from sqlalchemy import func, cast, Date
    query = select(NewsArticle).order_by(NewsArticle.created_at.desc())
    if category:
        query = query.where(NewsArticle.category == category)
    if date:
        query = query.where(func.date(NewsArticle.created_at) == date)
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
            "date": str(a.created_at)[:10] if a.created_at else "",
        }
        for a in articles
    ]


@router.post("/generate-daily")
async def generate_daily_digest(db: AsyncSession = Depends(get_db)):
    """生成今日资讯 — 先抓取RSS → DeepSeek优化 → 返回结果"""
    import httpx, json
    from datetime import date
    from ..config import get_api_config

    today = date.today().isoformat()

    # 1. 先触发 RSS 抓取（并发，单源 10s 超时兜底）
    result = await db.execute(select(RssSource).where(RssSource.active == True))
    sources = result.scalars().all()
    fetch_count = 0
    for src, articles in await _fetch_all_sources(sources):
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
            fetch_count += 1
    await db.commit()

    # 2. 获取今天的文章
    result = await db.execute(
        select(NewsArticle).order_by(NewsArticle.created_at.desc()).limit(30)
    )
    articles = result.scalars().all()

    if not articles:
        return {"message": "今日暂无新资讯", "count": 0, "digest": ""}

    # 3. 构建文章列表
    article_text = "\n".join(
        f"- [{a.category or '综合'}] {a.title}（{a.summary[:100] if a.summary else '无摘要'}）"
        for a in articles[:20]
    )

    # 4. DeepSeek 优化生成日报
    prompt = f"""你是专业资讯编辑。请根据以下今日文章列表，生成一份结构化的每日资讯简报：

今日文章（共{len(articles)}篇）：
{article_text}

请按以下格式输出：
# 📰 今日资讯简报（{today}）

## 🔥 热点关注
（3-5条最重要的资讯，每条包含标题和50字摘要）

## 📂 分类速览
按类别整理，每类列出2-3条要点

## 📊 数据概览
今日共收录{len(articles)}篇，覆盖{len(set(a.category for a in articles))}个领域

## 💡 编辑推荐
重点推荐2-3篇必读文章并说明理由

请用专业新闻语言，简洁有力。"""

    key = get_api_config("deepseek")
    if not key:
        return {"message": "请先配置DeepSeek API Key", "count": len(articles)}

    try:
        async with httpx.AsyncClient(timeout=60) as c:
            resp = await c.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "deepseek-v4-pro",  # 该账号仅支持 v4 系列（旧值 deepseek-chat 必然 400）
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7, "max_tokens": 2000,
                }
            )
            if resp.status_code == 200:
                digest = resp.json()["choices"][0]["message"]["content"]

                # 保存日报到数据库
                for a in articles[:20]:
                    if not a.ai_summary:
                        a.ai_summary = digest.split(f"[{a.category or '综合'}]")[-1][:200] if f"[{a.category or '综合'}]" in digest else a.summary

                await db.commit()
                return {
                    "message": f"今日资讯已生成，共 {len(articles)} 篇，新增抓取 {fetch_count} 篇",
                    "count": len(articles),
                    "fetch_count": fetch_count,
                    "digest": digest,
                    "date": today,
                }
    except Exception as e:
        pass

    return {"message": "AI生成失败，请稍后重试", "count": len(articles)}
