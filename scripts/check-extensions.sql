-- ========================================
-- 检查 Supabase 扩展状态
-- ========================================

-- 1. 检查已启用的扩展
SELECT
  extname AS extension_name,
  extversion AS version,
  CASE
    WHEN extname IN ('pgcrypto', 'pg_cron') THEN '✅ 必需'
    ELSE '其他'
  END AS status
FROM pg_extension
WHERE extname IN ('pgcrypto', 'pg_cron', 'uuid-ossp', 'pgsodium')
ORDER BY extname;

-- 2. 查看所有可用的扩展
SELECT
  name,
  installed_version,
  CASE
    WHEN installed_version IS NOT NULL THEN '✅ 已安装'
    ELSE '⏸️ 未安装'
  END AS status,
  comment
FROM pg_available_extensions
WHERE name IN ('pgcrypto', 'pg_cron')
ORDER BY name;

-- 3. 测试 pgcrypto 功能（如果已启用）
SELECT
  'pgcrypto 测试' AS test_name,
  gen_random_uuid() AS test_result;

-- 4. 测试 pg_cron（如果已启用）
SELECT
  'pg_cron 测试' AS test_name,
  COUNT(*) AS current_jobs
FROM cron.job;
