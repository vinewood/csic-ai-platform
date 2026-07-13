"""学术搜索统一服务 — AMiner + OpenAlex + Semantic Scholar"""

import httpx, json
from typing import Optional

AMINER_BASE = "https://datacenter.aminer.cn/gateway/open_platform/api"
OPENALEX_BASE = "https://api.openalex.org"
SEMANTIC_BASE = "https://api.semanticscholar.org/graph/v1"


def _get_aminer_token() -> Optional[str]:
    """从数据库读取 AMiner API Key"""
    import sqlite3
    try:
        conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
        row = conn.execute("SELECT config_json FROM api_configs WHERE provider='aminer'").fetchone()
        conn.close()
        if row:
            cfg = json.loads(row[0])
            return cfg.get("key", "") or ""
    except: pass
    return ""


def _get_aminer_auth() -> str:
    """获取 AMiner Authorization header 值"""
    token = _get_aminer_token()
    if token:
        return f"Bearer {token}"
    # 免费接口无需认证，直接返回空字符串
    return ""


def _get_openalex_email() -> str:
    """从数据库读取 OpenAlex email"""
    import sqlite3
    try:
        conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
        row = conn.execute("SELECT config_json FROM api_configs WHERE provider='openalex'").fetchone()
        conn.close()
        if row:
            cfg = json.loads(row[0])
            return cfg.get("key", "") or cfg.get("email", "")
    except: pass
    return ""


# ==================== AMiner API ====================

async def aminer_search_scholar(name: str = "", org: str = "", size: int = 10) -> dict:
    """搜索学者（免费接口）"""
    auth = _get_aminer_auth()
    headers = {"Authorization": auth} if auth else {}

    async with httpx.AsyncClient(timeout=20) as c:
        body = {"name": name, "size": size}
        if org: body["org"] = org
        if not name and not org: return {"results": [], "note": "请至少输入姓名或机构"}

        r = await c.post(f"{AMINER_BASE}/person/search", headers=headers, json=body)
        if r.status_code == 200:
            data = r.json()
            return {
                "results": [{
                    "id": p.get("id"), "name": p.get("name", ""),
                    "name_zh": p.get("name_zh", ""), "h_index": p.get("h_index", ""),
                    "n_citation": p.get("n_citation", 0),
                    "interests": p.get("interests", ""),
                    "org": p.get("org", ""),
                } for p in data.get("data", [])[:size]],
                "total": data.get("total", 0)
            }
    return {"results": [], "error": "AMiner API 请求失败"}


async def aminer_search_paper(title: str = "", keyword: str = "", author: str = "", page: int = 0, size: int = 10) -> dict:
    """搜索论文（免费接口）"""
    auth = _get_aminer_auth()
    headers = {"Authorization": auth} if auth else {}

    async with httpx.AsyncClient(timeout=20) as c:
        params = {"page": page, "size": size}
        if title: params["title"] = title
        if keyword: params["keyword"] = keyword
        if author: params["author"] = author

        r = await c.get(f"{AMINER_BASE}/paper/search/pro", headers=headers, params=params)
        if r.status_code == 200:
            data = r.json()
            return {
                "results": [{
                    "id": p.get("id"), "doi": p.get("doi", ""),
                    "title": p.get("title", ""), "title_zh": p.get("title_zh", ""),
                    "year": p.get("year", ""),
                } for p in data.get("data", [])[:size]],
                "total": data.get("total", 0)
            }
    return {"results": [], "error": "AMiner API 请求失败"}


async def aminer_paper_detail(paper_id: str) -> dict:
    """论文详情"""
    token = _get_aminer_token()
    if not token: return {"error": "请配置 AMiner API Key"}

    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(
            f"{AMINER_BASE}/paper/detail",
            headers={"Authorization": f"Bearer {token}"},
            params={"id": paper_id}
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("data", {})
    return {"error": "获取失败"}


async def aminer_qa_search(query: str, size: int = 10) -> dict:
    """AI学术问答"""
    token = _get_aminer_token()
    if not token: return {"error": "请配置 AMiner API Key"}

    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{AMINER_BASE}/paper/qa/search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query, "use_topic": True, "size": size,
                  "topic_high": [[query]]}
        )
        if r.status_code == 200:
            data = r.json()
            return {
                "results": [{
                    "id": p.get("id"), "doi": p.get("doi", ""),
                    "title": p.get("title", ""), "title_zh": p.get("title_zh", ""),
                } for p in data.get("data", [])[:size]],
                "total": data.get("total", 0)
            }
    return {"results": [], "error": "QA请求失败"}


# ==================== OpenAlex API ====================

async def openalex_search_works(query: str = "", filter_str: str = "", page: int = 1, per_page: int = 25) -> dict:
    """搜索 OpenAlex 论文"""
    email = _get_openalex_email()
    params = {"per_page": per_page, "page": page}
    if query: params["search"] = query
    if filter_str: params["filter"] = filter_str
    if email: params["mailto"] = email

    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{OPENALEX_BASE}/works", params=params)
        if r.status_code == 200:
            data = r.json()
            return {
                "results": [{
                    "id": w["id"].split("/")[-1],
                    "title": w.get("title", ""),
                    "doi": w.get("doi", ""),
                    "year": w.get("publication_year", ""),
                    "cited_by": w.get("cited_by_count", 0),
                    "is_oa": w.get("open_access", {}).get("is_oa", False),
                    "authors": [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:5]],
                    "concepts": [c.get("display_name", "") for c in w.get("concepts", [])[:3]],
                    "abstract": _invert_abstract(w.get("abstract_inverted_index")),
                } for w in data.get("results", [])],
                "total": data.get("meta", {}).get("count", 0),
                "page": page
            }
    return {"results": [], "error": "OpenAlex 请求失败"}


async def openalex_search_authors(query: str = "", page: int = 1) -> dict:
    """搜索 OpenAlex 学者"""
    email = _get_openalex_email()
    params = {"search": query, "per_page": 25, "page": page}
    if email: params["mailto"] = email

    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{OPENALEX_BASE}/authors", params=params)
        if r.status_code == 200:
            data = r.json()
            return {
                "results": [{
                    "id": a["id"].split("/")[-1],
                    "name": a.get("display_name", ""),
                    "h_index": a.get("summary_stats", {}).get("h_index", 0),
                    "cited_by": a.get("summary_stats", {}).get("cited_by_count", 0),
                    "works_count": a.get("works_count", 0),
                    "institution": a.get("last_known_institution", {}).get("display_name", "") if a.get("last_known_institution") else "",
                } for a in data.get("results", [])],
                "total": data.get("meta", {}).get("count", 0)
            }
    return {"results": []}


def _invert_abstract(inverted: dict) -> str:
    """还原 OpenAlex 倒排索引的摘要"""
    if not inverted: return ""
    try:
        max_pos = max(max(v) for v in inverted.values())
        words = [""] * (max_pos + 1)
        for word, positions in inverted.items():
            for p in positions:
                words[p] = word
        return " ".join(words)[:500]
    except: return ""
