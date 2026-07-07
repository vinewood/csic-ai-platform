---
name: csic-platform-pitfalls
description: 中船党校AI平台开发踩坑记录与铁律。涉及CDN策略、JSX编译、图标替换、加载优化、缓存配置、脚本加载顺序等关键决策。处理CSIC AI平台项目时需优先加载此skill。
agent_created: true
---

# CSIC AI Platform — 踩坑记录与铁律

## 铁律（必须遵守）

1. **国内 CDN 优先** — 所有公共库用 BootCDN（cdn.bootcdn.net，阿里云系）。本地文件做 fallback。严禁 unpkg/jsdelivr/cdnjs 等国外 CDN。
2. **加载顺序** — antd v6 依赖 `React → ReactDOM → dayjs`。必须按此顺序加载，否则 antd 初始化报 `Cannot read properties of undefined (reading 'extend')`。
3. **antd v6 不需要 dayjs 插件** — antd v6 的 UMD 只 require(react, react-dom, dayjs)，不需要 dayjs_plugin_*。antd v5 也不需要（那是 ant-design-vue 的依赖）。
4. **CSS 非阻塞加载** — 外部 CSS 用 `<link rel="stylesheet" media="print" onload="this.media='all'">`。
5. **图片/静态文件必须缓存** — 服务端设 `Cache-Control: public, max-age=31536000, immutable`。用户浏览器跨页面不重复加载。
6. **JSX 预编译** — 不用浏览器端 Babel。`scripts/compile.js` 将 JSX 编译为纯 JS。
7. **图标用 RemixIcon + 适配器** — `window.AntDesignIcons = { UserOutlined: ic('ri-user-line'), ... }`。同时设 `window.icons = ic`（antdx 需要）。
8. **antdx 需要 antdCssinjs 别名** — antdx 依赖 `window.antdCssinjs`（`@ant-design/cssinjs` 的 StyleProvider）。antd v6 已内置 StyleProvider，但 antdx 没直接引用。必须提供 `window.antdCssinjs = { StyleProvider: ... }`。
9. **mermaid 从 BootCDN 下载** — 国外 CDN（如 unpkg）下载的 mermaid 可能截断。必须从 BootCDN 下载。
10. **先看 skill/记忆再动手** — 遇到任何加载/编译/兼容性问题，优先查看 `.workbuddy/skills/csic-platform-pitfalls/SKILL.md` 和 `.workbuddy/memory/MEMORY.md`，避免重复踩坑。

## 踩坑记录

### 1. tailwind Play CDN
- **问题**: 加载了 `cdn.tailwindcss.com` 的Play CDN版本（407KB），包含完整PostCSS运行时，模板实际没用到任何Tailwind类。
- **解决**: 直接删除 `<script>` 引用。所有样式通过 `brand.css` 自定义类 + 内联style实现。

### 2. ant-design-icons 兼容性
- **问题**: `@ant-design/icons` 的本地文件导出 `window.icons`，但模板统一用 `AntDesignIcons` 全局。CDN v6.0.2与本地版不一致。
- **解决**: 用RemixIcon字体图标替代，通过适配器将 `AntDesignIcons.xxx` 映射到 `ri-xxx-line` CSS类。体积从881KB JS降至~300KB CSS。

### 3. Babel运行时3MB
- **问题**: `<script type="text/babel">` 需要下载3MB babel.min.js + 运行时编译JSX，严重拖慢加载（企业内网尤为明显）。
- **解决**: 用 `scripts/compile.js`（Node.js + 本地babel.min.js）将10个模板的JSX预编译为纯JS，存入 `static/js/pages/`。编译产物仅11-20KB/页。

### 4. CDN慢于本地
- **问题**: BootCDN从企业内网访问需7秒下载antd.min.js（950KB）。
- **解决**: 切换回本地 `/static/lib/` 文件 + 服务端 `Cache-Control: immutable`。本地页面跳转时缓存命中，秒开。

### 5. CSS阻塞渲染
- **问题**: antd.min.css（558KB）和remixicon.min.css从CDN/本地加载时，浏览器不显示任何内容。
- **解决**: `media="print" onload="this.media='all'"` 技巧让CSS非阻塞。

### 6. 脚本加载顺序
- **问题**: antd依赖React，ReactDOM依赖React。`async`/`defer` 不保证执行顺序。
- **解决**: 动态脚本加载器 + `s.async = false` 保证按序执行，同时不阻塞解析。

### 7. JSX编译后编辑困难
- **问题**: Babel将中文转为Unicode转义（如 `\u4E2D\u56FD`），sed/grep替换困难。
- **解决**: 用Python直接读写JS文件进行字符串替换。修改后需保持编译脚本可用。

### 8. 粒子效果丢失
- **问题**: `ocean-particles.js` 异步加载后，topbar的内联init脚本已运行完毕（`window.OceanParticles` 未定义）。
- **解决**: 在base.html的脚本加载链中，ocean-particles.js加载后立即调 `initTopbarParticles()`。

## 预编译工作流

```bash
# 修改模板JSX后重新编译（注意：当前JSX已不在模板中，需直接编辑 static/js/pages/*.js）
# 如需重新从JSX编译:
cd csic-ai-platform
cp templates/xxx.html  # 恢复携带有JSX的模板备份
# 编辑模板中的JSX
npx @babel/standalone scripts/compile.js
# 或直接编辑 static/js/pages/xxx.js（当前工作流）
python -c "
p = 'static/js/pages/xxx.js'
with open(p) as f: c = f.read()
c = c.replace('old', 'new')
with open(p, 'w') as f: f.write(c)
"
```

## 静态文件缓存配置

在 `main.py` 中加入:
```python
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith('/static/'):
            if '/lib/' in path or '/pages/' in path:
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            else:
                response.headers['Cache-Control'] = 'public, max-age=86400'
        return response

app.add_middleware(CacheControlMiddleware)
```

### 12. Element AI Vue 聊天组件库

`element-ai-vue@0.1.6` — Vue 3 原生 AI 聊天组件库，基于 Element Plus。

**组件**: Bubble（气泡）、BubbleList（滚动列表）、Sender（输入框）、Markdown、ThoughtChain、Thinking、FilesCard 等。

**全局构建**: `dist/index.full.min.js` (13MB)，导出 `window.ElementAiVue`，通过 `app.use(ElementAiVue)` 注册。CSS: `dist/index.css` (71KB)。**必须本地加载**（体积大，CDN不可接受）。

**关键 API**:
- `el-ai-bubble`: placement('start'|'end'), content, typing, typingOver, loading, isMarkdown, variant('filled'|'outlined'|'shadow'|'borderless'), shape('default'|'round'|'corner')
- `el-ai-bubble-list`: 自动滚动容器，ref 可调用 scrollToBottom()/scrollToTop()
- `el-ai-sender`: v-model(html), loading, placeholder, theme, @send(content)
