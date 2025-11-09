#!/usr/bin/env python3
"""
数据库迁移执行脚本
修复 UUID vs Integer 不匹配问题
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# 数据库连接配置（从环境变量读取）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.hxxnkbxyjhhorfeodiji:kaJtGrK8s54jOw56@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"
)

async def execute_migration(connection, migration_file: str):
    """执行单个迁移文件"""
    print(f"📄 执行迁移: {migration_file}")

    try:
        # 读取迁移文件内容
        migration_path = Path(__file__).parent.parent / "supabase" / "migrations" / migration_file
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # 执行迁移
        await connection.execute(migration_sql)
        print(f"✅ 迁移 {migration_file} 执行成功")

    except Exception as e:
        print(f"❌ 迁移 {migration_file} 执行失败: {str(e)}")
        raise

async def validate_migration(connection):
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")

    # 检查 conversations 表的 ID 类型
    result = await connection.fetchval("""
        SELECT pg_typeof(id) FROM public.conversations LIMIT 1
    """)
    print(f"   conversations.id 类型: {result}")

    # 检查 messages 表是否有 metadata 列
    exists = await connection.fetchval("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'messages' AND column_name = 'metadata'
    """)
    print(f"   messages.metadata 列存在: {'是' if exists > 0 else '否'}")

    # 检查外键约束
    constraints = await connection.fetch("""
        SELECT constraint_name, table_name
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name IN ('messages', 'reports')
    """)

    print(f"   外键约束数量: {len(constraints)}")
    for constraint in constraints:
        print(f"     - {constraint['table_name']}.{constraint['constraint_name']}")

    # 检查数据完整性
    orphaned_messages = await connection.fetchval("""
        SELECT COUNT(*) FROM public.messages
        WHERE conversation_id IS NULL
    """)
    print(f"   孤立消息数量: {orphaned_messages}")

    return {
        'conversations_id_type': result,
        'messages_metadata_exists': exists > 0,
        'foreign_key_constraints': len(constraints),
        'orphaned_messages': orphaned_messages
    }

async def main():
    """主函数"""
    print("🚀 开始执行数据库迁移")
    print("=" * 50)

    try:
        # 连接数据库
        print("📡 连接数据库...")
        connection = await asyncpg.connect(DATABASE_URL)
        print("✅ 数据库连接成功")

        # 开始事务
        async with connection.transaction():
            # 执行迁移1: UUID 转换
            await execute_migration(connection, "20251110_switch_conversations_to_uuid.sql")

            # 执行迁移2: 添加 metadata 列
            await execute_migration(connection, "20251110_add_messages_metadata.sql")

        # 验证迁移结果
        validation_result = await validate_migration(connection)

        print("\n✅ 所有迁移执行完成!")
        print(f"📊 迁移验证结果:")
        print(f"   - conversations.id 类型: {validation_result['conversations_id_type']}")
        print(f"   - messages.metadata 存在: {validation_result['messages_metadata_exists']}")
        print(f"   - 外键约束数量: {validation_result['foreign_key_constraints']}")
        print(f"   - 孤立消息数量: {validation_result['orphaned_messages']}")

        # 关闭连接
        await connection.close()

        # 判断迁移是否成功
        if (validation_result['conversations_id_type'] == 'uuid' and
            validation_result['messages_metadata_exists'] and
            validation_result['orphaned_messages'] == 0):
            print("\n🎉 数据库迁移成功完成!")
            return 0
        else:
            print("\n⚠️ 迁移完成但验证发现问题")
            return 1

    except Exception as e:
        print(f"\n💥 迁移执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)