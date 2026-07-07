"""教学工作台路由 — 调用 AI API 生成真实教学内容"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..auth import get_current_user
from ..config import get_api_config

router = APIRouter(prefix="/api/teaching", tags=["教学"])

# 教学请求模型
class TeachingRequest(BaseModel):
    input: Optional[str] = "党建培训"
    depth: Optional[str] = "标准"
    topic: Optional[str] = None
    inspire_type: Optional[str] = None
    content_types: Optional[List[str]] = None


async def _ai_call(messages: list, model: str = "deepseek") -> str:
    """通用 AI 调用函数"""
    api_key = get_api_config(model)
    if not api_key:
        raise HTTPException(status_code=503, detail=f"请先配置 {model} 的 API Key：系统管理 → API 配置")

    import httpx
    endpoint = "https://api.deepseek.com/chat/completions"
    if model == "qwen":
        endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    elif model == "zhipu":
        endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": messages, "temperature": 0.7}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"AI 调用失败: {resp.text[:200]}")
        return resp.json()["choices"][0]["message"]["content"]


@router.post("/generate")
async def generate_topics(req: TeachingRequest, current_user: dict = Depends(get_current_user)):
    """AI 生成教学课题"""
    input_text = req.input or "党建培训"
    count = {"基础": 3, "标准": 5, "深入": 7}.get(req.depth or "标准", 5)

    prompt = f"""你是党校教学课程设计专家。请为主题"{input_text}"设计{count}个教学课题。

要求：
- 每个课题包含 title（课题名称）、desc（简短描述）、level（基础/标准/深入）、hours（课时数）、audience（适用对象）
- 返回严格的 JSON 数组格式

仅输出 JSON 数组，不要其他文字。"""

    try:
        result = await _ai_call([{"role": "user", "content": prompt}])
        # 清理 AI 输出
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result[:-3]
        topics = json.loads(result)
        if isinstance(topics, list) and len(topics) > 0:
            return {"topics": topics}
    except Exception:
        pass

    # Fallback: 模板生成
    levels = ["入门", "标准深度", "深入"]
    audiences = ["党校学员", "青年干部", "中层管理人员", "党委成员"]
    return {"topics": [
        {
            "title": f"{input_text}教学专题{i+1}",
            "desc": f"围绕{input_text}，系统讲解核心知识点",
            "level": levels[i % 3],
            "hours": 2 + i * 2,
            "audience": audiences[i % 4]
        } for i in range(count)
    ]}


@router.post("/inspire")
async def inspire_ideas(req: TeachingRequest, current_user: dict = Depends(get_current_user)):
    """AI 生成教学灵感"""
    topic_title = req.topic or "党建教学"
    inspire_type = req.inspire_type or "案例"

    prompt = f"""你是党校教学创新顾问。请为主题"{topic_title}"生成4条{inspire_type}类的教学创意。

要求：
- 每条创意包含 title（简短标题）和 detail（100字以内的具体描述）
- 创意要新颖、实用，适合党校教学场景
- 返回严格的 JSON 数组格式

仅输出 JSON 数组。"""

    try:
        result = await _ai_call([{"role": "user", "content": prompt}])
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rstrip("```").strip()
        ideas = json.loads(result)
        if isinstance(ideas, list) and len(ideas) > 0:
            return {"ideas": ideas}
    except Exception:
        pass

    return {"ideas": [
        {"title": "真实案例分析", "detail": f"围绕{topic_title}，选取实际工作场景进行案例教学"},
        {"title": "互动讨论", "detail": f"分组讨论{topic_title}相关的实际问题，分享经验"},
        {"title": "模拟演练", "detail": f"设计{topic_title}的模拟场景，学员实操演练"},
        {"title": "专家讲座", "detail": f"邀请{topic_title}领域专家进行专题讲座和经验分享"},
    ]}


@router.post("/content")
async def generate_content(req: TeachingRequest, current_user: dict = Depends(get_current_user)):
    """AI 生成教学内容（大纲/讲稿/课件）"""
    topic_title = req.topic or "党建教学专题"
    types = req.content_types or ["教学大纲"]

    result = {}
    for t in types:
        prompt_map = {
            "教学大纲": "请为主题 " + topic_title + " 生成一份详细的教学大纲，包含课程目标、教学内容、课时安排、考核方式，用 Markdown 格式",
            "逐页讲稿": "请为主题 " + topic_title + " 生成一份教师讲稿，包含开场白、逐页讲解内容、总结，用 Markdown 格式",
            "配套案例": "请为主题 " + topic_title + " 生成3个配套教学案例，每个案例包含背景、问题、解决方案",
            "随堂测验": "请为主题 " + topic_title + " 生成5道随堂测验题（含答案），题型包括选择题和简答题",
            "PPT提纲": "请为主题 " + topic_title + " 生成一份PPT课件提纲，10-15页，每页标注标题和要点",
        }
        prompt = prompt_map.get(t, "请为主题 " + topic_title + " 生成" + t + "内容")

        try:
            content = await _ai_call([{"role": "user", "content": prompt}])
            result[t] = content
        except Exception:
            result[t] = f"【{t}】AI 生成失败，请检查 API Key 配置后重试。"

    return {"contents": result}


# 兼容旧接口
@router.get("/knowledge-bases")
async def list_teaching_kb():
    """获取教学知识库列表（从数据库）"""
    from ..database import async_session
    from ..models import KnowledgeBase
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(select(KnowledgeBase).where(KnowledgeBase.type == "教学"))
        kbs = result.scalars().all()
        return [{"id": kb.id, "name": kb.name, "description": kb.description} for kb in kbs]
