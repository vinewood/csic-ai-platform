"""MCP 接口 — Model Context Protocol（Streamable HTTP 传输）

挂载于主应用 /mcp，供 hibuddy 等外部 Agent 以标准 MCP 协议调用本平台能力。
认证：Authorization: Bearer <token>，token 为平台 JWT 或 api_configs 中的 mcp 静态令牌。
"""

import json

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.types import ASGIApp, Receive, Scope, Send

mcp = FastMCP(
    "csic-ai-platform",
    instructions="中船党校 AI 智能业务平台：对话、知识库检索、学术检索、每日资讯、技能列表",
    streamable_http_path="/",  # 挂载点即根（app.mount("/mcp") 之后 path 为 /）
    # SDK 默认开启 DNS 重绑定防护会拒绝域名 Host；显式放行本站域名与本地回环
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["csic.thinkalike.com.cn", "csic.thinkalike.com.cn:*",
                       "127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*"],
        allowed_origins=["https://csic.thinkalike.com.cn", "http://127.0.0.1:*", "http://localhost:*"],
    ),
)


@mcp.tool()
async def csic_chat(query: str, model: str = "deepseek") -> str:
    """与中船党校 AI 助手对话（直连大模型）。

    model 可选：deepseek（默认）/ qwen-plus / qwen-max / glm-4 / kimi / minimax。
    返回模型的完整文本回复。
    """
    from app.services.dify_service import chat_stream

    full = ""
    async for chunk in chat_stream(query=query, model=model, user_id="mcp-client"):
        full += chunk
    return full.strip() or "[模型无回复]"


@mcp.tool()
async def csic_knowledge_search(query: str, top_k: int = 5) -> str:
    """检索党校知识库（《党校工作条例》等已灌语料），返回相关文档片段与来源。

    top_k 默认 5，最大 10。
    """
    from app.services.kb_storage import retrieve_from_kb

    top_k = max(1, min(int(top_k), 10))
    results = retrieve_from_kb(query, "", top_k)
    if not results:
        return "未检索到相关内容"
    lines = []
    for i, r in enumerate(results, 1):
        name = r.get("name", "?")
        snippet = (r.get("snippet") or "").strip()
        lines.append(f"[{i}] 来源《{name}》\n{snippet}")
    return "\n\n".join(lines)


@mcp.tool()
async def csic_academic_search(query: str) -> str:
    """学术文献检索（OpenAlex，免费公开库），返回前 5 篇论文的标题/年份/引用数/链接。"""
    from app.services.academic_search import openalex_search_works

    data = await openalex_search_works(query=query)
    works = (data or {}).get("results") or []
    if not works:
        return "未检索到相关论文"
    lines = []
    for i, w in enumerate(works[:5], 1):
        title = w.get("title") or w.get("display_name") or "?"
        year = w.get("year") or w.get("publication_year") or ""
        cited = w.get("cited_by_count", w.get("cited_by", ""))
        doi = w.get("doi") or ""
        wid = w.get("id") or ""
        url = doi if doi.startswith("http") else (f"https://openalex.org/works/{wid}" if wid else "")
        lines.append(f"[{i}] {title}（{year}，被引 {cited}）\n{url}")
    return "\n\n".join(lines)


@mcp.tool()
async def csic_daily_news(category: str = "", date: str = "") -> str:
    """获取每日资讯（RSS 聚合 + AI 摘要）。

    category 可选分类名（如 时政/经济/科技），date 格式 YYYY-MM-DD，默认取最新 15 条。
    """
    from sqlalchemy import select, func

    from app.database import async_session
    from app.models import NewsArticle

    async with async_session() as s:
        q = select(NewsArticle).order_by(NewsArticle.created_at.desc())
        if category:
            q = q.where(NewsArticle.category == category)
        if date:
            q = q.where(func.date(NewsArticle.created_at) == date)
        rows = (await s.execute(q.limit(15))).scalars().all()
    if not rows:
        return "暂无资讯"
    lines = []
    for a in rows:
        summary = (a.ai_summary or a.summary or "").strip()
        day = str(a.created_at)[:10] if a.created_at else ""
        lines.append(f"【{a.category or '资讯'}】{a.title}（{day}）\n{summary}\n{a.url or ''}")
    return "\n\n".join(lines)


@mcp.tool()
async def csic_list_skills() -> str:
    """列出平台预置与用户自定义的 AI 技能（名称/分类/描述）。"""
    from sqlalchemy import select

    from app.database import async_session
    from app.models import Skill

    async with async_session() as s:
        rows = (await s.execute(select(Skill).order_by(Skill.category, Skill.id))).scalars().all()
    if not rows:
        return "暂无技能"
    return "\n".join(
        f"- [{sk.category or '未分类'}] {sk.name}：{sk.description or '无描述'}" for sk in rows
    )


# ------------------------------------------------------------------
# 认证中间件：Bearer 平台 JWT 或 api_configs(mcp) 静态令牌
# ------------------------------------------------------------------

class McpAuthMiddleware:
    """包在 MCP ASGI 应用外层：校验 Authorization 头，不通过返回 401。"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        auth = headers.get("authorization", "")
        token = auth[7:] if auth.lower().startswith("bearer ") else ""

        if not token or not _token_ok(token):
            body = json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32001, "message": "Unauthorized: 需要 Bearer 平台 JWT 或 MCP 令牌"},
            }).encode()
            await send({
                "type": "http.response.start", "status": 401,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({"type": "http.response.body", "body": body})
            return

        await self.app(scope, receive, send)


def _token_ok(token: str) -> bool:
    """JWT 有效，或等于 api_configs 里的 mcp 静态令牌"""
    # 1) 平台 JWT
    try:
        from jose import jwt as jose_jwt

        from app.auth import SECRET_KEY, ALGORITHM
        jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except Exception:
        pass
    # 2) MCP 静态令牌
    try:
        from app.config import get_api_config
        static = get_api_config("mcp")
        return bool(static) and token == static
    except Exception:
        return False
