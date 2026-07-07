"""
中船党校 AI 平台 —— 数据库完整设计
数据库: SQLite (文件: data/csic.db)
日期: 2026-07-06
"""

# ============================================================
# 1. 用户与认证
# ============================================================

# users — 用户表
# 对应前端: Landing.vue 登录, Admin.vue 用户管理
# API: POST /api/auth/login, GET/POST/DELETE /api/users
# 字段:
#   id              INTEGER PRIMARY KEY   — 主键
#   username        VARCHAR(64) UNIQUE     — 用户名 (admin)
#   email           VARCHAR(128)           — 邮箱
#   hashed_password VARCHAR(256)           — bcrypt 哈希密码
#   is_active       BOOLEAN DEFAULT 1      — 是否激活
#   role            VARCHAR(32) DEFAULT 'user' — 角色 (admin/user)
#   created_at      DATETIME               — 创建时间

# ============================================================
# 2. 对话与消息
# ============================================================

# conversations — 对话表
# 对应前端: Chat.vue 左栏历史列表、新建/切换/删除
# API: GET/POST/DELETE /api/chat/conversations
# 字段:
#   id              INTEGER PRIMARY KEY
#   title           VARCHAR(256) DEFAULT '新对话'
#   user_id         INTEGER FK→users      — 所属用户
#   model           VARCHAR(64)            — 使用的模型
#   created_at      DATETIME
#   updated_at      DATETIME

# messages — 消息表
# 对应前端: Chat.vue 消息显示区
# API: 通过 /api/chat/stream SSE 写入
# 字段:
#   id              INTEGER PRIMARY KEY
#   conversation_id INTEGER FK→conversations
#   role            VARCHAR(16)            — user / assistant
#   content         TEXT                   — 消息内容
#   model           VARCHAR(64)            — 响应模型
#   created_at      DATETIME

# ============================================================
# 3. 知识库 (RAG)
# ============================================================

# knowledge_bases — 知识库表
# 对应前端: Knowledge.vue 列表/新建/编辑/删除
# API: GET/POST/PUT/DELETE /api/knowledge
# 字段:
#   id              INTEGER PRIMARY KEY
#   name            VARCHAR(128)           — 知识库名称
#   description     TEXT                   — 描述
#   type            VARCHAR(32)            — 类型 (教学/科研/政策)
#   created_at      DATETIME
#   updated_at      DATETIME

# knowledge_docs — 知识库文档表
# 对应前端: Knowledge.vue 上传/查看/编辑/删除文档
# API: GET/POST/DELETE /api/knowledge/{kb_id}/docs
# 字段:
#   id              INTEGER PRIMARY KEY
#   kb_id           INTEGER FK→knowledge_bases
#   title           VARCHAR(256)           — 文档标题
#   filename        VARCHAR(256)           — 原始文件名
#   filepath        VARCHAR(512)           — 服务器存储路径
#   content         TEXT                   — 文本内容(提取后)
#   file_size       INTEGER                — 文件大小
#   created_at      DATETIME

# ============================================================
# 4. 技能中心
# ============================================================

# skills — 技能表
# 对应前端: Skills.vue 列表/收藏/新建
# API: GET/POST/PUT/DELETE /api/skills
# 字段:
#   id              INTEGER PRIMARY KEY
#   name            VARCHAR(128)           — 技能名称
#   description     TEXT                   — 功能描述
#   category        VARCHAR(32)            — 分类 (科研/教学/新闻/工具)
#   prompt          TEXT                   — 系统提示词
#   icon            VARCHAR(32)            — 图标名
#   color           VARCHAR(16)            — 颜色
#   rating          FLOAT DEFAULT 5.0      — 评分
#   favorited       BOOLEAN DEFAULT 0      — 是否收藏
#   is_preset       BOOLEAN DEFAULT 0      — 是否预置
#   user_id         INTEGER FK→users       — 创建者(自建技能)
#   created_at      DATETIME

# ============================================================
# 5. 项目空间 (科研)
# ============================================================

# projects — 项目表
# 对应前端: Research.vue 项目空间
# API: GET/POST/PUT/DELETE /api/projects
# 字段:
#   id              INTEGER PRIMARY KEY
#   name            VARCHAR(256)           — 项目名称
#   description     TEXT                   — 描述
#   status          VARCHAR(32)            — 状态 (进行中/已完成/规划中)
#   progress        INTEGER DEFAULT 0      — 进度 0-100
#   members_count   INTEGER DEFAULT 1      — 成员数
#   papers_count    INTEGER DEFAULT 0      — 论文数
#   color           VARCHAR(16)            — 卡片颜色
#   user_id         INTEGER FK→users
#   created_at      DATETIME
#   updated_at      DATETIME

# ============================================================
# 6. 选题与测评 (科研)
# ============================================================

# research_topics — 选题表
# 对应前端: Research.vue 智能选题/选题测评
# API: POST /api/research/generate, POST /api/research/evaluate
# 字段:
#   id              INTEGER PRIMARY KEY
#   title           VARCHAR(512)           — 选题标题
#   description     TEXT                   — 选题描述
#   field           VARCHAR(64)            — 研究领域
#   feasibility     INTEGER                — 可行性评分 0-100
#   innovation      INTEGER                — 创新性评分 0-100
#   academic_value  INTEGER                — 学术价值评分 0-100
#   practical_value INTEGER                — 实践意义评分 0-100
#   advice          TEXT                   — 综合建议
#   user_id         INTEGER FK→users
#   created_at      DATETIME

# ============================================================
# 7. 教学课题 (教学工作台)
# ============================================================

# teaching_topics — 教学课题表
# 对应前端: Teaching.vue 课题选题/内容创作
# API: POST /api/teaching/generate, POST /api/teaching/content
# 字段:
#   id              INTEGER PRIMARY KEY
#   title           VARCHAR(512)           — 课题标题
#   description     TEXT                   — 描述
#   level           VARCHAR(32)            — 深度 (基础/标准/深入)
#   hours           INTEGER                — 课时
#   audience        VARCHAR(128)           — 适用对象
#   content_outline TEXT                   — 课件大纲
#   lecture_script  TEXT                   — 逐页讲稿
#   ppt_outline     TEXT                   — PPT提纲
#   user_id         INTEGER FK→users
#   created_at      DATETIME

# ============================================================
# 8. 视频分析
# ============================================================

# video_tasks — 视频分析任务表
# 对应前端: Video.vue 上传/分析/结果
# API: POST /api/video/upload, GET /api/video/{id}
# 字段:
#   id              INTEGER PRIMARY KEY
#   title           VARCHAR(256)           — 视频标题
#   filename        VARCHAR(256)           — 文件名
#   filepath        VARCHAR(512)           — 存储路径
#   status          VARCHAR(32)            — 状态 (pending/processing/done/failed)
#   transcript      TEXT                   — 转录文本
#   summary         TEXT                   — AI摘要
#   flashcards      TEXT(JSON)             — 知识闪卡 JSON
#   duration        INTEGER                — 时长(秒)
#   file_size       INTEGER                — 文件大小
#   user_id         INTEGER FK→users
#   created_at      DATETIME
#   updated_at      DATETIME

# ============================================================
# 9. 新闻资讯 (RSS)
# ============================================================

# rss_sources — RSS源表
# 对应前端: Admin.vue RSS管理
# API: GET/POST/PUT/DELETE /api/rss/sources
# 字段:
#   id              INTEGER PRIMARY KEY
#   name            VARCHAR(128)
#   url             VARCHAR(512)           — RSS链接
#   category        VARCHAR(32)            — 分类
#   ai_enabled      BOOLEAN DEFAULT 1      — AI摘要开关
#   active          BOOLEAN DEFAULT 1
#   created_at      DATETIME

# news_articles — 文章表
# 对应前端: News.vue 列表/阅读
# API: GET /api/rss/articles, POST /api/rss/fetch
# 字段:
#   id              INTEGER PRIMARY KEY
#   source_id       INTEGER FK→rss_sources
#   title           VARCHAR(512)
#   url             VARCHAR(512)
#   summary         TEXT
#   ai_summary      TEXT
#   category        VARCHAR(32)
#   published       DATETIME
#   created_at      DATETIME

# ============================================================
# 10. 系统配置
# ============================================================

# api_configs — API配置表
# 对应前端: Admin.vue API配置
# API: GET/PUT /api/config/{provider}
# 字段:
#   id              INTEGER PRIMARY KEY
#   provider        VARCHAR(64) UNIQUE     — 服务商名
#   config_json     JSON                   — 完整配置
#   updated_at      DATETIME

# email_config — 邮箱配置表
# 对应前端: Admin.vue 邮箱配置
# API: GET/PUT /api/email/config
# 字段:
#   id              INTEGER PRIMARY KEY
#   smtp_host       VARCHAR(256)
#   smtp_port       INTEGER DEFAULT 465
#   smtp_user       VARCHAR(256)
#   smtp_pass       VARCHAR(256)
#   from_addr       VARCHAR(256)
#   to_addr         VARCHAR(256)
#   send_time       VARCHAR(16) DEFAULT '08:00'
#   auto_send       BOOLEAN DEFAULT 0

# ============================================================
# 11. 灵感与内容 (教学工作台)
# ============================================================

# inspirations — 灵感记录表
# 对应前端: Teaching.vue 灵感激发
# API: POST /api/teaching/inspire
# 字段:
#   id              INTEGER PRIMARY KEY
#   topic_id        INTEGER FK→teaching_topics
#   type            VARCHAR(32)            — 类型 (case/interactive/activity/discussion)
#   title           VARCHAR(256)
#   detail          TEXT
#   adopted         BOOLEAN DEFAULT 0
#   created_at      DATETIME
