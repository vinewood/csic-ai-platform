"""技能管理路由 — CRUD + 收藏 + 种子数据"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Skill
from ..schemas import MessageResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/skills", tags=["技能"],
    dependencies=[Depends(get_current_user)])  # v3.1.2 路由级鉴权


# ---- 请求/响应模型 ----
class SkillCreate(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    prompt: str = ""
    icon: str = "MagicStick"
    color: str = "#1677ff"


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    prompt: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class SkillOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    prompt: str
    icon: str
    color: str
    rating: float
    favorited: bool
    is_preset: bool
    user_id: Optional[int] = None
    created_at: Optional[str] = None


class FavoriteResponse(BaseModel):
    message: str
    favorited: bool


# ---- 列表 / 创建 ----
@router.get("", response_model=list[SkillOut])
async def list_skills(db: AsyncSession = Depends(get_db)):
    """获取全部技能"""
    result = await db.execute(select(Skill).order_by(Skill.id))
    skills = result.scalars().all()
    return [_skill_to_dict(s) for s in skills]


@router.post("", response_model=MessageResponse)
async def create_skill(
    req: SkillCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """创建新技能"""
    skill = Skill(
        name=req.name,
        description=req.description,
        category=req.category,
        prompt=req.prompt,
        icon=req.icon,
        color=req.color,
    )
    db.add(skill)
    await db.commit()
    return MessageResponse(message="技能已创建")


# ---- 更新 / 删除 ----
@router.put("/{skill_id}", response_model=MessageResponse)
async def update_skill(
    skill_id: int,
    req: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """更新技能"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)
    await db.commit()
    return MessageResponse(message="技能已更新")


@router.delete("/{skill_id}", response_model=MessageResponse)
async def delete_skill(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """删除技能"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    await db.delete(skill)
    await db.commit()
    return MessageResponse(message="技能已删除")


# ---- 收藏 ----
@router.put("/{skill_id}/favorite", response_model=FavoriteResponse)
async def toggle_favorite(
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """切换收藏状态"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    skill.favorited = not skill.favorited
    await db.commit()
    return FavoriteResponse(
        message="已收藏" if skill.favorited else "已取消收藏",
        favorited=skill.favorited,
    )


@router.get("/favorites", response_model=list[SkillOut])
async def list_favorites(db: AsyncSession = Depends(get_db)):
    """获取收藏的技能"""
    result = await db.execute(
        select(Skill).where(Skill.favorited == True).order_by(Skill.id)
    )
    skills = result.scalars().all()
    return [_skill_to_dict(s) for s in skills]


# ---- 辅助 ----
def _skill_to_dict(skill: Skill) -> dict:
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description or "",
        "category": skill.category or "",
        "prompt": skill.prompt or "",
        "icon": skill.icon or "MagicStick",
        "color": skill.color or "#1677ff",
        "rating": skill.rating or 5.0,
        "favorited": skill.favorited or False,
        "is_preset": skill.is_preset or False,
        "user_id": skill.user_id,
        "created_at": skill.created_at.isoformat() if skill.created_at else None,
    }


# ---- 种子数据 ----
DEFAULT_SKILLS = [
    {
        "name": "智能写作助手",
        "description": "辅助撰写各类技术文档、报告、方案，支持大纲生成、内容扩写与润色。",
        "category": "办公效率",
        "prompt": "你是一名专业的写作助手，请帮助用户完成技术文档的撰写工作，包括生成大纲、扩写内容和润色文字。",
        "icon": "EditNote",
        "color": "#1677ff",
    },
    {
        "name": "代码生成助手",
        "description": "根据需求生成 Python / JavaScript / Java 等语言的代码片段，含注释与示例。",
        "category": "编程开发",
        "prompt": "你是一名资深程序员，请根据用户的需求生成高质量的代码片段，包含必要的注释说明。",
        "icon": "Code",
        "color": "#52c41a",
    },
    {
        "name": "数据可视化",
        "description": "将原始数据转换为图表描述与 ECharts 配置，辅助快速搭建可视化面板。",
        "category": "数据分析",
        "prompt": "你是一名数据分析师，请根据用户提供的数据，生成适合的图表类型建议和对应的 ECharts 配置代码。",
        "icon": "BarChart",
        "color": "#fa8c16",
    },
    {
        "name": "船舶设计辅助",
        "description": "提供船舶设计规范查询、结构计算建议与设计思路推演。",
        "category": "船舶工程",
        "prompt": "你是一名船舶设计专家，请回答用户在船舶设计中的技术问题，提供规范、计算方法和设计建议。",
        "icon": "DirectionsBoat",
        "color": "#13c2c2",
    },
    {
        "name": "知识问答",
        "description": "基于企业知识库与行业资料，为用户提供准确的技术问答服务。",
        "category": "知识管理",
        "prompt": "你是企业知识助手，请基于提供的知识库内容，准确回答用户提出的技术问题。",
        "icon": "Psychology",
        "color": "#722ed1",
    },
    {
        "name": "文献综述",
        "description": "检索并归纳学术文献要点，快速生成综述初稿。",
        "category": "学术研究",
        "prompt": "你是一名科研助手，请帮助用户检索相关文献并归纳核心观点，生成综述报告。",
        "icon": "MenuBook",
        "color": "#eb2f96",
    },
    {
        "name": "报告生成",
        "description": "根据关键数据与主题，一键生成结构完整的工作报告与汇报材料。",
        "category": "办公效率",
        "prompt": "你是报告撰写专家，请根据用户提供的主题和数据，生成结构完整、逻辑清晰的工作报告。",
        "icon": "Description",
        "color": "#1677ff",
    },
    {
        "name": "图表解读",
        "description": "上传图表图片或描述，AI 分析图表趋势与关键结论。",
        "category": "数据分析",
        "prompt": "你是一名数据分析专家，请帮助用户解读图表数据，分析趋势、异常点和关键结论。",
        "icon": "Insights",
        "color": "#fa541c",
    },
    {
        "name": "翻译助手",
        "description": "支持中英等多语言互译，保留技术术语准确性。",
        "category": "办公效率",
        "prompt": "你是一名专业翻译，请将用户提供的内容准确翻译为目标语言，注意保留技术术语的一致性。",
        "icon": "Translate",
        "color": "#2f54eb",
    },
    {
        "name": "技术文档",
        "description": "撰写 API 文档、接口说明、部署手册等标准技术文档。",
        "category": "编程开发",
        "prompt": "你是一名技术写作专家，请帮助用户撰写格式规范、内容完整的技术文档。",
        "icon": "Article",
        "color": "#08979c",
    },
    {
        "name": "项目规划",
        "description": "协助制定项目计划、分解任务、评估风险与资源需求。",
        "category": "项目管理",
        "prompt": "你是一名项目管理专家，请帮助用户制定详细的项目计划，包括任务分解、里程碑设置和风险评估。",
        "icon": "AccountTree",
        "color": "#d4b106",
    },
    {
        "name": "头脑风暴",
        "description": "围绕主题发散创意，生成多种思路与实施方案。",
        "category": "创意灵感",
        "prompt": "你是一名创意顾问，请围绕用户提出的主题，从多个角度展开头脑风暴，生成具有创新性的思路和建议。",
        "icon": "AutoAwesome",
        "color": "#eb2f96",
    },
    {
        "name": "代码审查",
        "description": "对提交的代码进行审查，指出潜在问题与改进建议。",
        "category": "编程开发",
        "prompt": "你是一名代码审查专家，请仔细审查用户提供的代码，指出潜在的错误、性能问题和改进建议。",
        "icon": "Review",
        "color": "#52c41a",
    },
    {
        "name": "会议纪要",
        "description": "根据会议录音或文字记录，自动生成结构化会议纪要。",
        "category": "办公效率",
        "prompt": "你是一名会议纪要助手，请根据用户的会议记录，提取关键信息并生成结构清晰的会议纪要。",
        "icon": "RecordVoiceOver",
        "color": "#595959",
    },
]


async def seed_skills(db: AsyncSession):
    """向 skills 表插入预设技能（表为空时执行）"""
    result = await db.execute(select(Skill).limit(1))
    if result.scalar_one_or_none():
        return  # 已有数据，跳过

    for data in DEFAULT_SKILLS:
        skill = Skill(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            prompt=data["prompt"],
            icon=data["icon"],
            color=data["color"],
            rating=5.0,
            favorited=False,
            is_preset=True,
        )
        db.add(skill)
    await db.commit()
