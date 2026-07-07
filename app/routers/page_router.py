"""CSIC Party School AI Platform - Page Routes."""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

router = APIRouter()
_tpl_dir = Path(__file__).parent.parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(_tpl_dir)))

def _render(template_name: str, request: Request, **extra) -> HTMLResponse:
    """Render a Jinja2 template with common context."""
    user = getattr(request.state, "user", None)
    ctx = {
        "request": request,
        "user": user,
        "app_name": "中船党校 AI 智能平台",
    }
    ctx.update(extra)
    template = jinja_env.get_template(template_name)
    return HTMLResponse(template.render(ctx))


# ── Public Pages ────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return _render("public/landing.html", request)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return _render("public/login.html", request)


# ── Core Pages ──────────────────────────────────────────────

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return _render("chat.html", request)


# ── Workspace Pages ─────────────────────────────────────────

@router.get("/workspace/teaching", response_class=HTMLResponse)
async def teaching_workspace(request: Request):
    return _render("workspace/teaching.html", request, active_nav="teaching")


@router.get("/workspace/research", response_class=HTMLResponse)
async def research_workspace(request: Request):
    return _render("workspace/research.html", request, active_nav="research")


@router.get("/workspace/news", response_class=HTMLResponse)
async def news_workspace(request: Request):
    return _render("workspace/news.html", request, active_nav="news")


@router.get("/workspace/skills", response_class=HTMLResponse)
async def skills_workspace(request: Request):
    return _render("workspace/skills.html", request, active_nav="skills")


@router.get("/workspace/video", response_class=HTMLResponse)
async def video_workspace(request: Request):
    return _render("workspace/video.html", request, active_nav="video")


@router.get("/workspace/admin", response_class=HTMLResponse)
async def admin_workspace(request: Request):
    return _render("workspace/admin.html", request, active_nav="admin")


@router.get("/workspace/knowledge", response_class=HTMLResponse)
async def knowledge_workspace(request: Request):
    return _render("workspace/knowledge.html", request, active_nav="knowledge")
