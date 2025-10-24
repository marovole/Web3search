#!/bin/bash

# ================================
# 开发环境启动脚本
# 启动所有必需的服务
# ================================

set -e

echo "🚀 启动 Web3 Search 开发环境..."

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker未运行，请先启动Docker"
    exit 1
fi

# 启动Docker服务（PostgreSQL + Redis）
echo "📦 启动Docker服务 (PostgreSQL + Redis)..."
docker-compose up -d postgres redis

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
sleep 5

# 检查.env文件
if [ ! -f "backend/.env" ]; then
    echo "⚠️  .env文件不存在，从.env.example复制..."
    cp backend/.env.example backend/.env
    echo "⚠️  请编辑 backend/.env 文件，填入必要的API密钥"
fi

# 进入backend目录
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 运行数据库迁移（如果有）
# echo "🔄 运行数据库迁移..."
# alembic upgrade head

# 启动FastAPI开发服务器
echo ""
echo "✅ 开发环境已就绪！"
echo ""
echo "📍 API服务: http://localhost:8000"
echo "📍 API文档: http://localhost:8000/docs"
echo "📍 健康检查: http://localhost:8000/health"
echo ""
echo "🔥 启动FastAPI服务器..."
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
