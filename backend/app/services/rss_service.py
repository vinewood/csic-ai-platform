"""RSS 抓取服务 —— 集成 RSSHub"""

import feedparser, re
from typing import List, Dict
import httpx
from html import unescape

RSSHUB_URL = "http://localhost:1200"


def _clean_html(text: str) -> str:
    """去除 HTML 标签和多余空白，只保留纯文本"""
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()[:500]


async def fetch_from_rsshub(route: str) -> List[Dict]:
    if not route: return []
    try:
        url = f"{RSSHUB_URL}{route}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                return [{
                    "title": _clean_html(e.get("title", "")),
                    "link": e.get("link", ""),
                    "summary": _clean_html(e.get("summary", e.get("description", ""))),
                    "published": e.get("published", ""),
                } for e in feed.entries[:20]]
    except Exception: pass
    return []


async def fetch_rss(url: str) -> List[Dict]:
    """抓取单个 RSS 源 —— httpx 10 秒超时后交 feedparser 解析

    修复历史 bug：旧实现 feedparser.parse(url) 同步直连且无超时，
    失效源可挂起 60s+，17 个源串行叠加必然触发 nginx 504。
    """
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0 RSSReader"}) as client:
            resp = await client.get(url)
        if resp.status_code >= 400:
            return []
        feed = feedparser.parse(resp.content)
        return [{
            "title": _clean_html(e.get("title", "")),
            "link": e.get("link", ""),
            "summary": _clean_html(e.get("summary", e.get("description", ""))),
            "published": e.get("published", ""),
        } for e in feed.entries[:20]]
    except Exception:
        return []


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
