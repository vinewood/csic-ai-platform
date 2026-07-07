"""RSS 抓取服务 —— 集成 RSSHub"""

import feedparser
from typing import List, Dict
import httpx

RSSHUB_URL = "http://localhost:1200"


async def fetch_from_rsshub(route: str) -> List[Dict]:
    """通过本地 RSSHub 实例抓取"""
    if not route:
        return []
    try:
        url = f"{RSSHUB_URL}{route}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                # RSSHub 返回 RSS XML
                feed = feedparser.parse(resp.text)
                articles = []
                for entry in feed.entries[:20]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "published": entry.get("published", ""),
                    })
                return articles
    except Exception:
        pass
    return []


async def fetch_rss(url: str) -> List[Dict]:
    """抓取 RSS 源并返回文章列表"""
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:20]:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", entry.get("description", "")),
                "published": entry.get("published", ""),
            })
        return articles
    except Exception:
        return []


# 知名党建媒体 RSSHub 路由映射
PARTY_MEDIA_ROUTES = {
    "新华网": "/xinhua/news",
    "人民网": "/people/opinion",
    "求是网": "/qstheory",
    "中国政府网": "/gov/latest",
    "国资委": "/sasac/latest",
    "36氪": "/36kr/news",
    "虎嗅": "/huxiu/articles",
    "机器之心": "/jiqizhixin",
    "量子位": "/qbitai",
}
