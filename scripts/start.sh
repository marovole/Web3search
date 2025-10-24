#!/bin/bash

# ================================
# 生产环境启动脚本
# 用于Railway/Docker部署
# ================================

set -e

echo "🚀 启动 Web3 Search API (生产模式)..."

cd /app/backend || cd backend

# 等待数据库就绪
echo "⏳ 等待数据库连接..."
python -c "
import asyncio
from app.core.database import engine

async def wait_for_db():
    max_retries = 30
    for i in range(max_retries):
        try:
            async with engine.connect() as conn:
                await conn.execute('SELECT 1')
            print('✅ 数据库连接成功')
            return
        except Exception as e:
            print(f'等待数据库... ({i+1}/{max_retries})')
            await asyncio.sleep(2)
    raise Exception('数据库连接超时')

asyncio.run(wait_for_db())
"

# 运行数据库迁移（如果需要）
if [ -f "alembic.ini" ]; then
    echo "🔄 运行数据库迁移..."
    alembic upgrade head
fi

# 启动生产服务器
echo "🔥 启动生产服务器..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --log-level info \
    --no-access-log
