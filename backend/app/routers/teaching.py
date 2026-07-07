"""教学管理路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import User, TeachingTopic, Inspiration
from ..schemas import MessageResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/teaching", tags=["教学"])


# ---- Request Schemas ----

class GenerateRequest(BaseModel):
    input: str
    depth: str = "标准"


class InspireRequest(BaseModel):
    topic_id: int
    type: str


class ContentRequest(BaseModel):
    topic_id: int
    content_types: list[str]


# ---- Helper ----

async def _get_current_user_id(token_payload: dict, db: AsyncSession) -> int:
    username = token_payload.get("sub")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user.id


# ---- 教学选题生成 ----

@router.post("/generate")
async def generate_topics(
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    depth_map = {"浅度": 3, "标准": 5, "深度": 7}
    count = depth_map.get(req.depth, 5)

    levels = ["入门", "标准深度", "深入"]
    audiences = ["本科生", "研究生", "青年教师", "企业技术人员"]
    mock_topics = [
        {
            "title": f"{req.input}教学专题{i+1}：{['基础概念', '核心原理', '实践应用', '前沿进展', '案例分析', '实验设计', '项目实战'][i]}",
            "desc": f"围绕{req.input}，系统讲解{i+1}个核心知识点，配合实例教学。",
            "level": levels[i % len(levels)],
            "hours": 2 + i * 2,
            "audience": audiences[i % len(audiences)],
        }
        for i in range(count)
    ]

    topics = []
    for t in mock_topics:
        topic = TeachingTopic(
            title=t["title"],
            description=t["desc"],
            level=t["level"],
            hours=t["hours"],
            audience=t["audience"],
            user_id=user_id,
        )
        db.add(topic)
        topics.append(topic)

    await db.commit()
    for t in topics:
        await db.refresh(t)

    return {"topics": [
        {
            "id": t.id, "title": t.title, "description": t.description,
            "level": t.level, "hours": t.hours, "audience": t.audience,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in topics
    ]}


# ---- 教学灵感生成 ----

@router.post("/inspire")
async def inspire_topic(
    req: InspireRequest,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)

    result = await db.execute(
        select(TeachingTopic).where(
            TeachingTopic.id == req.topic_id, TeachingTopic.user_id == user_id
        )
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="教学选题不存在")

    type_map = {
        "案例": [
            {"title": "行业典型案例", "detail": f"收集{topic.title}相关的3-5个行业典型案例，涵盖成功与失败经验。"},
            {"title": "对比分析案例", "detail": f"设计{topic.title}的对比分析案例，突出关键差异与决策要点。"},
            {"title": "实践项目案例", "detail": f"提供一个完整的{topic.title}实践项目案例，包含需求、设计、实现与评估。"},
            {"title": "历史演进案例", "detail": f"梳理{topic.title}的发展历程，以关键里程碑事件为案例进行讲解。"},
        ],
        "互动": [
            {"title": "课堂讨论主题", "detail": f"提出3个围绕{topic.title}的开放性问题，引导学生分组讨论。"},
            {"title": "实时投票设计", "detail": f"设计{topic.title}相关的5道选择题，用于课堂实时投票互动。"},
            {"title": "角色扮演场景", "detail": f"设计{topic.title}的角色扮演场景，让学生分别扮演不同角色进行决策。"},
            {"title": "小组竞赛方案", "detail": f"将{topic.title}分解为多个子任务，设计小组竞赛机制。"},
        ],
        "扩展": [
            {"title": "跨学科关联", "detail": f"探讨{topic.title}与相关学科的交叉点，拓展学生的知识视野。"},
            {"title": "前沿文献推荐", "detail": f"推荐{topic.title}领域的3篇前沿综述和研究论文。"},
            {"title": "实践拓展任务", "detail": f"设计{topic.title}的课后拓展实践任务，鼓励学生动手操作。"},
            {"title": "职业发展衔接", "detail": f"分析{topic.title}在相关行业岗位中的应用，帮助学生明确职业方向。"},
        ],
        "资源": [
            {"title": "推荐教材与参考书", "detail": f"列出{topic.title}的经典教材、参考书和在线课程资源。"},
            {"title": "开源工具与平台", "detail": f"推荐{topic.title}相关的开源工具、实验平台和数据集。"},
            {"title": "视频与多媒体资源", "detail": f"整理{topic.title}相关的优质视频教程、讲座和播客资源。"},
            {"title": "考试题库与练习", "detail": f"生成{topic.title}的配套练习题和考试题库，覆盖不同难度层次。"},
        ],
    }

    inspirations_data = type_map.get(req.type, type_map["扩展"])
    inspirations = []
    for insp in inspirations_data:
        obj = Inspiration(
            topic_id=req.topic_id,
            type=req.type,
            title=insp["title"],
            detail=insp["detail"],
        )
        db.add(obj)
        inspirations.append(obj)

    await db.commit()
    for insp in inspirations:
        await db.refresh(insp)

    return {"inspirations": [
        {
            "id": i.id, "type": i.type, "title": i.title,
            "detail": i.detail, "adopted": i.adopted,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in inspirations
    ]}


# ---- 教学内容生成 ----

@router.post("/content")
async def generate_content(
    req: ContentRequest,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    result = await db.execute(
        select(TeachingTopic).where(
            TeachingTopic.id == req.topic_id, TeachingTopic.user_id == user_id
        )
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="教学选题不存在")

    content_results = {}

    if "大纲" in req.content_types or "outline" in req.content_types:
        outline = (
            f"# {topic.title} 教学大纲\n\n"
            f"## 课程概述\n"
            f"{topic.description}\n\n"
            f"## 教学目标\n"
            f"1. 理解{topic.title}的核心概念与基本原理\n"
            f"2. 掌握相关技术与方法论\n"
            f"3. 能够独立完成实践项目\n\n"
            f"## 课时安排（共{topic.hours}课时）\n"
            f"- 第1-2课时：基础知识讲解\n"
            f"- 第3-4课时：核心原理分析\n"
            f"- 第5-6课时：案例实践与讨论\n"
            f"- 第7-{topic.hours}课时：综合项目实训\n\n"
            f"## 考核方式\n"
            f"- 课堂参与：20%\n"
            f"- 课后作业：30%\n"
            f"- 期末项目：50%"
        )
        topic.content_outline = outline
        content_results["大纲"] = outline

    if "讲稿" in req.content_types or "lecture" in req.content_types:
        lecture = (
            f"# {topic.title} 讲稿\n\n"
            f"## 开场（5分钟）\n"
            f"大家好，今天我们一起来学习{topic.title}。\n\n"
            f"## 核心内容（{max(topic.hours - 1, 1)}课时）\n"
            f"### 第一节：背景介绍\n"
            f"{topic.description}\n"
            f"本课程面向{topic.audience}群体，内容难度为【{topic.level}】层次。\n\n"
            f"### 第二节：核心知识点\n"
            f"1. 理论框架与基础概念\n"
            f"2. 关键技术问题分析\n"
            f"3. 实践应用场景\n\n"
            f"## 互动环节（10分钟）\n"
            f"课堂讨论：请同学们分享自己对该主题的理解。\n\n"
            f"## 总结与作业（5分钟）\n"
            f"总结本次课的核心内容，布置课后作业。"
        )
        topic.lecture_script = lecture
        content_results["讲稿"] = lecture

    if "课件" in req.content_types or "ppt" in req.content_types:
        ppt = (
            f"# {topic.title} 课件结构\n\n"
            f"## 幻灯片列表\n\n"
            f"1. **封面页**：{topic.title}\n"
            f"   - 授课对象：{topic.audience}\n"
            f"   - 课时：{topic.hours}课时\n\n"
            f"2. **目录页**\n"
            f"   - 课程背景\n"
            f"   - 核心概念\n"
            f"   - 方法论\n"
            f"   - 案例分析\n"
            f"   - 课后练习\n\n"
            f"3. **课程背景**（2-3页）\n"
            f"   - {topic.description}\n\n"
            f"4. **核心概念**（3-5页）\n"
            f"   - 关键术语与定义\n"
            f"   - 原理框图\n\n"
            f"5. **方法论**（3-5页）\n"
            f"   - 主流方法与技术路线\n"
            f"   - 对比分析\n\n"
            f"6. **案例分析**（2-3页）\n"
            f"   - 典型应用场景\n\n"
            f"7. **总结与作业**（1-2页）\n\n"
            f"## 设计建议\n"
            f"- 使用 {topic.level} 级别的语言表达\n"
            f"- 每页幻灯片控制在5-7个要点以内\n"
            f"- 适当插入图表和示意图"
        )
        topic.ppt_outline = ppt
        content_results["课件"] = ppt

    await db.commit()
    await db.refresh(topic)

    return {
        "topic_id": topic.id,
        "title": topic.title,
        "content": content_results,
        "content_outline": topic.content_outline,
        "lecture_script": topic.lecture_script,
        "ppt_outline": topic.ppt_outline,
    }


# ---- 查询与删除 ----

@router.get("/topics")
async def list_topics(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    result = await db.execute(
        select(TeachingTopic)
        .where(TeachingTopic.user_id == user_id)
        .order_by(TeachingTopic.id.desc())
    )
    topics = result.scalars().all()
    return {"topics": [
        {
            "id": t.id, "title": t.title, "description": t.description,
            "level": t.level, "hours": t.hours, "audience": t.audience,
            "content_outline": t.content_outline,
            "lecture_script": t.lecture_script,
            "ppt_outline": t.ppt_outline,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in topics
    ]}


@router.get("/topics/{topic_id}")
async def get_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    result = await db.execute(
        select(TeachingTopic).where(
            TeachingTopic.id == topic_id, TeachingTopic.user_id == user_id
        )
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="教学选题不存在")

    # Load inspirations
    insp_result = await db.execute(
        select(Inspiration)
        .where(Inspiration.topic_id == topic_id)
        .order_by(Inspiration.id)
    )
    inspirations = insp_result.scalars().all()

    return {
        "topic": {
            "id": topic.id, "title": topic.title, "description": topic.description,
            "level": topic.level, "hours": topic.hours, "audience": topic.audience,
            "content_outline": topic.content_outline,
            "lecture_script": topic.lecture_script,
            "ppt_outline": topic.ppt_outline,
            "created_at": topic.created_at.isoformat() if topic.created_at else None,
        },
        "inspirations": [
            {
                "id": i.id, "type": i.type, "title": i.title,
                "detail": i.detail, "adopted": i.adopted,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in inspirations
        ],
    }


@router.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(get_current_user),
):
    user_id = await _get_current_user_id(token, db)
    result = await db.execute(
        select(TeachingTopic).where(
            TeachingTopic.id == topic_id, TeachingTopic.user_id == user_id
        )
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="教学选题不存在")

    # Cascade delete inspirations (model has cascade="all, delete-orphan")
    await db.delete(topic)
    await db.commit()
    return MessageResponse(message="删除成功")
