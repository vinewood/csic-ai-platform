"""教学工作台路由 — 调用 AI API 生成真实教学内容"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..auth import get_current_user
from ..config import get_api_config

router = APIRouter(prefix="/api/teaching", tags=["教学"],
    dependencies=[Depends(get_current_user)])  # v3.1.2 路由级鉴权

# 教学请求模型
class TeachingRequest(BaseModel):
    input: Optional[str] = "党建培训"
    depth: Optional[str] = "标准"
    topic: Optional[str] = None
    inspire_type: Optional[str] = None
    content_types: Optional[List[str]] = None
    model: Optional[str] = "deepseek"  # v3.1.0：支持指定模型，路由见 MODEL_ENDPOINTS


async def _ai_call(messages: list, model: str = "deepseek") -> str:
    """通用 AI 调用（非流式）—— 统一走 MODEL_ENDPOINTS 路由

    修复历史 bug：旧实现无视 model 参数、永远发 deepseek 模型名，
    导致 qwen/zhipu 等百炼路由必然报错。现统一映射端点+模型名+密钥来源。
    """
    from ..services.dify_service import MODEL_ENDPOINTS

    ep = MODEL_ENDPOINTS.get(model, MODEL_ENDPOINTS["deepseek"])
    if ep.get("route") == "deepseek":
        api_key = get_api_config("deepseek")
        provider_label = "DeepSeek"
    else:
        api_key = get_api_config("bailian") or get_api_config("dashscope") or get_api_config("qwen")
        provider_label = "百炼/DashScope"
    if not api_key:
        raise HTTPException(status_code=503, detail=f"请先配置 {provider_label} 的 API Key：系统管理 → API 配置")

    import httpx
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            ep["url"],
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": ep["model"], "messages": messages, "temperature": 0.7}
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
        result = await _ai_call([{"role": "user", "content": prompt}], model=req.model)
    except HTTPException:
        raise  # 503 缺 key / 502 AI 故障必须如实上抛，禁止吞掉后冒充成功
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 课题生成失败：{e}")

    # 清理 AI 输出并解析 JSON；解析失败如实报错，禁止回退模板假数据
    result = result.strip()
    if result.startswith("```"):
        result = result.split("\n", 1)[1]
        if result.endswith("```"):
            result = result[:-3]
    try:
        topics = json.loads(result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI 返回格式异常（非 JSON），请重试")
    if isinstance(topics, list) and len(topics) > 0:
        return {"topics": topics}
    raise HTTPException(status_code=502, detail="AI 未返回有效课题，请重试")


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
        result = await _ai_call([{"role": "user", "content": prompt}], model=req.model)
    except HTTPException:
        raise  # 503 缺 key / 502 AI 故障必须如实上抛
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 灵感生成失败：{e}")

    result = result.strip()
    if result.startswith("```"):
        result = result.split("\n", 1)[1].rstrip("```").strip()
    try:
        ideas = json.loads(result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI 返回格式异常（非 JSON），请重试")
    if isinstance(ideas, list) and len(ideas) > 0:
        return {"ideas": ideas}
    raise HTTPException(status_code=502, detail="AI 未返回有效创意，请重试")


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
            content = await _ai_call([{"role": "user", "content": prompt}], model=req.model)
            result[t] = content
        except Exception:
            result[t] = f"【{t}】AI 生成失败，请检查 API Key 配置后重试。"

    return {"contents": result}


# 兼容旧接口
@router.get("/topics")
async def list_teaching_topics():
    """获取已保存的教学课题"""
    from ..database import async_session
    from ..models import TeachingTopic
    from sqlalchemy import select
    async with async_session() as s:
        result = await s.execute(select(TeachingTopic).order_by(TeachingTopic.id.desc()).limit(20))
        topics = result.scalars().all()
        return [{"id": t.id, "title": t.title, "description": t.description, "level": t.level, "hours": t.hours, "audience": t.audience} for t in topics]

@router.get("/save-topic")
async def save_topic(title: str, desc: str = "", level: str = "标准", hours: int = 4, audience: str = "党校学员"):
    """保存教学课题"""
    from ..database import async_session
    from ..models import TeachingTopic
    async with async_session() as s:
        topic = TeachingTopic(title=title, description=desc, level=level, hours=hours, audience=audience)
        s.add(topic)
        await s.commit()
        return {"id": topic.id, "saved": True}

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
