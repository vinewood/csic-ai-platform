"""种子数据 — 全量初始化所有内置数据（技能/RSS/知识库/科研/教学）"""
import bcrypt
from sqlalchemy import select
from app.models import User, Skill, KnowledgeBase, KnowledgeDoc, RssSource, ResearchTopic


async def seed_all(session):
    """全量种子：用户、技能、RSS、知识库、科研、教学"""
    existing = await session.execute(select(User).limit(1))
    if existing.scalar_one_or_none():
        return  # 已有数据

    # ── 1. 管理员 ──
    user = User(
        username="admin", email="admin@csic.cn",
        hashed_password=bcrypt.hashpw(b"***REMOVED-PASSWORD***", bcrypt.gensalt()).decode(),
        is_active=True, role="admin"
    )
    session.add(user)
    await session.flush()

    # ── 2. 普通用户 ──
    for uname in ["lecturer01", "researcher01", "editor01"]:
        session.add(User(username=uname, email=f"{uname}@csic.cn",
                          hashed_password=bcrypt.hashpw(b"***REMOVED-PASSWORD***", bcrypt.gensalt()).decode(),
                          is_active=True, role="user" if uname != "editor01" else "editor"))

    # ── 3. 技能中心（14个真实技能 — 带系统提示词和图标） ──
    skills_data = [
        ("课题选题生成", "科研", "Lightbulb", "你是党校科研助手。根据用户输入的研究方向，生成4个规范的学术选题，每个选题包含：题目、研究方向、创新点、可行性分析。"),
        ("选题测评", "科研", "Assessment", "请对以下选题进行四维度评估（学术价值/创新性/可行性/实践意义），每项0-100分，给出综合建议。"),
        ("文献综述", "科研", "MenuBook", "根据输入的主题，生成一篇结构完整的文献综述，包含：研究背景、理论基础、研究现状、研究空白、参考文献。"),
        ("论文润色", "科研", "AutoFixHigh", "请对话学术论文进行语言润色，修正语法错误，优化表达流畅性，保持学术风格不变。"),
        ("投稿选刊", "科研", "Send", "根据论文主题和研究方向，推荐3-5个合适的投稿期刊，包含期刊名称、影响因子、审稿周期、录用率。"),
        ("理论文章撰写", "科研", "Article", "根据输入的理论主题，撰写一篇结构完整的理论文章，包含：引言、理论基础、分析框架、政策建议。"),
        ("课程设计", "教学", "DesignServices", "根据培训目标和学员对象，设计一份完整的课程方案，包含：课程目标、教学大纲、课时安排、考核方式。"),
        ("课件生成", "教学", "Slideshow", "根据课程主题生成一份PPT课件大纲，包含：封面、目录、逐页内容、总结页，每页标注要点。"),
        ("经验萃取", "教学", "FilterVintage", "从输入的经验材料中提取可复用的方法论和最佳实践，输出结构化经验档案。"),
        ("试题生成", "教学", "Quiz", "根据教学内容生成一套考试试题，包含：单选题、多选题、判断题、简答题，标注难度和分值。"),
        ("培训方案", "教学", "Assignment", "根据培训需求，制定一份完整的培训方案，包含：培训目标、对象分析、课程体系、师资安排、评估方式。"),
        ("新闻摘要", "新闻", "Summarize", "对输入的新闻内容进行200字以内的专业摘要，提取关键信息，保持客观中立。"),
        ("舆情分析", "新闻", "TrendingUp", "对输入的多条新闻进行舆情分析，识别舆论倾向、关键议题、情感分布，给出研判建议。"),
        ("会议纪要", "工具", "Mic", "根据会议录音转写内容，生成结构化的会议纪要，包含：会议主题、参与人、讨论要点、决议事项、待办任务。"),
    ]
    for name, category, icon, prompt in skills_data:
        session.add(Skill(name=name, category=category, icon=icon, prompt=prompt))

    # ── 4. RSS 新闻源（20个内置源） ──
    rss_sources = [
        ("新华网", "http://www.xinhuanet.com/politics/leaders/rss.xml", "官方", True),
        ("人民网", "http://www.people.com.cn/rss/politics.xml", "官方", True),
        ("求是网", "http://www.qstheory.cn/v1/qswp.htm", "官方", True),
        ("中国政府网", "http://www.gov.cn/rss/zcjd.xml", "官方", True),
        ("国务院国资委", "http://www.sasac.gov.cn/n2588025/n2588139/index.html", "官方", True),
        ("中国船舶", "http://www.cssc.net.cn/component_news/news.php", "行业", True),
        ("国防科工局", "https://www.sastind.gov.cn", "行业", True),
        ("自然资源部", "http://www.mnr.gov.cn", "政策", True),
        ("36氪科技", "https://36kr.com/feed", "科技", True),
        ("虎嗅网", "https://www.huxiu.com/rss/0.xml", "科技", True),
        ("机器之心", "https://www.jiqizhixin.com/rss", "科技", True),
        ("量子位", "https://www.qbitai.com/feed", "科技", True),
        ("科学网", "http://news.sciencenet.cn/xml/news.aspx", "科研", True),
        ("中国知网", "https://kns.cnki.net", "科研", False),
        ("人民日报评论", "http://opinion.people.com.cn/rss/opinion.xml", "评论", True),
        ("学习强国", "https://www.xuexi.cn", "学习", True),
        ("经济学人", "https://www.economist.com", "经济", False),
        ("华尔街见闻", "https://wallstreetcn.com/news/global", "经济", True),
        ("军事科技", "https://www.81.cn", "军事", True),
        ("中国海洋", "http://www.ncosm.org.cn", "行业", True),
    ]
    for name, url, category, active in rss_sources:
        session.add(RssSource(name=name, url=url, category=category, is_active=active))

    # ── 5. 知识库（4个内置） ──
    kb_data = [
        ("党建知识库", "包含党章、党史、党建理论、组织建设等核心资料", "党建"),
        ("船舶工程知识库", "包含船舶设计、制造工艺、海洋工程等技术文档", "技术"),
        ("教学资源库", "包含培训课程、课件模板、教学案例等教育资源", "教学"),
        ("政策法规库", "包含国家政策、行业法规、标准规范等文件", "政策"),
    ]
    for name, desc, category in kb_data:
        session.add(KnowledgeBase(name=name, description=desc, category=category))

    # ── 6. 科研选题（8个内置） ──
    research_data = [
        ("国有企业数字化转型路径研究", "数字经济", 92, 85, 78, 88, "研究国有企业在数字经济背景下的转型策略与实施路径"),
        ("船舶智能制造关键技术突破", "智能制造", 95, 90, 72, 91, "围绕船舶工业的智能化升级，研究关键技术的突破方向"),
        ("新时代党建工作创新实践", "党建", 88, 82, 95, 90, "探索基层党组织在新时代背景下的创新工作方法"),
        ("海洋强国战略下的国防科技发展", "国防", 90, 88, 75, 85, "分析海洋强国战略对国防科技的需求与挑战"),
        ("双碳目标下的绿色船舶技术", "绿色能源", 94, 92, 70, 87, "研究低碳、零碳船舶技术的发展路径"),
        ("人工智能在教育培训中的应用", "AI教育", 86, 80, 88, 89, "探索AI技术在干部教育培训中的深度应用"),
        ("产业链安全与自主可控研究", "产业安全", 91, 87, 76, 86, "分析关键产业链的安全风险与自主可控策略"),
        ("大国重器背后的技术创新体系", "创新管理", 93, 89, 74, 84, "研究重大技术装备的创新体系与管理机制"),
    ]
    for title, field, academic, innovation, feasibility, practice, desc in research_data:
        session.add(ResearchTopic(
            title=title, field=field, academic_value=academic,
            innovation_score=innovation, feasibility=feasibility,
            practice_value=practice, description=desc
        ))

    await session.commit()
    print("✅ Seed complete: 1 admin + 3 users + 14 skills + 20 RSS + 4 KB + 8 research topics")
