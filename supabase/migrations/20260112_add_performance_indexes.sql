-- Performance indexes for Agent system tables
-- Migration: 20260112_add_performance_indexes.sql

-- agent_tasks indexes
CREATE INDEX IF NOT EXISTS idx_agent_tasks_user_status 
  ON agent_tasks(user_id, status);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_type_status 
  ON agent_tasks(task_type, status);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_next_run 
  ON agent_tasks(next_run_at) 
  WHERE status = 'active';

-- agent_runs indexes
CREATE INDEX IF NOT EXISTS idx_agent_runs_task_started 
  ON agent_runs(task_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_status 
  ON agent_runs(status, started_at DESC);

-- notifications indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_created 
  ON notifications(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread 
  ON notifications(user_id, read) 
  WHERE read = false;

CREATE INDEX IF NOT EXISTS idx_notifications_type_created 
  ON notifications(type, created_at DESC);

-- watchlist indexes
CREATE INDEX IF NOT EXISTS idx_watchlist_user_symbol 
  ON watchlist(user_id, symbol);

-- push_subscriptions indexes
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user 
  ON push_subscriptions(user_id);

-- user_quotas indexes
CREATE INDEX IF NOT EXISTS idx_user_quotas_reset_dates 
  ON user_quotas(daily_reset_at, monthly_reset_at);

-- agent_conversations indexes (if table exists)
CREATE INDEX IF NOT EXISTS idx_agent_conversations_user_created 
  ON agent_conversations(user_id, created_at DESC);
