-- =================================================
-- Week 3 Day 13-14: pg_cron 后台任务
-- 设置定时任务（数据清理、统计聚合）
-- =================================================

-- 注意：需要先在 Supabase Dashboard 中启用 pg_cron 扩展
-- Dashboard -> Database -> Extensions -> 搜索 "pg_cron" -> Enable

-- 检查 pg_cron 是否已启用
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_extension WHERE extname = 'pg_cron'
  ) THEN
    RAISE EXCEPTION 'pg_cron extension is not enabled. Please enable it in Supabase Dashboard first.';
  END IF;
END $$;

-- =================================================
-- 1. 数据清理任务
-- 每天 UTC 02:05 执行
-- =================================================

SELECT cron.schedule(
  'data-cleanup-old-conversations',
  '5 2 * * *',  -- 每天 UTC 02:05
  $$
  DO $$
  DECLARE
    v_task_id UUID;
    v_deleted_count INTEGER;
    v_oldest_date TIMESTAMPTZ;
    v_error_message TEXT;
  BEGIN
    -- 开始任务
    v_task_id := start_task_run('data-cleanup-old-conversations', 'pg_cron');

    BEGIN
      -- 删除 30 天前的对话（messages 会通过 FK CASCADE 自动删除）
      WITH deleted AS (
        DELETE FROM conversations
        WHERE created_at < NOW() - INTERVAL '30 days'
        RETURNING id, created_at
      )
      SELECT COUNT(*), MIN(created_at)
      INTO v_deleted_count, v_oldest_date
      FROM deleted;

      -- 记录审计日志
      INSERT INTO cleanup_audit (
        operation,
        table_name,
        rows_deleted,
        oldest_deleted_at,
        details
      ) VALUES (
        'delete_old_conversations',
        'conversations',
        v_deleted_count,
        v_oldest_date,
        jsonb_build_object('retention_days', 30)
      );

      -- 标记任务成功
      PERFORM finish_task_run(v_task_id, 'success', v_deleted_count);

    EXCEPTION WHEN OTHERS THEN
      -- 记录错误
      GET STACKED DIAGNOSTICS v_error_message = MESSAGE_TEXT;
      PERFORM finish_task_run(v_task_id, 'failed', 0, v_error_message);
      RAISE;
    END;
  END $$;
  $$
);

-- =================================================
-- 2. 每日统计任务
-- 每天 UTC 02:15 执行
-- =================================================

SELECT cron.schedule(
  'daily-stats-aggregation',
  '15 2 * * *',  -- 每天 UTC 02:15
  $$
  DO $$
  DECLARE
    v_task_id UUID;
    v_stat_date DATE;
    v_dau INTEGER;
    v_total_conversations INTEGER;
    v_total_messages INTEGER;
    v_total_tokens BIGINT;
    v_error_count INTEGER;
    v_total_requests INTEGER;
    v_error_rate DECIMAL(5,2);
    v_error_message TEXT;
  BEGIN
    -- 开始任务
    v_task_id := start_task_run('daily-stats-aggregation', 'pg_cron');
    v_stat_date := CURRENT_DATE - INTERVAL '1 day';  -- 统计昨天的数据

    BEGIN
      -- 计算每日活跃用户数（暂时用对话数估算，后续可通过 user_id）
      SELECT COUNT(DISTINCT id)
      INTO v_dau
      FROM conversations
      WHERE DATE(created_at) = v_stat_date;

      -- 新增对话数
      SELECT COUNT(*)
      INTO v_total_conversations
      FROM conversations
      WHERE DATE(created_at) = v_stat_date;

      -- 新增消息数
      SELECT COUNT(*)
      INTO v_total_messages
      FROM messages
      WHERE DATE(created_at) = v_stat_date;

      -- 总消耗 tokens（从 conversations 表）
      SELECT COALESCE(SUM(total_tokens), 0)
      INTO v_total_tokens
      FROM conversations
      WHERE DATE(created_at) = v_stat_date;

      -- 错误次数（从 task_runs 表）
      SELECT COUNT(*)
      INTO v_error_count
      FROM task_runs
      WHERE DATE(created_at) = v_stat_date
        AND status = 'failed';

      -- 总请求数
      v_total_requests := v_total_messages;

      -- 错误率
      IF v_total_requests > 0 THEN
        v_error_rate := (v_error_count::DECIMAL / v_total_requests) * 100;
      ELSE
        v_error_rate := 0;
      END IF;

      -- 插入或更新统计数据
      INSERT INTO daily_metrics (
        stat_date,
        dau,
        total_conversations,
        total_messages,
        total_tokens,
        error_count,
        error_rate,
        generated_at
      ) VALUES (
        v_stat_date,
        v_dau,
        v_total_conversations,
        v_total_messages,
        v_total_tokens,
        v_error_count,
        v_error_rate,
        NOW()
      )
      ON CONFLICT (stat_date) DO UPDATE SET
        dau = EXCLUDED.dau,
        total_conversations = EXCLUDED.total_conversations,
        total_messages = EXCLUDED.total_messages,
        total_tokens = EXCLUDED.total_tokens,
        error_count = EXCLUDED.error_count,
        error_rate = EXCLUDED.error_rate,
        updated_at = NOW();

      -- 标记任务成功
      PERFORM finish_task_run(v_task_id, 'success', 1);

    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS v_error_message = MESSAGE_TEXT;
      PERFORM finish_task_run(v_task_id, 'failed', 0, v_error_message);
      RAISE;
    END;
  END $$;
  $$
);

-- =================================================
-- 3. 热门查询统计任务
-- 每天 UTC 02:20 执行
-- =================================================

SELECT cron.schedule(
  'daily-hot-queries',
  '20 2 * * *',  -- 每天 UTC 02:20
  $$
  DO $$
  DECLARE
    v_task_id UUID;
    v_stat_date DATE;
    v_inserted_count INTEGER;
    v_error_message TEXT;
  BEGIN
    -- 开始任务
    v_task_id := start_task_run('daily-hot-queries', 'pg_cron');
    v_stat_date := CURRENT_DATE - INTERVAL '1 day';

    BEGIN
      -- 删除旧的热门查询记录
      DELETE FROM daily_hot_queries WHERE stat_date = v_stat_date;

      -- 插入 Top 10 热门查询
      WITH query_stats AS (
        SELECT
          content AS query_text,
          COUNT(*) AS hit_count,
          ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rank
        FROM messages
        WHERE role = 'user'
          AND DATE(created_at) = v_stat_date
          AND LENGTH(content) > 0
          AND LENGTH(content) < 200  -- 过滤掉过长的查询
        GROUP BY content
        ORDER BY hit_count DESC
        LIMIT 10
      )
      INSERT INTO daily_hot_queries (stat_date, rank, query_text, hit_count)
      SELECT v_stat_date, rank, query_text, hit_count
      FROM query_stats;

      GET DIAGNOSTICS v_inserted_count = ROW_COUNT;

      -- 标记任务成功
      PERFORM finish_task_run(v_task_id, 'success', v_inserted_count);

    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS v_error_message = MESSAGE_TEXT;
      PERFORM finish_task_run(v_task_id, 'failed', 0, v_error_message);
      RAISE;
    END;
  END $$;
  $$
);

-- =================================================
-- 4. 清理失败任务记录
-- 每周日 UTC 03:00 执行
-- =================================================

SELECT cron.schedule(
  'cleanup-failed-tasks',
  '0 3 * * 0',  -- 每周日 UTC 03:00
  $$
  DO $$
  DECLARE
    v_task_id UUID;
    v_deleted_count INTEGER;
    v_error_message TEXT;
  BEGIN
    v_task_id := start_task_run('cleanup-failed-tasks', 'pg_cron');

    BEGIN
      -- 删除 7 天前的失败任务记录
      WITH deleted AS (
        DELETE FROM task_runs
        WHERE status = 'failed'
          AND created_at < NOW() - INTERVAL '7 days'
        RETURNING id
      )
      SELECT COUNT(*) INTO v_deleted_count FROM deleted;

      -- 记录审计日志
      INSERT INTO cleanup_audit (
        operation,
        table_name,
        rows_deleted,
        details
      ) VALUES (
        'delete_old_failed_tasks',
        'task_runs',
        v_deleted_count,
        jsonb_build_object('retention_days', 7)
      );

      PERFORM finish_task_run(v_task_id, 'success', v_deleted_count);

    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS v_error_message = MESSAGE_TEXT;
      PERFORM finish_task_run(v_task_id, 'failed', 0, v_error_message);
      RAISE;
    END;
  END $$;
  $$
);

-- =================================================
-- 5. 清理旧的健康检查事件
-- 每天 UTC 03:30 执行
-- =================================================

SELECT cron.schedule(
  'cleanup-old-healthcheck-events',
  '30 3 * * *',  -- 每天 UTC 03:30
  $$
  DO $$
  DECLARE
    v_task_id UUID;
    v_deleted_count INTEGER;
    v_error_message TEXT;
  BEGIN
    v_task_id := start_task_run('cleanup-old-healthcheck-events', 'pg_cron');

    BEGIN
      -- 只保留最近 7 天的健康检查记录
      WITH deleted AS (
        DELETE FROM healthcheck_events
        WHERE observed_at < NOW() - INTERVAL '7 days'
        RETURNING id
      )
      SELECT COUNT(*) INTO v_deleted_count FROM deleted;

      INSERT INTO cleanup_audit (
        operation,
        table_name,
        rows_deleted,
        details
      ) VALUES (
        'delete_old_healthcheck_events',
        'healthcheck_events',
        v_deleted_count,
        jsonb_build_object('retention_days', 7)
      );

      PERFORM finish_task_run(v_task_id, 'success', v_deleted_count);

    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS v_error_message = MESSAGE_TEXT;
      PERFORM finish_task_run(v_task_id, 'failed', 0, v_error_message);
      RAISE;
    END;
  END $$;
  $$
);

-- =================================================
-- 查看已配置的 cron 任务
-- =================================================

-- 查询所有 cron 任务
-- SELECT * FROM cron.job;

-- 查询任务运行历史
-- SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;

-- 取消任务示例（需要时手动执行）
-- SELECT cron.unschedule('data-cleanup-old-conversations');
