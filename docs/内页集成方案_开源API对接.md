# 中船党校 AI 平台 — 内页集成方案：开源工具 × API 对接 × UI-功能映射

> 核心问题：内页界面如何与开源工具的实际功能 + 参考网站 API 严格匹配？

---

## 一、整体集成架构

```
┌──────────────────────────────────────────────────────────────┐
│                    内页 UI（Jinja2 + Alpine.js）                │
│                                                              │
│  每个工作台页面的 Alpine.js 从后端 API 获取数据                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 教学页面  │  │ 科研页面  │  │ 新闻页面  │  │ 会话页面  │   │
│  │ x-data   │  │ x-data   │  │ x-data   │  │ x-data   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │          │
├───────┼──────────────┼──────────────┼──────────────┼──────────┤
│       │        FastAPI Backend（统一 API 层）                   │
│  ┌────┴──────────────┴──────────────┴──────────────┴────┐   │
│  │  /api/chat/stream    — SSE 流式对话（百炼 API）        │   │
│  │  /api/research/*     — 科研工具（gpt_academic 引擎）   │   │
│  │  /api/teaching/*     — 教学工具（自建 CRUD）           │   │
│  │  /api/news/*         — 新闻聚合（RSSHub+Miniflux）    │   │
│  │  /api/video/*        — 视频分析（转录引擎）            │   │
│  │  /api/skills/*       — 技能管理（MySQL CRUD）          │   │
│  │  /api/admin/*        — 系统管理（MySQL CRUD）          │   │
│  └────┬─────────────────────────────────────────────────┘   │
│       │                                                      │
├───────┼──────────────────────────────────────────────────────┤
│       │        集成层（Python 函数 / Docker 服务）              │
│  ┌────┴────────────┬──────────────┬──────────────────────┐  │
│  │ 开源工具引擎     │ 外部 API      │ 自建服务              │  │
│  │                 │              │                      │  │
│  │ gpt_academic    │ 阿里云百炼    │ 课程 CRUD (SQLAlchemy) │  │
│  │ AI-Video-Trans  │ AMiner API   │ 技能 CRUD (SQLAlchemy) │  │
│  │ RSSHub (Docker) │ 维普 API      │ 用户/权限 (SQLAlchemy) │  │
│  │ Miniflux (Docker)│ DeepSeek API │ 文件存储 (OSS/本地)   │  │
│  │                 │ 智谱 API      │                      │  │
│  │                 │ Moonshot API  │                      │  │
│  │                 │ MiniMax API   │                      │  │
│  │                 │ 豆包 API      │                      │  │
│  └─────────────────┴──────────────┴──────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、逐模块 UI ↔ 功能映射

### 模块一：AI 对话 (`/chat`)

**当前 UI 状态**：✅ 已实现（单模/多模切换、流式输出模拟）

**需要对接的实际能力**：

| UI 元素 | 数据来源 | 实现方式 |
|---------|---------|---------|
| 模型列表 (千问/智谱/Kimi/DeepSeek/MiniMax/豆包) | 数据库 `models` 表 | `GET /api/models` 返回可用模型列表 |
| 单模型对话 | 阿里云百炼 / 各模型直连 API | `POST /api/chat/single` → SSE 流式返回 |
| 多模型并行 (最多6个) | 并发调用多个 API | `POST /api/chat/multi` → 并发 SSE 汇总返回 |
| 对话历史 | 数据库 `conversations` / `messages` 表 | `GET /api/conversations` `POST /api/messages` |
| 技能绑定对话 | 从技能中心选择 Skill，预填 system prompt | URL 参数 `?skill=id` 传递 prompt |

**关键实现代码骨架（FastAPI）**：

```python
# app/routers/chat_router.py
@router.post("/api/chat/single")
async def chat_single(req: ChatRequest):
    """单模型对话 — SSE 流式"""
    return StreamingResponse(
        bailian_stream(req.model, req.messages),
        media_type="text/event-stream"
    )

@router.post("/api/chat/multi")
async def chat_multi(req: MultiChatRequest):
    """多模型并行 — 并发调用 + SSE 汇总"""
    async def generate():
        tasks = [bailian_stream(m, req.messages) for m in req.models]
        async for chunk in merge_streams(*tasks):
            yield f"data: {json.dumps(chunk)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

### 模块二：教学工作台 (`/workspace/teaching`)

**当前 UI 状态**：✅ 已实现（搜索+分类过滤+课程列表）

**参考网站**：aizke（搜索驱动界面）+ 妙塔AI（培训管理）

**需要对接的实际能力**：

| UI 元素 | 数据来源 | 实现方式 |
|---------|---------|---------|
| 课程列表 | 数据库 `courses` 表 | `GET /api/courses?search=xxx&type=xxx` |
| 课件管理 | 数据库 `slides` 表 + OSS 文件存储 | `GET/POST /api/slides` |
| 课程搜索 | MySQL LIKE / 全文检索 | 前端 Alpine.js `filter()` 绑定 API 查询 |
| 音视频转录 | AI-Video-Transcriber 引擎 | `POST /api/video/transcribe`（异步 Celery） |
| AI 课件生成 | 百炼 API + Jinja2 模板 | `POST /api/teaching/generate-slide` |
| 经验萃取 | 百炼 API (system prompt) | `POST /api/teaching/extract-experience` |

**课程表设计**：

```sql
CREATE TABLE courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),        -- 'course' / 'slide' / 'video' / 'case'
    slide_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

### 模块三：科研工作台 (`/workspace/research`)

**当前 UI 状态**：✅ 已实现（仪表盘+选题助手+文献检索+项目列表）

**参考网站**：AMiner + 维普

**需要对接的实际能力**：

| UI 元素 | 数据来源 | 实现方式 |
|---------|---------|---------|
| 选题分析 | gpt_academic 引擎 + 百炼 API | `POST /api/research/topic-analysis` → 返回选题列表 |
| 文献检索 | AMiner API（付费）或维普 API | `GET /api/research/literature?q=xxx` |
| 文献综述生成 | gpt_academic `ai_summarize` | `POST /api/research/literature-review` |
| 论文润色 | gpt_academic `ai_polish` | `POST /api/research/polish` |
| 论文翻译 | gpt_academic `ai_translate` | `POST /api/research/translate` |
| 论文校对 | gpt_academic `ai_proofread` | `POST /api/research/proofread` |
| 项目空间 | 数据库 `projects` 表 | `GET/POST/PUT /api/projects` |

**gpt_academic 集成关键**：

```python
# app/integrations/academic_tools.py
# 只导入核心函数，不启动 Gradio UI
import sys
sys.path.append('./vendor/gpt_academic')  # 子模块方式引入

from toolbox import get_conf
from crazy_functions.pdf_fns.parse_pdf import parse_pdf
from request_llms.bridge_all import predict_no_ui_long_connection

async def summarize_paper(text: str, model: str = "qwen-max") -> str:
    """调用 gpt_academic 的 AI 总结函数"""
    return await predict_no_ui_long_connection(
        inputs=text,
        llm_kwargs={"model": model},
        sys_prompt="请对以下论文内容进行专业学术总结..."
    )
```

---

### 模块四：信息导航台 (`/workspace/news`)

**当前 UI 状态**：✅ 已实现（RSS源管理+分类过滤+新闻列表+日报面板）

**需要对接的实际能力**：

| UI 元素 | 数据来源 | 实现方式 |
|---------|---------|---------|
| RSS 源管理 | 数据库 `rss_sources` 表 | `GET/POST/DELETE /api/rss-sources` |
| 新闻列表 | Miniflux API（Docker 内部） | `GET /api/news?category=xxx` |
| AI 摘要 | 百炼 API（qwen-turbo 降成本） | `POST /api/news/summarize`（批量异步） |
| 日报生成 | 百炼 API + Celery Beat | 每日定时生成，存入 `daily_briefs` 表 |
| RSSHub 路由 | RSSHub Docker 容器 | Nginx 反向代理 `rsshub:1200` |

**定时抓取流程**：

```python
# app/tasks/news_crawler.py
@celery_app.task
def fetch_all_news():
    """定时任务：从 RSSHub 拉取所有源的最新文章"""
    sources = db.query(RssSource).filter_by(is_active=True).all()
    for src in sources:
        feed = httpx.get(f"http://rsshub:1200/{src.route}").json()
        for item in feed.get("items", []):
            if not db.query(NewsArticle).filter_by(url=item["url"]).first():
                db.add(NewsArticle(source_id=src.id, title=item["title"], ...))
    db.commit()

@celery_app.task
def generate_daily_brief():
    """每日生成要点简报"""
    today_news = db.query(NewsArticle).filter(
        func.date(NewsArticle.fetched_at) == func.current_date()
    ).all()
    summary = bailian_summarize(today_news)  # AI 汇总
    db.add(DailyBrief(date=date.today(), content=summary))
    db.commit()
```

---

### 模块五：技能中心 (`/workspace/skills`)

**当前 UI 状态**：✅ 已实现（技能卡片网格+分类+搜索）

**参考网站**：青泥 AI 技能广场

**需要对接的实际能力**：

| UI 元素 | 数据来源 | 实现方式 |
|---------|---------|---------|
| 技能列表 | 数据库 `skills` 表 | `GET /api/skills?category=xxx` |
| 技能创建 | 数据库 CRUD | `POST /api/skills` |
| 使用技能 | 跳转 /chat 并注入 system prompt | `GET /chat?skill=id` → 预填 prompt |
| 技能评分/收藏 | `user_skills` 关联表 | `POST /api/skills/{id}/rate` |

**技能表设计**：

```sql
CREATE TABLE skills (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category ENUM('research','teaching','news','general'),
    system_prompt TEXT NOT NULL,       -- 核心：注入给 AI 的提示词
    recommended_model VARCHAR(50),
    temperature FLOAT DEFAULT 0.7,
    is_public BOOLEAN DEFAULT TRUE,
    creator_id INT,
    usage_count INT DEFAULT 0,
    rating DECIMAL(2,1),
    FOREIGN KEY (creator_id) REFERENCES users(id)
);
```

---

### 模块六：视频分析 (`/workspace/video`)

**当前 UI 状态**：✅ 已实现（上传+进度+四面板结果）

**参考网站**：dwsj.cn

**需要对接的实际能力**：

| UI 元素 | 数据来源 | 实现方式 |
|---------|---------|---------|
| 文件上传 | FastAPI UploadFile → OSS | `POST /api/video/upload` |
| 语音转录 | AI-Video-Transcriber 引擎（Whisper） | Celery 异步任务 → WebSocket 推送进度 |
| AI 摘要 | 百炼 API | 转录完成后自动调用 |
| 思维导图 | simple-mind-map（前端渲染） | 百炼返回结构化 JSON → 前端渲染 |
| 结构化笔记 | 百炼 API | `POST /api/video/notes` |

**异步处理流程**：

```python
# app/tasks/video_transcribe.py
@celery_app.task(bind=True)
def transcribe_video(self, file_path: str, user_id: int):
    """异步转录视频"""
    self.update_state(state="PROGRESS", meta={"progress": 10, "stage": "上传完成"})
    
    # Step 1: 语音转文字
    text = whisper_transcribe(file_path)  # 调用开源引擎
    self.update_state(state="PROGRESS", meta={"progress": 50, "stage": "转录完成"})
    
    # Step 2: AI 摘要
    summary = bailian_chat(f"请总结以下内容：{text[:8000]}")
    self.update_state(state="PROGRESS", meta={"progress": 75, "stage": "摘要完成"})
    
    # Step 3: 思维导图
    mindmap = bailian_chat(f"将以下内容转化为JSON树形结构：{text[:8000]}")
    
    return {"text": text, "summary": summary, "mindmap": mindmap}
```

---

## 三、每个开源工具的 UI 集成方式

| 开源工具 | 技术栈 | UI 来源 | 集成到内页的方式 |
|---------|--------|---------|----------------|
| **gpt_academic** | Python (Gradio UI) | ❌ 不取其 UI | 提取核心函数到 `integrations/academic_tools.py`，通过 REST API 调用 |
| **AI-Video-Transcriber** | Python + Vue | ❌ 不取其 UI | 提取转录引擎到 `integrations/video_tools.py`，Celery 异步 |
| **RSSHub** | Node.js (Koa) | ❌ 纯 API | Docker 部署，Nginx 反向代理，FastAPI 定时拉取 |
| **Miniflux** | Go | ❌ 不取其 UI | Docker 部署，FastAPI 通过其 REST API 获取数据 |
| **simple-mind-map** | 纯 JS 库 | ✅ npm CDN | 直接在 `<script>` 中引入，前端渲染 |
| **PlayEdu** | Java (SpringBoot) | ❌ 不部署 | 用 FastAPI + SQLAlchemy 自建简单课程/培训管理 CRUD |
| **OpenMAIC** | Python | ❌ 仅参考 | 参考其多智能体课堂设计理念，用百炼 Agent 实现 |
| **ChatALL** | Vue + Electron | ❌ 桌面端 | 多模型并行功能在自研聊天模块实现 |
| **LobeChat** | Next.js/React | ❌ 不使用 | 自建聊天组件（chat-core.js + SSE） |

---

## 四、API 对接清单

| API | 调用方 | 用途 | 计费模式 |
|-----|--------|------|---------|
| **阿里云百炼** | 后端 FastAPI | 千问 Max 对话/RAG 知识库/插件 | 按 Token |
| **DeepSeek API** | 后端 FastAPI | DeepSeek V3 对话 | 按 Token |
| **智谱 API** | 后端 FastAPI | GLM-4 对话 | 按 Token |
| **Moonshot API** | 后端 FastAPI | Kimi 对话（超长上下文） | 按 Token |
| **MiniMax API** | 后端 FastAPI | abab6.5 对话（创意写作） | 按 Token |
| **豆包 API** | 后端 FastAPI | 豆包 Pro 对话 | 按 Token |
| **AMiner API** | 后端 FastAPI | 学术文献检索/学者画像 | 按次/包年 |
| **维普 API** | 后端 FastAPI | 中文文献检索 | 按次/包年 |
| **RSSHub** | Docker 内部 | RSS 源生成（1000+ 适配器） | 免费 |
| **Miniflux** | Docker 内部 | RSS 订阅管理 + 文章存储 | 免费 |

---

## 五、数据库表完整清单

```
users               — 用户（40人，多租户 user_id 隔离）
user_preferences    — 用户偏好（默认工作台、卡片排序）
conversations       — 对话会话
messages            — 对话消息（支持多模型标记）
projects            — 科研/教学项目
courses             — 课程
slides              — 课件
rss_sources         — RSS 新闻源
news_articles       — 新闻文章（AI 摘要）
daily_briefs        — 每日简报
skills              — 技能（公开+私有）
user_skills         — 用户技能收藏/自定义
video_tasks         — 视频转录任务
api_usage_logs      — API 用量日志
```

---

## 六、下一步行动

1. **建立 FastAPI 后端 API 路由骨架** — 所有 `/api/*` 端点
2. **数据库建模 + Alembic 迁移** — 按上面表清单创建
3. **百炼 SDK 集成** — 统一模型调用抽象层
4. **gpt_academic 引擎提取** — 安装依赖 + 包装 API
5. **RSSHub + Miniflux Docker 部署** — docker-compose 就绪
6. **异步任务（Celery）** — 视频转录 + 新闻抓取
7. **前端 AJAX 对接** — 替换模拟数据为真实 API 调用

---

*文档版本：v1.0 | 编制日期：2026-07-04*
