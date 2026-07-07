# 中船党校 AI 平台 — 配置手册 v2.1
# 最后更新: 2026-07-07
# 此文件包含项目所有账号/密码/API Key/部署信息，妥善保管

# ============================================================
# 一、服务器信息
# ============================================================
ECS_SERVER=39.96.86.119
ECS_SSH_KEY=~/.ssh/baota_ecs_key
ECS_USER=root
ECS_SSH=ssh -i ~/.ssh/baota_ecs_key root@39.96.86.119
DOMAIN=csic.thinkalike.com.cn
HTTPS=https://csic.thinkalike.com.cn
RAM=4GB
OS=Ubuntu 26.04

# ============================================================
# 二、默认密码（全站统一）
# ============================================================
DEFAULT_PASSWORD=***REMOVED-PASSWORD***

# 管理员账号
ADMIN_USER=admin
ADMIN_EMAIL=admin@csic.cn
ADMIN_PASSWORD=***REMOVED-PASSWORD***

# 普通用户
USER_LIST=lecturer01, researcher01, editor01
USER_PASSWORD=***REMOVED-PASSWORD***

# ============================================================
# 三、数据库密码
# ============================================================
SQLITE_DB=backend/data/csic.db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=***REMOVED-PASSWORD***
POSTGRES_DB=dify

# ============================================================
# 四、Dify 平台
# ============================================================
DIFY_URL=http://127.0.0.1:5001
DIFY_WEB=http://127.0.0.1:3000
DIFY_ADMIN=admin@csic.cn
DIFY_PASSWORD=***REMOVED-PASSWORD***
DIFY_API_KEY=***REMOVED-DIFY-KEY***

# ============================================================
# 五、AI 模型 API Keys
# ============================================================
DEEPSEEK_API_KEY=***REMOVED-DEEPSEEK-KEY***
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/chat/completions

# 阿里云百炼（千问/ASR）
DASHSCOPE_API_KEY=  # 待配置
QWEN_MODEL=qwen-max
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions

# 智谱 GLM
ZHIPU_API_KEY=  # 待配置
ZHIPU_MODEL=glm-4

# Kimi/Moonshot
MOONSHOT_API_KEY=  # 待配置
MOONSHOT_MODEL=moonshot-v1-128k

# MiniMax
MINIMAX_API_KEY=  # 待配置

# 豆包/字节
DOUBAO_API_KEY=  # 待配置

# ============================================================
# 六、第三方学术 API
# ============================================================
AMINER_API_KEY=  # 待配置 (https://www.aminer.cn)
VIP_API_KEY=  # 待配置 (维普 https://www.cqvip.com)

# ============================================================
# 七、项目路径
# ============================================================
LOCAL_ROOT=D:\vinewood@163.com\Desktop\Work\csic\csic-ai-platform
LOCAL_BACKEND=D:\vinewood@163.com\Desktop\Work\csic\csic-ai-platform\backend
LOCAL_FRONTEND=D:\vinewood@163.com\Desktop\Work\csic\csic-ai-platform\frontend
LOCAL_WWW=D:\vinewood@163.com\Desktop\Work\csic\csic-ai-platform\www

SERVER_ROOT=/www/wwwroot/csic.thinkalike.com.cn
SERVER_BACKEND=/www/wwwroot/csic.thinkalike.com.cn/backend
SERVER_WWW=/www/wwwroot/csic.thinkalike.com.cn/www
SERVER_SYSTEMD=/etc/systemd/system/csic-backend.service

# ============================================================
# 八、集成开源项目
# ============================================================
DIFY_COMPOSE=/opt/dify/docker/docker-compose.yml
RSSHUB_DIR=/opt/RSSHub
RSSHUB_PORT=1200
GPT_ACADEMIC_DIR=/opt/gpt_academic
GPT_ACADEMIC_PORT=8765
GPT_ACADEMIC_PYTHON=/usr/bin/python3.11

# ============================================================
# 九、GitHub
# ============================================================
GITHUB_REPO=https://github.com/vinewood/csic-ai-platform
GITHUB_BRANCH=main

# ============================================================
# 十、部署命令速查
# ============================================================

# 本地运行
cd csic-ai-platform/backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 前端构建
cd csic-ai-platform/frontend
npx vite build && cp -r dist/* ../www/

# 上传到服务器
scp -r csic-ai-platform/www root@39.96.86.119:/www/wwwroot/csic.thinkalike.com.cn/
scp csic-ai-platform/backend/app/*.py root@39.96.86.119:/www/wwwroot/csic.thinkalike.com.cn/backend/app/

# 服务器重启
ssh root@39.96.86.119 "systemctl restart csic-backend"

# 服务器一键恢复（密码+DB+后端）
ssh root@39.96.86.119 "bash /root/recover.sh"

# 查看日志
ssh root@39.96.86.119 "journalctl -u csic-backend -f"
ssh root@39.96.86.119 "docker logs dify-api --tail 50"

# ============================================================
# 十一、SSL 证书
# ============================================================
SSL_PROVIDER=Let's Encrypt (certbot)
SSL_AUTO_RENEW=certbot.timer (每日 00:12 CST)
SSL_DOMAIN=csic.thinkalike.com.cn
SSL_PATH=/etc/letsencrypt/live/csic.thinkalike.com.cn/
