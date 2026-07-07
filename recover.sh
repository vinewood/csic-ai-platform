#!/bin/bash
# 中船党校 — 一键恢复脚本 v3（含 Node.js + RSSHub）
set -e
echo "=== $(date) 中船党校 ECS 一键恢复 v3 ==="

# 1. 安装 Node.js（如缺失）
if ! command -v node &>/dev/null; then
    apt-get update -qq && apt-get install -y nodejs npm -qq || snap install node --classic
fi

# 2. RSSHub 依赖安装（如缺失）
if [ -d /opt/RSSHub ] && [ ! -d /opt/RSSHub/node_modules/.package-lock.json ]; then
    cd /opt/RSSHub && npm config set registry https://registry.npmmirror.com && npm install --production &
fi

# 3. 修复 admin 密码
source /www/wwwroot/csic.thinkalike.com.cn/backend/venv/bin/activate
cd /www/wwwroot/csic.thinkalike.com.cn/backend
python3 -c "
import asyncio, bcrypt
from app.database import async_session
from app import models
from sqlalchemy import select
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(b'***REMOVED-PASSWORD***', salt).decode()
async def fix():
    async with async_session() as s:
        u = await s.execute(select(models.User).where(models.User.username=='admin'))
        user = u.scalar_one_or_none()
        if user:
            user.hashed_password = hashed; user.role = 'admin'
            await s.commit()
            print('Password+role fixed')
asyncio.run(fix())
"

# 4. 重启后端
systemctl restart csic-backend 2>/dev/null || true
sleep 4

# 5. 验证
echo "=== Verification ==="
curl -s http://127.0.0.1:8000/api/health
echo ""
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"***REMOVED-PASSWORD***"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token','FAIL')[:20])" 2>/dev/null)
echo "Login: ${TOKEN}..."
curl -s http://127.0.0.1:8000/api/admin/integrations -H "Authorization: Bearer $TOKEN" | head -1
echo ""
echo "=== $(date) Recovery complete ==="
