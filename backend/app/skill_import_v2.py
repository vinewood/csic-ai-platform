"""技能库 v2 导入 — 来自 awesome-chatgpt-prompts + fabric 等开源项目"""
import asyncio
from app.database import async_session
from app.models import Skill
from sqlalchemy import select

NEW_SKILLS = [
    # ====== 写作与内容创作 ======
    {"name":"专业校对润色","category":"工具","icon":"EditPen","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"校对文本的拼写、语法和标点错误，提供修改建议",
     "prompt":"你是专业校对员。请校对以下文本的拼写、语法和标点错误，逐条列出修改建议，不改动原意。"},
    {"name":"创意故事创作","category":"工具","icon":"Sunny","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"根据主题创作引人入胜的短篇故事",
     "prompt":"你是一位有才华的故事作家。请根据用户提供的主题创作一个引人入胜、有转折和情感共鸣的短篇故事。"},
    {"name":"求职信撰写","category":"工具","icon":"Document","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"根据技术栈和职业目标撰写求职信",
     "prompt":"请根据我的技术栈和职业目标撰写一封专业的求职信，突出关键技能和成就。"},
    {"name":"PRD产品需求文档","category":"工具","icon":"DataAnalysis","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"起草产品需求文档（PRD），含问题陈述、目标、用户故事等",
     "prompt":"你是资深产品经理。请为以下产品起草PRD，包括：问题陈述、产品目标、用户故事、功能需求、成功指标、非功能需求。"},
    {"name":"提示词增强器","category":"工具","icon":"MagicStick","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"将简单提示词增强为详细、有层次的专业提示词",
     "prompt":"你是提示词工程专家。请将以下简单提示词增强为更详细、更有层次的专业提示词，包含角色设定、任务描述、约束条件和输出格式。"},
    {"name":"文学评论分析","category":"科研","icon":"Reading","color":"#722ed1","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"从体裁、主题、情节、语言等角度分析文学作品",
     "prompt":"你是文学评论家。请从体裁特点、主题深度、情节结构、语言风格、人物塑造等角度分析以下文学作品节选。"},
    {"name":"代码审查助手","category":"工具","icon":"Monitor","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"审查代码质量，提供改进建议和最佳实践",
     "prompt":"你是资深代码审查员。请审查以下代码：检查代码质量、安全性、性能问题，提供具体的改进建议和替代实现方案。"},
    {"name":"正则表达式生成","category":"工具","icon":"Connection","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"根据需求自动生成正则表达式",
     "prompt":"请根据以下文本匹配需求生成一个精确的正则表达式模式。仅输出正则表达式，附简要说明。"},
    {"name":"单元测试生成","category":"工具","icon":"Check","color":"#1677ff","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"分析代码并生成单元测试用例",
     "prompt":"你是测试专家。请分析以下代码，识别关键业务逻辑，编写覆盖正常路径、边界条件和异常场景的单元测试用例。"},
    {"name":"数据库SQL优化","category":"工具","icon":"DataLine","color":"#1677ff",
     "description":"分析SQL查询性能并提供优化方案",
     "prompt":"你是数据库优化专家。请分析以下SQL查询，识别性能瓶颈，提供索引建议、查询重写方案和执行计划解读。"},
    {"name":"API文档生成","category":"工具","icon":"Files","color":"#1677ff",
     "description":"根据代码自动生成RESTful API文档",
     "prompt":"你是技术文档工程师。请根据以下代码中的API接口，生成OpenAPI/Swagger规范的接口文档，包含路径、方法、参数、响应格式和示例。"},
    {"name":"技术方案评审","category":"工具","icon":"SetUp","color":"#1677ff",
     "description":"评审技术方案，指出风险点和改进方向",
     "prompt":"你是技术架构师。请评审以下技术方案，从可行性、扩展性、安全性、成本四个维度分析，指出潜在风险和改进建议。"},

    # ====== 数据分析 ======
    {"name":"数据洞察分析","category":"工具","icon":"TrendCharts","color":"#13c2c2","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"从数据中提取关键洞察和改进建议",
     "prompt":"你是数据科学家。请分析以下数据集，提取3-5个关键洞察，每个洞察包含数据支撑和改进建议。"},
    {"name":"SWOT分析","category":"工具","icon":"Histogram","color":"#13c2c2",
     "description":"对项目或方案进行SWOT分析",
     "prompt":"请对以下项目/方案进行SWOT分析。分别列出优势(Strengths)、劣势(Weaknesses)、机会(Opportunities)、威胁(Threats)，每个维度3-5条。"},
    {"name":"竞品分析报告","category":"工具","icon":"Search","color":"#13c2c2",
     "description":"生成竞品对比分析报告",
     "prompt":"你是产品分析师。请对以下竞品进行多维度对比分析：核心功能、用户体验、定价策略、市场定位、技术架构、优劣势总结。"},
    
    # ====== 创意与设计 ======
    {"name":"PPT大纲设计","category":"工具","icon":"PictureFilled","color":"#fa8c16",
     "description":"设计专业的PPT演示文稿大纲",
     "prompt":"你是演示设计专家。请为主题设计一份15页PPT大纲，每页包含：标题、核心要点(3-5条)、建议的视觉表现形式(图表/图片/图标)。"},
    {"name":"品牌命名与Slogan","category":"工具","icon":"Medal","color":"#fa8c16",
     "description":"生成品牌名称和Slogan创意",
     "prompt":"你是品牌策划专家。请为以下业务生成5个品牌名称建议和对应的Slogan，每个附简短说明。"},
    {"name":"UI设计建议","category":"工具","icon":"Monitor","color":"#fa8c16",
     "description":"提供用户体验和界面设计建议",
     "prompt":"你是UX/UI设计顾问。请分析以下产品的用户流程，提出3-5个具体的界面和交互改进建议，附优先级说明。"},
    
    # ====== 个人发展 ======
    {"name":"职业规划顾问","category":"工具","icon":"Star","color":"#8b5cf6","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"根据个人背景提供职业发展建议",
     "prompt":"你是职业规划顾问。请根据我的专业背景、技能和兴趣，提供3条可行的职业发展路径建议，含所需技能、时间规划和市场前景。"},
    {"name":"面试模拟训练","category":"工具","icon":"ChatDotSquare","color":"#8b5cf6","github_url":"https://github.com/f/awesome-chatgpt-prompts",
     "description":"模拟面试场景，提供专业面试训练",
     "prompt":"你是资深面试官。请模拟一场技术/管理面试，每次提一个问题，根据回答追问并给出评估反馈。"},
    {"name":"学习路线规划","category":"工具","icon":"Notebook","color":"#8b5cf6",
     "description":"制定系统化的学习路线图",
     "prompt":"你是学习规划师。请为以下学习目标制定3-6个月的学习路线图，包含：阶段划分、学习主题、推荐资源、练习项目、检验标准。"},
    
    # ====== 沟通与协作 ======
    {"name":"邮件润色优化","category":"工具","icon":"Message","color":"#ec4899",
     "description":"优化商务邮件的语气、结构和表达",
     "prompt":"你是商务沟通顾问。请优化以下邮件的语气和结构，使其更专业、清晰、得体。保持核心信息不变。"},
    {"name":"冲突调解建议","category":"工具","icon":"Connection","color":"#ec4899",
     "description":"提供工作冲突的调解和沟通建议",
     "prompt":"你是组织行为学顾问。请分析以下工作冲突场景，提供双方都能接受的调解方案和具体的沟通话术建议。"},
    {"name":"述职报告优化","category":"工具","icon":"TrendCharts","color":"#ec4899",
     "description":"优化述职报告的框架和表达",
     "prompt":"你是人力资源管理顾问。请协助优化述职报告：梳理工作亮点、量化成果数据、平衡个人贡献与团队协作、提出有建设性的改进方向。"},
    
    # ====== 法律与合规 ======
    {"name":"合同条款审查","category":"工具","icon":"Files","color":"#f43f5e",
     "description":"审查合同条款，识别风险点",
     "prompt":"你是法务顾问。请审查以下合同条款，识别潜在风险点和不公平条款，提供修改建议和谈判要点。"},
    {"name":"政策解读分析","category":"工具","icon":"Document","color":"#f43f5e",
     "description":"解读政策文件，分析影响和建议",
     "prompt":"你是政策研究员。请解读以下政策文件，分析其背景、核心要点、对不同主体的影响以及应对建议。"},
    
    # ====== fabric 模式 ======
    {"name":"提取核心观点","category":"工具","icon":"Magnet","color":"#06b6d4","github_url":"https://github.com/danielmiessler/fabric",
     "description":"从长文本中提取最核心的观点和见解",
     "prompt":"请从以下内容中提取最核心的观点和见解。输出格式：1. 一句话总结 2. 5个关键观点(每个1-2句话) 3. 3个可行动的建议。"},
    {"name":"AI提示词优化","category":"工具","icon":"MagicStick","color":"#06b6d4","github_url":"https://github.com/danielmiessler/fabric",
     "description":"优化和增强AI提示词的效果",
     "prompt":"你是提示词优化专家。请分析并优化以下提示词，使其更加具体、结构化，提升AI输出质量。添加角色设定、任务细节、格式要求和质量标准。"},
    {"name":"创建摘要","category":"工具","icon":"Histogram","color":"#06b6d4","github_url":"https://github.com/danielmiessler/fabric",
     "description":"将长文本压缩为高质量摘要",
     "prompt":"你是信息提炼专家。请将以下内容总结为简洁摘要：1. 一句话概括 2. 3个关键要点 3. 最重要的一个数据/事实。保持客观准确。"},
    {"name":"分析主张逻辑","category":"工具","icon":"DataAnalysis","color":"#06b6d4","github_url":"https://github.com/danielmiessler/fabric",
     "description":"分析论证中的逻辑结构和漏洞",
     "prompt":"你是逻辑分析专家。请分析以下论述的逻辑结构：1. 识别核心主张 2. 评估证据有效性 3. 找出潜在的逻辑谬误 4. 提出反驳论点。"},
    {"name":"编写微内容","category":"工具","icon":"EditPen","color":"#06b6d4","github_url":"https://github.com/danielmiessler/fabric",
     "description":"为社交媒体编写精炼的微内容",
     "prompt":"你是社交媒体内容专家。请根据以下长内容，为不同平台创作微内容版本：微博(140字)、朋友圈(200字)、LinkedIn(300字专业版)。"},
]

async def import_all():
    async with async_session() as session:
        imported = 0
        for s in NEW_SKILLS:
            check = await session.execute(select(Skill).where(Skill.name == s["name"]))
            if check.scalar_one_or_none():
                continue
            skill = Skill(
                name=s["name"], category=s["category"], icon=s["icon"],
                prompt=s["prompt"], description=s.get("description", ""),
                color=s.get("color", "#1677ff"), github_url=s.get("github_url")
            )
            session.add(skill)
            imported += 1
        await session.commit()
        total = (await session.execute(select(Skill))).scalars().all()
        print(f"✅ 导入 {imported} 个技能 (总计 {len(total)} 个)")

if __name__ == "__main__":
    asyncio.run(import_all())
