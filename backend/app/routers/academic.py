"""gpt_academic 集成路由 — 论文翻译/润色/综述/大纲 功能"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..services.academic_service import AcademicEngine
from ..auth import get_current_user

router = APIRouter(prefix="/api/academic", tags=["学术工具"])


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "zh"


class ReviewRequest(BaseModel):
    topic: str


class PolishRequest(BaseModel):
    text: str


class OutlineRequest(BaseModel):
    topic: str


@router.post("/translate")
async def translate_paper(req: TranslateRequest, current_user: dict = Depends(get_current_user)):
    """论文翻译 — gpt_academic 引擎"""
    result = await AcademicEngine.translate_paper(req.text, req.target_lang)
    return {"result": result}


@router.post("/review")
async def literature_review(req: ReviewRequest, current_user: dict = Depends(get_current_user)):
    """文献综述 — gpt_academic 引擎"""
    result = await AcademicEngine.literature_review(req.topic)
    return {"result": result}


@router.post("/polish")
async def polish_writing(req: PolishRequest, current_user: dict = Depends(get_current_user)):
    """论文润色 — gpt_academic 引擎"""
    result = await AcademicEngine.polish_writing(req.text)
    return {"result": result}


@router.post("/outline")
async def paper_outline(req: OutlineRequest, current_user: dict = Depends(get_current_user)):
    """论文大纲 — gpt_academic 引擎"""
    result = await AcademicEngine.paper_outline(req.topic)
    return {"result": result}


@router.get("/health")
async def academic_health():
    """gpt_academic 引擎健康检查"""
    import os
    exists = os.path.exists("/opt/gpt_academic/core_functional.py")
    return {
        "status": "connected" if exists else "not_installed",
        "engine": "gpt_academic + DeepSeek",
        "path": "/opt/gpt_academic" if exists else None
    }
