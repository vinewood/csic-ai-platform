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
