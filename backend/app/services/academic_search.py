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


# ==================== Crossref API (免费，无需Key，7500万+ DOI) ====================

CROSSREF_BASE = "https://api.crossref.org"


async def crossref_search(query: str, rows: int = 10, offset: int = 0) -> dict:
    """搜索 Crossref 论文元数据"""
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(
            f"{CROSSREF_BASE}/works",
            params={"query": query, "rows": rows, "offset": offset, "sort": "relevance"}
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("message", {}).get("items", [])
            return {
                "results": [{
                    "doi": i.get("DOI", ""),
                    "title": (i.get("title") or [""])[0],
                    "author": ", ".join(
                        f"{a.get('given','')} {a.get('family','')}".strip()
                        for a in (i.get("author") or [])[:3]
                    ),
                    "year": (i.get("published-print") or i.get("created") or {}).get("date-parts", [[0]])[0][0],
                    "publisher": i.get("publisher", ""),
                    "type": i.get("type", ""),
                    "cited_by": i.get("is-referenced-by-count", 0),
                    "url": i.get("URL", f"https://doi.org/{i.get('DOI','')}"),
                } for i in items],
                "total": data.get("message", {}).get("total-results", 0),
            }
    return {"results": [], "error": "Crossref 请求失败"}


async def crossref_lookup_doi(doi: str) -> dict:
    """通过 DOI 获取论文完整信息"""
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(f"{CROSSREF_BASE}/works/{doi}")
        if r.status_code == 200:
            i = r.json().get("message", {})
            return {
                "doi": i.get("DOI", ""),
                "title": (i.get("title") or [""])[0],
                "abstract": i.get("abstract", ""),
                "author": ", ".join(
                    f"{a.get('given','')} {a.get('family','')}".strip()
                    for a in (i.get("author") or [])[:10]
                ),
                "year": (i.get("published-print") or i.get("created") or {}).get("date-parts", [[0]])[0][0],
                "publisher": i.get("publisher", ""),
                "journal": ", ".join(i.get("container-title") or []),
                "cited_by": i.get("is-referenced-by-count", 0),
                "references_count": i.get("references-count", 0),
                "type": i.get("type", ""),
                "url": i.get("URL", f"https://doi.org/{i.get('DOI','')}"),
            }
    return {"error": "DOI 查询失败"}


# ==================== Moodle LMS API ====================

def _get_moodle_config() -> tuple:
    """获取 Moodle 配置 (url, token)"""
    import sqlite3, json
    try:
        conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
        row = conn.execute("SELECT config_json FROM api_configs WHERE provider='moodle'").fetchone()
        conn.close()
        if row:
            cfg = json.loads(row[0])
            return cfg.get("url", ""), cfg.get("token", "")
    except: pass
    return "", ""


async def moodle_get_courses() -> dict:
    """获取 Moodle 课程列表"""
    url, token = _get_moodle_config()
    if not url or not token:
        return {"error": "请在系统设置中配置 Moodle 地址和 API Token"}
    
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(
            f"{url}/webservice/rest/server.php",
            params={
                "wstoken": token, "wsfunction": "core_course_get_courses",
                "moodlewsrestformat": "json"
            }
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return {"courses": [{
                    "id": c.get("id"), "fullname": c.get("fullname", ""),
                    "shortname": c.get("shortname", ""),
                    "summary": (c.get("summary") or "")[:200],
                    "enrolled_count": c.get("enrolledusercount", 0),
                    "category": c.get("categoryname", ""),
                } for c in data], "total": len(data)}
    return {"error": str(r.status_code) if r.status_code else "连接失败"}


async def moodle_get_users() -> dict:
    """获取 Moodle 用户列表"""
    url, token = _get_moodle_config()
    if not url or not token: return {"error": "请配置 Moodle"}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(
            f"{url}/webservice/rest/server.php",
            params={
                "wstoken": token,
                "wsfunction": "core_enrol_get_enrolled_users",
                "moodlewsrestformat": "json"
            }
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                return {"users": [{"id": u.get("id"), "fullname": u.get("fullname", ""),
                    "email": u.get("email", "")} for u in data[:50]], "total": len(data)}
    return {"error": "获取失败"}


# ==================== Khan Academy API ====================

KHAN_BASE = "https://www.khanacademy.org/api/v1"


async def khan_search_topics(query: str = "") -> dict:
    """搜索 Khan Academy 课程主题"""
    async with httpx.AsyncClient(timeout=20) as c:
        if query:
            r = await c.get(f"{KHAN_BASE}/topictree")
            data = r.json()
            # Filter matching topics
            matches = []
            def search_node(node):
                if query.lower() in node.get("translated_title", "").lower():
                    matches.append(node)
                for child in node.get("children", []):
                    search_node(child)
            search_node(data)
            return {"topics": [{
                "id": m.get("id"), "title": m.get("translated_title", ""),
                "kind": m.get("kind", ""),
                "children_count": len(m.get("children", []))
            } for m in matches[:20]], "total": len(matches)}
        else:
            r = await c.get(f"{KHAN_BASE}/topictree")
            data = r.json()
            def top_level(node):
                return [{
                    "id": n.get("id"), "title": n.get("translated_title", ""),
                    "kind": n.get("kind", ""),
                    "children_count": len(n.get("children", []))
                } for n in node.get("children", [])[:12]]
            return {"topics": top_level(data), "total": len(top_level(data))}
