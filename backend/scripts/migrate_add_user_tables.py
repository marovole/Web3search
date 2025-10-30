#!/usr/bin/env python3
"""
用户账号系统数据库迁移脚本
使用SQLAlchemy创建用户相关表结构
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models import (  # noqa: F401
    project,
    report,
    conversation,
    user,
)


async def migrate_user_tables():
    """迁移数据库，添加用户相关表"""
    print("🚀 开始用户账号系统数据库迁移...")

    try:
        async with engine.begin() as conn:
            print("📊 创建用户相关表...")
            
            # 导入所有模型，确保它们被注册到 Base.metadata
            # 表结构已经通过模型定义，create_all会自动处理
            
            # 创建所有表（如果不存在）
            await conn.run_sync(Base.metadata.create_all)
            
            print("✅ 用户相关表创建成功！")

        print("\n📋 已创建/更新的表:")
        user_tables = ['users', 'user_preferences', 'sessions']
        for table_name in user_tables:
            if table_name in Base.metadata.tables:
                print(f"  ✅ {table_name}")
            else:
                print(f"  ⚠️  {table_name} (未找到)")

        # 检查conversations和reports表的user_id字段
        print("\n📋 检查现有表的外键:")
        async with engine.connect() as conn:
            # 检查conversations表
            result = await conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'conversations' AND column_name = 'user_id'
                """
            )
            if result.fetchone():
                print("  ✅ conversations.user_id 字段已存在")
            else:
                print("  ⚠️  conversations.user_id 字段不存在，需要手动添加")

            # 检查reports表
            result = await conn.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'reports' AND column_name = 'user_id'
                """
            )
            if result.fetchone():
                print("  ✅ reports.user_id 字段已存在")
            else:
                print("  ⚠️  reports.user_id 字段不存在，需要手动添加")

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

    print("\n✅ 数据库迁移完成！")
    print("\n📝 注意事项:")
    print("  1. 如果conversations或reports表已存在但缺少user_id字段，")
    print("     请手动执行SQL脚本: scripts/migrate_add_user_tables.sql")
    print("  2. 如果使用Alembic，请创建迁移脚本而不是直接使用此脚本")
    print("  3. 生产环境建议先备份数据库再执行迁移")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(migrate_user_tables())
    sys.exit(0 if success else 1)

