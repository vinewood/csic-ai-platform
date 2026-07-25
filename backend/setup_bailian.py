import sqlite3, json, os, sys

# 铁律：任何 API Key 只允许存在本地/服务器，禁止硬编码进源码
# 用法：BAILIAN_KEY=sk-xxx python3 setup_bailian.py
BAILIAN_KEY = os.getenv("BAILIAN_KEY", "")
if not BAILIAN_KEY:
    print("错误：请先设置环境变量 BAILIAN_KEY（新 key 从阿里云百炼控制台获取）")
    sys.exit(1)

conn = sqlite3.connect('/www/wwwroot/csic.thinkalike.com.cn/data/csic.db')

# Bailian config
cfg = json.dumps({
    "key": BAILIAN_KEY,
    "endpoint": "https://ws-eg0sswldqhhc6qko.cn-beijing.maas.aliyuncs.com/api/v1",
    "baseUrl": "https://ws-eg0sswldqhhc6qko.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
})
conn.execute('INSERT OR REPLACE INTO api_configs (provider, config_json) VALUES (?, ?)', ('dashscope', cfg))

# Clear old models and insert new
conn.execute('DELETE FROM api_models')
models = [
    ('qwen-turbo', 'dashscope', 'qwen-turbo', 1, '通义千问 Turbo · 快速响应'),
    ('qwen-plus', 'dashscope', 'qwen-plus', 1, '通义千问 Plus · 均衡性能'),
    ('qwen-max', 'dashscope', 'qwen-max', 1, '通义千问 Max · 最强推理'),
    ('qwen-max-longcontext', 'dashscope', 'qwen-max-longcontext', 1, 'Qwen Max · 超长上下文'),
    ('qwen-coder-plus', 'dashscope', 'qwen-coder-plus', 1, '通义千问 Coder Plus · 代码专家'),
    ('deepseek', 'deepseek', 'deepseek-chat', 1, 'DeepSeek · 高性价比独立调用'),
]
for name, provider, api_name, active, desc in models:
    conn.execute('INSERT OR REPLACE INTO api_models (name, provider, api_name, is_active, description) VALUES (?,?,?,?,?)',
                 (name, provider, api_name, active, desc))
conn.commit()

for r in conn.execute('SELECT name, provider, api_name FROM api_models WHERE is_active=1').fetchall():
    print(r[0], r[1], r[2])
conn.close()
print('DONE')
