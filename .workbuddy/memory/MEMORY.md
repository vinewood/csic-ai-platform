# CSIC AI Platform — 长期项目记忆

## 项目铁律
- **零国外CDN**：禁止 unpkg/jsdelivr/cdnjs/cdn.tailwindcss.com
- **CSS非阻塞**：所有外部CSS用 media="print" + onload
- **图片必须缓存**：服务端 Cache-Control: immutable
- **JSX预编译**：不用浏览器端Babel，用 scripts/compile.js
- **图标用RemixIcon**：不用 ant-design-icons
- **静态文件长期缓存**：/static/lib/ + /static/js/pages/ 返回 immutable

## 关键技能
- `.workbuddy/skills/csic-platform-pitfalls/` — 完整踩坑记录与铁律
- 每次新建对话时自动加载此技能

## 架构决策
- 后端: FastAPI + Jinja2 + 零npm前端
- 脚本加载: 动态script加载器 (async=false) 确保顺序
- 页面脚本: 预编译JS + page_script 变量模式
- 超时保护: 15秒替换splash显示错误

## 2026-07-07 重要变更

### 技术栈更新
- **前端重构为 Vue 3 + Element Plus + Vite 8**（已替代 Jinja2 + Alpine.js）
- **代码已推送 GitHub**: https://github.com/vinewood/csic-ai-platform
- **ECS 生产环境**: 39.96.86.119 → 4GB RAM
- **部署方式**: systemd + Docker（非 Docker Compose 全容器方式）

### 集成开源项目
- **Dify**: 5 容器（api/worker/web/postgres/redis），端口 5001/3000
- **gpt_academic**: 已上传到 /opt/gpt_academic，research.py 调用
- **RSSHub**: 已上传到 /opt/RSSHub，rss_service.py 调用
- **DeepSeek API**: Key 已配，实测通过

### 生产环境域名
- http://csic.thinkalike.com.cn/（Nginx 反代 127.0.0.1:8000）
- 开机自启: systemd `csic-backend.service`

### 关键修复
- `Chat.vue` skills.value.find 修复技能点击带入 bug
- `api.js` port 检测: 5173→localhost:8000, 生产→同域
- `dify_kb.py` 全能力集成（对话/知识库/文档解析/视频分析/同步）
