#!/bin/bash

# ================================
# 测试脚本
# 运行所有单元测试和集成测试
# ================================

set -e

echo "🧪 运行 Web3 Search 测试套件..."

cd backend

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 检查pytest是否安装
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest未安装，正在安装..."
    pip install pytest pytest-asyncio pytest-cov httpx-mock
fi

# 运行测试
echo ""
echo "📋 运行测试..."
echo ""

# 基础测试
pytest tests/ -v --tb=short

# 带覆盖率的测试
echo ""
echo "📊 生成覆盖率报告..."
echo ""
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "✅ 测试完成！"
echo "📊 覆盖率报告: backend/htmlcov/index.html"
