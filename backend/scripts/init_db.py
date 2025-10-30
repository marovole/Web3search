#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有表结构
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models import (  # noqa: F401
    project,
    snapshot,
    report,
    conversation,
    user,
)


async def init_database():
    """初始化数据库，创建所有表"""
    print("🚀 开始初始化数据库...")

    try:
        async with engine.begin() as conn:
            print("📊 创建数据库表...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ 数据库表创建成功！")

        print("\n📋 已创建的表:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

    print("\n✅ 数据库初始化完成！")
    return True


if __name__ == "__main__":
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)
