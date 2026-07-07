# 中船党校 AI 智能业务平台

> CSIC Party School AI Platform  
> 集科研辅助 + 教学培训 + 信息聚合于一体的党校 AI 智能工作平台

---

## 快速开始

### 一键部署（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url> csic-ai-platform
cd csic-ai-platform

# 2. 启动所有服务
docker compose up -d

# 3. 访问
# 前端: http://localhost
# 后端API: http://localhost:8000/api
# API文档: http://localhost:8000/docs
```

### 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin  | dh24681357 | 管理员 |

---

## 系统架构

```
┌──────────────────────────────────────────────────┐
│                   Nginx (:80)                     │
│           前端静态文件 + API 反向代理               │
├──────────────────────────────────────────────────┤
│   ┌───────────┐  ┌──────────┐  ┌──────────────┐  │
│   │ Vue 3 SPA  │  │ FastAPI  │  │   Dify AI    │  │
│   │ (www/)     │  │ (:8000)  │  │   (:5001)    │  │
│   │ 9页面      │  │ SSE/CRUD │  │  LLM调度/RAG │  │
│   └───────────┘  └──────────┘  └──────────────┘  │
│                      │              │             │
│                 ┌────┴──────┐  ┌───┴───────┐      │
│                 │  SQLite   │  │PostgreSQL │      │
│                 │ (数据持久) │  │(Dify数据)  │      │
│                 └───────────┘  └───────────┘      │
├──────────────────────────────────────────────────┤
│               RSSHub (:1200)                      │
│              新闻源抓取                            │
└──────────────────────────────────────────────────┘
```

### 服务列表

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| nginx | nginx:alpine | 80/443 | 前端 + 反向代理 |
| backend | 自定义 | 8000 | FastAPI 后端 |
| dify | langgenius/dify | 5001 | AI 引擎 |
| dify-db | postgres:15 | - | Dify 数据库 |
| dify-redis | redis:7 | - | Dify 缓存 |
| rsshub | diygod/rsshub | 1200 | RSS 抓取 |

---

## 前端页面清单

| 路由 | 页面 | 功能 |
|------|------|------|
| `/` | 登录页 | 默认账号 admin/dh24681357 |
| `/workspace/chat` | AI 对话 | 单/多模型、技能、知识库、SSE流式 |
| `/workspace/skills` | 技能中心 | 14 预置技能 + 收藏 + 新建 |
| `/workspace/teaching` | 教学工作台 | 选题/灵感/内容/数据包 |
| `/workspace/research` | 科研工作台 | 选题/测评/文献/项目 |
| `/workspace/video` | 视频分析 | 转录/摘要/闪卡/思维导图 |
| `/workspace/news` | 每日资讯 | RSS 日报 + AI 摘要 |
| `/workspace/knowledge` | 知识库 | 增删改查 |
| `/workspace/admin` | 系统管理 | 用户/模型/API/邮箱/RSS |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3.5 + Vite 8 + Element Plus 2.14 + Vue Router 5 |
| **后端** | Python 3.12 + FastAPI + SQLAlchemy 2.0 + SQLite |
| **AI引擎** | Dify (LLMOps 平台) |
| **数据库** | SQLite (业务) + PostgreSQL (Dify) |
| **缓存** | Redis 7 |
| **RSS** | RSSHub |
| **部署** | Docker Compose + Nginx |

---

## 后端 API 概览

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 登录 |
| `/api/auth/register` | POST | 注册 |
| `/api/auth/me` | GET | 当前用户 |
| `/api/chat/stream` | POST | SSE 流式对话 |
| `/api/chat/conversations` | GET | 对话列表 |
| `/api/chat/conversations/{id}` | DELETE | 删除对话 |
| `/api/chat/models` | GET | 模型列表 |
| `/api/users` | GET/POST/DELETE | 用户 CRUD |
| `/api/rss/sources` | GET/POST/PUT/DELETE | RSS 源管理 |
| `/api/rss/fetch` | POST | 手动抓取 RSS |
| `/api/rss/articles` | GET | 文章列表 |
| `/api/email/config` | GET/PUT | 邮箱配置 |
| `/api/email/test` | POST | 测试邮件 |
| `/api/files/upload` | POST | 文件上传 |
| `/api/academic/aminer/search` | POST | AMiner 文献搜索 |
| `/api/academic/vip/search` | POST | 维普文献搜索 |
| `/api/config/{provider}` | GET/PUT | API 配置管理 |
| `/api/health` | GET | 健康检查 |

---

## 部署到阿里云 ECS

### 前置条件

- 阿里云 ECS（推荐 2C4G 或以上）
- 安装 Docker 和 Docker Compose
- 开放端口：80（HTTP）、443（HTTPS可选）

### 部署步骤

```bash
# 1. SSH 到服务器
ssh root@your-ecs-ip

# 2. 安装 Docker（如未安装）
curl -fsSL https://get.docker.com | bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 3. 上传项目
# 将整个 csic-ai-platform 目录上传到服务器
scp -r csic-ai-platform root@your-ecs-ip:/opt/

# 4. 启动
cd /opt/csic-ai-platform
docker compose up -d

# 5. 验证
curl http://localhost:8000/api/health
# 应返回: {"status":"ok","version":"2.0.0"}
```

### 使用 HTTPS（可选）

```bash
# 安装 certbot
apt install -y certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d your-domain.com

# 重启 Nginx
docker compose restart nginx
```

### 备份

```bash
# 备份数据库
docker exec csic-backend tar czf /tmp/backup.tar.gz /app/data
docker cp csic-backend:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
```

---

## 开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev

# 访问
# 前端: http://localhost:5173
# 后端: http://localhost:8000
```

---

## 密码说明

- 默认管理员密码：`dh24681357`
- Dify 管理员密码：`dh24681357`
- PostgreSQL 密码：`dh24681357`
- Redis 密码：`dh24681357`
- **生产环境请务必修改所有默认密码！**

---

## 许可证

本项目为内部使用，版权归中国船舶集团党校所有。
