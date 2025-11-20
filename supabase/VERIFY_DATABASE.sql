-- =============================================
-- 数据库验证脚本
-- 检查所有必要的表是否已创建
-- =============================================

-- 1. 检查所有表
SELECT
  '✅ 表存在检查' as check_type,
  tablename,
  CASE
    WHEN tablename IS NOT NULL THEN '✅ 存在'
    ELSE '❌ 缺失'
  END as status
FROM (
  VALUES
    ('conversations'),
    ('messages'),
    ('projects'),
    ('background_tasks'),
    ('deep_research_tasks'),
    ('reports'),
    ('api_calls_telemetry')
) AS required_tables(tablename)
LEFT JOIN pg_tables
  ON pg_tables.tablename = required_tables.tablename
  AND pg_tables.schemaname = 'public'
ORDER BY required_tables.tablename;

-- 2. 检查conversations表的行数
SELECT
  '📊 数据统计' as info,
  'conversations' as table_name,
  COUNT(*) as row_count
FROM public.conversations

UNION ALL

SELECT
  '📊 数据统计',
  'projects',
  COUNT(*)
FROM public.projects

UNION ALL

SELECT
  '📊 数据统计',
  'messages',
  COUNT(*)
FROM public.messages;

-- 3. 列出所有projects（应该至少有Bitcoin和Ethereum）
SELECT
  '🪙 测试数据' as info,
  symbol,
  name,
  coingecko_id
FROM public.projects
ORDER BY symbol;
