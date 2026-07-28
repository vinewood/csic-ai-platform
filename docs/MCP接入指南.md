# MCP 接入指南 — 中船党校 AI 平台

> 版本：v3.3.0 · 更新：2026-07-28
> 协议：Model Context Protocol · Streamable HTTP 传输（protocolVersion `2025-03-26`）

## 一、端点与认证

```
POST https://csic.thinkalike.com.cn/mcp/
Authorization: Bearer <令牌>
Content-Type: application/json
Accept: application/json, text/event-stream
```

令牌二选一：

1. **平台 JWT** — 调用 `/api/auth/login` 获取（会过期，适合短期调试）
2. **MCP 静态令牌** — 供 hibuddy 等系统长期对接使用，格式 `mcp_...`，
   由管理员在服务器 `api_configs` 表的 `mcp` 记录中维护（铁律：令牌只存服务器与本地，不进 Git）

无令牌或令牌错误返回 `401`（JSON-RPC error `-32001`）。

## 二、客户端配置示例

支持 Streamable HTTP 的 MCP 客户端（如 Claude Code / Cursor / 自研 Agent）：

```json
{
  "mcpServers": {
    "csic-ai-platform": {
      "type": "http",
      "url": "https://csic.thinkalike.com.cn/mcp/",
      "headers": {
        "Authorization": "Bearer <MCP 静态令牌>"
      }
    }
  }
}
```

## 三、握手流程（标准 MCP）

```bash
# 1) initialize（响应头 mcp-session-id 为会话 ID，后续请求必须携带）
curl -D - -X POST https://csic.thinkalike.com.cn/mcp/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"hibuddy","version":"1.0"}}}'

# 2) 通知初始化完成
curl -X POST https://csic.thinkalike.com.cn/mcp/ \
  -H "Authorization: Bearer $TOKEN" -H "mcp-session-id: $SID" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# 3) 调用工具
curl -X POST https://csic.thinkalike.com.cn/mcp/ \
  -H "Authorization: Bearer $TOKEN" -H "mcp-session-id: $SID" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"csic_knowledge_search","arguments":{"query":"党校职责","top_k":3}}}'
```

> 注意：请求体必须是 **UTF-8** JSON；Windows 下用 curl 行内中文会被终端转成 GBK，
> 请把 JSON 写入 UTF-8 文件后用 `--data-binary @file` 发送。

## 四、工具清单

| 工具 | 参数 | 说明 |
|---|---|---|
| `csic_chat` | `query`（必填）、`model` | 与平台 AI 对话。model：`deepseek`（默认）/ `qwen-plus` / `qwen-max` / `glm-4` / `kimi` / `minimax` |
| `csic_knowledge_search` | `query`（必填）、`top_k` | 检索党校知识库语料（《党校工作条例》等），返回片段与来源，top_k ≤ 10 |
| `csic_academic_search` | `query`（必填） | OpenAlex 学术检索，返回前 5 篇论文（标题/年份/被引/链接） |
| `csic_daily_news` | `category`、`date` | 每日资讯（RSS 聚合 + AI 摘要），date 格式 `YYYY-MM-DD`，默认最新 15 条 |
| `csic_list_skills` | 无 | 列出平台 AI 技能（名称/分类/描述） |

返回均为标准 MCP `content: [{type:"text", text:"..."}]`。

## 五、hibuddy 对接要点

1. 用上方客户端配置接入，或按第三节手工握手
2. 长期对接务必使用 **MCP 静态令牌**（JWT 会过期）
3. 会话为 Stateful：`mcp-session-id` 在 initialize 响应头中返回，丢失需重新 initialize
4. 超时建议 60s 以上（`csic_chat` 依赖大模型生成）
