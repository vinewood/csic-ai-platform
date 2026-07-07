#!/bin/bash
# ==========================================
# 中船党校 AI 平台 - 一键部署脚本
# 适用于阿里云 ECS / 任意 Linux 服务器
# ==========================================

set -e

echo "======================================"
echo "  中船党校 AI 平台 一键部署脚本"
echo "======================================"

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "[1/5] 安装 Docker..."
    curl -fsSL https://get.docker.com | bash
fi

# 2. 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[2/5] 安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 3. 创建目录结构
echo "[3/5] 准备项目目录..."
mkdir -p data uploads www

# 4. 启动所有服务
echo "[4/5] 启动 Docker 服务..."
docker-compose up -d --build

# 5. 健康检查
echo "[5/5] 健康检查..."
sleep 10
curl -s http://localhost:8000/api/health && echo "" && echo "✅ 部署成功！" || echo "❌ 部署可能有问题，请检查 docker-compose logs"

echo ""
echo "======================================"
echo "  访问地址"
echo "  前端: http://localhost"
echo "  API:  http://localhost:8000/api"
echo "  文档: http://localhost:8000/docs"
echo "  默认账号: admin / dh24681357"
echo "======================================"
