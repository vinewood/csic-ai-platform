"""开发调试脚本：查看 Dify 数据集（仅服务器本地使用）

密码从环境变量 DIFY_DB_PASSWORD 读取，源码严禁硬编码（铁律）。
用法：ssh 到服务器后 `DIFY_DB_PASSWORD=xxx python3 check_dify_db.py`
"""
import asyncio
import os
import sys

import asyncpg


async def test():
    password = os.getenv("DIFY_DB_PASSWORD", "")
    if not password:
        print("请先设置环境变量 DIFY_DB_PASSWORD（见本地 CONFIG.md）")
        sys.exit(1)
    conn = await asyncpg.connect(host='127.0.0.1', port=5432, user='postgres', password=password, database='dify')
    rows = await conn.fetch("SELECT id, name, document_count FROM datasets ORDER BY created_at DESC")
    print(f"Datasets: {len(rows)}")
    for r in rows:
        print(f"  {r['name']} (docs={r['document_count']}) - {r['id']}")
    await conn.close()


asyncio.run(test())
