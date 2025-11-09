-- =================================================
-- Week 3 Day 13-14: 后台任务队列
-- 创建任务日志、统计和健康检查表
-- =================================================

-- 1. 任务运行记录表
CREATE TABLE IF NOT EXISTS task_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_name TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('pg_cron', 'worker')),
  scheduled_for TIMESTAMPTZ NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
  rows_affected INTEGER DEFAULT 0,
  error_message TEXT,
  duration_ms INTEGER,
  extra JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 幂等性约束：同一任务同一调度时间只能执行一次
  UNIQUE (job_name, scheduled_for)
);

-- 索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_task_runs_job_name ON task_runs(job_name);
CREATE INDEX IF NOT EXISTS idx_task_runs_status ON task_runs(status);
CREATE INDEX IF NOT EXISTS idx_task_runs_created_at ON task_runs(created_at DESC);

-- 2. 每日统计指标表
CREATE TABLE IF NOT EXISTS daily_metrics (
  stat_date DATE PRIMARY KEY,
  dau INTEGER NOT NULL DEFAULT 0,                    -- 每日活跃用户数
  total_conversations INTEGER NOT NULL DEFAULT 0,    -- 新增对话数
  total_messages INTEGER NOT NULL DEFAULT 0,         -- 新增消息数
  quick_chat_calls INTEGER NOT NULL DEFAULT 0,       -- 快速聊天调用次数
  deep_research_calls INTEGER NOT NULL DEFAULT 0,    -- 深度研究调用次数
  total_tokens INTEGER NOT NULL DEFAULT 0,           -- 总消耗 tokens
  error_count INTEGER NOT NULL DEFAULT 0,            -- 错误次数
  error_rate DECIMAL(5,2) DEFAULT 0.00,             -- 错误率 (%)
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. 每日热门查询表
CREATE TABLE IF NOT EXISTS daily_hot_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stat_date DATE NOT NULL,
  rank INTEGER NOT NULL CHECK (rank >= 1 AND rank <= 10),
  query_text TEXT NOT NULL,
  hit_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 唯一约束：每天每个排名只能有一个查询
  UNIQUE (stat_date, rank)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_daily_hot_queries_date ON daily_hot_queries(stat_date DESC);

-- 4. 健康检查事件表
CREATE TABLE IF NOT EXISTS healthcheck_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  check_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('healthy', 'degraded', 'down')),
  latency_ms INTEGER,
  error_message TEXT,
  details JSONB DEFAULT '{}'::jsonb,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_healthcheck_events_name ON healthcheck_events(check_name);
CREATE INDEX IF NOT EXISTS idx_healthcheck_events_status ON healthcheck_events(status);
CREATE INDEX IF NOT EXISTS idx_healthcheck_events_observed_at ON healthcheck_events(observed_at DESC);

-- 5. 数据清理审计表（记录清理操作）
CREATE TABLE IF NOT EXISTS cleanup_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operation TEXT NOT NULL,
  table_name TEXT NOT NULL,
  rows_deleted INTEGER NOT NULL DEFAULT 0,
  oldest_deleted_at TIMESTAMPTZ,
  newest_deleted_at TIMESTAMPTZ,
  executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  details JSONB DEFAULT '{}'::jsonb
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_cleanup_audit_table_name ON cleanup_audit(table_name);
CREATE INDEX IF NOT EXISTS idx_cleanup_audit_executed_at ON cleanup_audit(executed_at DESC);

-- =================================================
-- 辅助函数
-- =================================================

-- 记录任务开始
CREATE OR REPLACE FUNCTION start_task_run(
  p_job_name TEXT,
  p_origin TEXT,
  p_scheduled_for TIMESTAMPTZ DEFAULT NOW()
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  v_task_id UUID;
BEGIN
  INSERT INTO task_runs (job_name, origin, scheduled_for, status, started_at)
  VALUES (p_job_name, p_origin, p_scheduled_for, 'running', NOW())
  ON CONFLICT (job_name, scheduled_for) DO NOTHING
  RETURNING id INTO v_task_id;

  RETURN v_task_id;
END;
$$;

-- 记录任务完成
CREATE OR REPLACE FUNCTION finish_task_run(
  p_task_id UUID,
  p_status TEXT,
  p_rows_affected INTEGER DEFAULT 0,
  p_error_message TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE task_runs
  SET
    finished_at = NOW(),
    status = p_status,
    rows_affected = p_rows_affected,
    error_message = p_error_message,
    duration_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
  WHERE id = p_task_id;
END;
$$;

-- =================================================
-- RLS (Row Level Security) 策略
-- =================================================

-- 启用 RLS
ALTER TABLE task_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_hot_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE healthcheck_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleanup_audit ENABLE ROW LEVEL SECURITY;

-- 允许服务角色完全访问
CREATE POLICY "Service role can do everything on task_runs"
  ON task_runs FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role can do everything on daily_metrics"
  ON daily_metrics FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role can do everything on daily_hot_queries"
  ON daily_hot_queries FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role can do everything on healthcheck_events"
  ON healthcheck_events FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role can do everything on cleanup_audit"
  ON cleanup_audit FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- 允许匿名用户读取统计数据（可选）
CREATE POLICY "Anyone can read daily_metrics"
  ON daily_metrics FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Anyone can read daily_hot_queries"
  ON daily_hot_queries FOR SELECT
  TO anon
  USING (true);

-- =================================================
-- 注释
-- =================================================

COMMENT ON TABLE task_runs IS '后台任务运行记录表';
COMMENT ON TABLE daily_metrics IS '每日统计指标表';
COMMENT ON TABLE daily_hot_queries IS '每日热门查询 Top 10';
COMMENT ON TABLE healthcheck_events IS '健康检查事件记录表';
COMMENT ON TABLE cleanup_audit IS '数据清理审计日志表';

COMMENT ON FUNCTION start_task_run IS '开始一个任务并返回任务 ID';
COMMENT ON FUNCTION finish_task_run IS '完成一个任务并记录结果';
