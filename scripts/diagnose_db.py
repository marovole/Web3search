#!/usr/bin/env python3
"""
数据库状态诊断脚本
检查迁移完成情况
"""

import asyncio
import asyncpg
import sys
import os

# 数据库连接配置（从环境变量读取）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.hxxnkbxyjhhorfeodiji:kaJtGrK8s54jOw56@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"
)

async def diagnose():
    """诊断数据库状态"""
    print("🔍 开始诊断数据库状态...")
    print("=" * 60)

    try:
        conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)

        # 1. 检查列和数据类型
        print("\n📋 1. 表结构检查:")
        columns = await conn.fetch('''
            SELECT table_name, column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name IN ('conversations','messages','reports')
            ORDER BY table_name, ordinal_position
        ''')

        current_table = None
        for col in columns:
            if col['table_name'] != current_table:
                current_table = col['table_name']
                print(f"\n   📊 {current_table}:")
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = col['column_default'] or "无"
            print(f"      - {col['column_name']}: {col['data_type']} ({nullable}) DEFAULT {default}")

        # 2. 检查约束
        print("\n\n🔒 2. 约束检查:")
        constraints = await conn.fetch('''
            SELECT conrelid::regclass AS table_name,
                   conname AS constraint_name,
                   contype,
                   pg_get_constraintdef(oid) AS definition
            FROM pg_constraint
            WHERE connamespace = 'public'::regnamespace
              AND conrelid::regclass::text IN ('public.conversations','public.messages','public.reports')
            ORDER BY table_name, contype DESC
        ''')

        current_table = None
        for const in constraints:
            if str(const['table_name']) != current_table:
                current_table = str(const['table_name'])
                print(f"\n   {current_table}:")
            type_map = {'p': 'PRIMARY KEY', 'f': 'FOREIGN KEY', 'c': 'CHECK', 'u': 'UNIQUE'}
            ctype = type_map.get(const['contype'], const['contype'])
            print(f"      - [{ctype}] {const['constraint_name']}")
            print(f"        {const['definition']}")

        # 3. 检查索引
        print("\n\n📑 3. 索引检查:")
        indexes = await conn.fetch('''
            SELECT tablename, indexname, indexdef
            FROM pg_indexes
            WHERE schemaname='public'
              AND tablename IN ('conversations','messages','reports')
            ORDER BY tablename, indexname
        ''')

        current_table = None
        for idx in indexes:
            if idx['tablename'] != current_table:
                current_table = idx['tablename']
                print(f"\n   {current_table}:")
            print(f"      - {idx['indexname']}")

        # 4. 检查孤立数据
        print("\n\n⚠️  4. 数据完整性检查:")

        orphan_messages = await conn.fetchval('''
            SELECT COUNT(*) FROM public.messages m
            LEFT JOIN public.conversations c ON m.conversation_id = c.id
            WHERE c.id IS NULL
        ''')
        print(f"   孤立的 messages: {orphan_messages}")

        # 检查 reports 表是否存在 conversation_id
        has_reports_conv = await conn.fetchval('''
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='reports' AND column_name='conversation_id'
            )
        ''')

        if has_reports_conv:
            try:
                orphan_reports = await conn.fetchval('''
                    SELECT COUNT(*) FROM public.reports r
                    LEFT JOIN public.conversations c ON r.conversation_id::text = c.id::text
                    WHERE c.id IS NULL
                ''')
                print(f"   孤立的 reports: {orphan_reports}")
            except Exception as e:
                print(f"   ⚠️  无法检查孤立 reports（类型不匹配）: {str(e)}")
        else:
            print(f"   reports 表没有 conversation_id 列")

        # 5. 检查扩展和默认值
        print("\n\n🔧 5. 扩展和默认值:")

        pgcrypto = await conn.fetchval('''
            SELECT extname FROM pg_extension WHERE extname='pgcrypto'
        ''')
        print(f"   pgcrypto 扩展: {'✅ 已安装' if pgcrypto else '❌ 未安装'}")

        conv_default = await conn.fetchval('''
            SELECT column_default
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name='conversations' AND column_name='id'
        ''')
        print(f"   conversations.id 默认值: {conv_default or '无'}")

        print("\n" + "=" * 60)
        print("✅ 诊断完成")

        await conn.close()
        return 0

    except Exception as e:
        print(f"\n💥 诊断失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(diagnose())
    sys.exit(exit_code)
