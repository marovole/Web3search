#!/usr/bin/env python3
"""
数据库修复脚本
修复部分完成的迁移
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

# Codex 提供的修复 SQL
REPAIR_SQL = """
BEGIN;

-- 修复 reports 表的 conversation_id 类型不匹配
-- 如果 reports 表有 conversation_id 列但类型是 integer，需要转换为 uuid
DO $$
DECLARE
    conv_id_type text;
BEGIN
    -- 检查 reports.conversation_id 的类型
    SELECT data_type INTO conv_id_type
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name='reports' AND column_name='conversation_id';

    IF conv_id_type = 'integer' THEN
        RAISE NOTICE '修复 reports.conversation_id: integer -> uuid';

        -- 删除旧的索引和约束（如果存在）
        DROP INDEX IF EXISTS ix_reports_conversation_id;

        -- 添加新的 UUID 列
        ALTER TABLE public.reports ADD COLUMN conversation_id_uuid UUID;

        -- 尝试从 uuid_id 或其他方式迁移数据
        -- 如果 reports 有 uuid_id 列，可能需要手动映射
        -- 这里先设置为 NULL，需要根据实际情况调整

        -- 删除旧列
        ALTER TABLE public.reports DROP COLUMN conversation_id;

        -- 重命名新列
        ALTER TABLE public.reports RENAME COLUMN conversation_id_uuid TO conversation_id;

        RAISE NOTICE 'reports.conversation_id 已转换为 UUID';
    ELSE
        RAISE NOTICE 'reports.conversation_id 已经是 UUID 类型';
    END IF;
END $$;

-- 重新创建缺失的外键约束
DO $$
BEGIN
    -- messages 表的外键
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'messages_conversation_id_fkey'
          AND conrelid = 'public.messages'::regclass
    ) THEN
        RAISE NOTICE '添加 messages 外键约束';
        ALTER TABLE public.messages
          ADD CONSTRAINT messages_conversation_id_fkey
          FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;
    ELSE
        RAISE NOTICE 'messages 外键约束已存在';
    END IF;

    -- reports 表的外键（如果 conversation_id 列存在）
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='reports' AND column_name='conversation_id'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'reports_conversation_id_fkey'
              AND conrelid = 'public.reports'::regclass
        ) THEN
            RAISE NOTICE '添加 reports 外键约束';
            ALTER TABLE public.reports
              ADD CONSTRAINT reports_conversation_id_fkey
              FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;
        ELSE
            RAISE NOTICE 'reports 外键约束已存在';
        END IF;
    END IF;
END $$;

-- 重新创建缺失的索引
DO $$
BEGIN
    RAISE NOTICE '创建缺失的索引...';
END $$;

CREATE INDEX IF NOT EXISTS ix_messages_conversation_id
  ON public.messages(conversation_id);

CREATE INDEX IF NOT EXISTS ix_messages_conversation_created
  ON public.messages(conversation_id, created_at);

CREATE INDEX IF NOT EXISTS ix_reports_conversation_id
  ON public.reports(conversation_id);

CREATE INDEX IF NOT EXISTS ix_messages_metadata_gin
  ON public.messages USING GIN (metadata);

COMMIT;
"""

async def repair():
    """执行修复"""
    print("🔧 开始修复数据库...")
    print("=" * 60)

    try:
        conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)

        print("\n📝 执行修复 SQL...")
        await conn.execute(REPAIR_SQL)

        print("\n✅ 修复 SQL 执行成功")
        print("\n📊 验证修复结果...")

        # 验证
        # 1. 检查外键数量
        fk_count = await conn.fetchval('''
            SELECT COUNT(*) FROM pg_constraint
            WHERE contype = 'F'
              AND conrelid::regclass::text IN ('public.messages', 'public.reports')
        ''')
        print(f"   外键约束数量: {fk_count}")

        # 2. 检查索引
        metadata_idx = await conn.fetchval('''
            SELECT indexname FROM pg_indexes
            WHERE schemaname='public'
              AND tablename = 'messages'
              AND indexname = 'ix_messages_metadata_gin'
        ''')
        print(f"   metadata GIN 索引: {'✅ 存在' if metadata_idx else '❌ 不存在'}")

        # 3. 检查 reports.conversation_id 类型
        reports_conv_type = await conn.fetchval('''
            SELECT data_type FROM information_schema.columns
            WHERE table_schema='public' AND table_name='reports' AND column_name='conversation_id'
        ''')
        print(f"   reports.conversation_id 类型: {reports_conv_type}")

        await conn.close()

        print("\n" + "=" * 60)
        print("✅ 修复完成")
        return 0

    except Exception as e:
        print(f"\n💥 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(repair())
    sys.exit(exit_code)
