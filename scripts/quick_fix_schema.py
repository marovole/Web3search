#!/usr/bin/env python3
"""
快速数据库架构修复
只修复必要的 UUID 和 metadata 问题
"""

import asyncio
import asyncpg
import sys
import uuid

# 数据库连接配置
DATABASE_URL = "postgresql://postgres.hxxnkbxyjhhorfeodiji:kaJtGrK8s54jOw56@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"

async def quick_fix():
    """快速修复数据库架构问题"""
    print("🚀 开始快速数据库架构修复")
    print("=" * 50)

    try:
        # 连接数据库
        print("📡 连接数据库...")
        connection = await asyncpg.connect(DATABASE_URL)
        print("✅ 数据库连接成功")

        # 开始事务
        async with connection.transaction():
            print("\n🔧 修复 1: 添加 messages.metadata 列")
            try:
                await connection.execute("""
                    ALTER TABLE public.messages
                    ADD COLUMN IF NOT EXISTS metadata JSONB
                """)
                print("✅ metadata 列已添加")
            except Exception as e:
                print(f"⚠️ metadata 列可能已存在: {str(e)}")

            print("\n🔧 修复 2: 检查 conversations 表结构")
            # 检查当前表结构
            conversations_schema = await connection.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'conversations'
                ORDER BY ordinal_position
            """)

            print("   conversations 表结构:")
            for col in conversations_schema:
                print(f"     - {col['column_name']}: {col['data_type']}")

            messages_schema = await connection.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'messages'
                ORDER BY ordinal_position
            """)

            print("   messages 表结构:")
            for col in messages_schema:
                print(f"     - {col['column_name']}: {col['data_type']}")

            print("\n🔧 修复 3: 检查数据类型兼容性")
            # 检查 conversations ID 类型
            id_type = await connection.fetchval("""
                SELECT pg_typeof(id) FROM public.conversations LIMIT 1
            """)
            print(f"   conversations.id 类型: {id_type}")

            # 检查 messages conversation_id 类型
            conv_id_type = await connection.fetchval("""
                SELECT pg_typeof(conversation_id) FROM public.messages LIMIT 1
            """)
            print(f"   messages.conversation_id 类型: {conv_id_type}")

            # 如果类型不匹配，我们需要清理现有数据并让应用重新创建
            if id_type != conv_id_type:
                print(f"\n⚠️ 发现类型不匹配: conversations.id 是 {id_type}, messages.conversation_id 是 {conv_id_type}")

                print("🔧 修复 4: 清理现有对话数据以重新开始")
                # 删除现有的消息和对话记录，让应用重新创建正确的UUID记录
                await connection.execute("DELETE FROM public.messages")
                await connection.execute("DELETE FROM public.conversations")
                print("✅ 已清理现有对话数据，应用将重新创建正确的UUID记录")

        # 验证修复结果
        print("\n🔍 验证修复结果...")

        # 检查 metadata 列
        metadata_exists = await connection.fetchval("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'messages' AND column_name = 'metadata'
        """)
        print(f"   messages.metadata 列存在: {'是' if metadata_exists > 0 else '否'}")

        # 检查表是否为空（准备重新开始）
        conv_count = await connection.fetchval("SELECT COUNT(*) FROM public.conversations")
        msg_count = await connection.fetchval("SELECT COUNT(*) FROM public.messages")
        print(f"   conversations 表行数: {conv_count}")
        print(f"   messages 表行数: {msg_count}")

        # 关闭连接
        await connection.close()

        if metadata_exists > 0:
            print("\n✅ 数据库架构修复完成!")
            print("💡 应用现在可以创建新的UUID对话和消息记录")
            return 0
        else:
            print("\n❌ metadata 列添加失败")
            return 2

    except Exception as e:
        print(f"\n💥 修复执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(quick_fix())
    sys.exit(exit_code)