/***********************************************
 * Deep Research Tasks Table Migration
 * 
 * 问题: POST /api/v1/deep-research 返回 500 错误
 * 原因: deep_research_tasks 表不存在
 * 
 * 执行方式:
 * 1. 登录 Supabase Dashboard: https://supabase.com/dashboard
 * 2. 选择项目 -> SQL Editor
 * 3. 复制此脚本并执行
 **********************************************/

-- =============================================
-- STEP 1: 创建 Deep Research Tasks 表
-- =============================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Deep Research Tasks Table
CREATE TABLE IF NOT EXISTS public.deep_research_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Task metadata
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  client_session_id uuid,
  conversation_id uuid REFERENCES public.conversations(id) ON DELETE CASCADE,

  -- Task details
  query text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),

  -- Research configuration
  research_depth text NOT NULL DEFAULT 'standard' CHECK (research_depth IN ('quick', 'standard', 'comprehensive')),
  max_sources integer NOT NULL DEFAULT 10,
  focus_areas text[],

  -- Model configuration
  model_id text,
  model_provider text CHECK (model_provider IN ('qwen', 'deepseek', 'anthropic', 'openai')),
  temperature numeric(3,2) DEFAULT 0.7,

  -- Results
  result jsonb,
  summary text,
  answer text,
  sources jsonb NOT NULL DEFAULT '[]'::jsonb,
  citations jsonb NOT NULL DEFAULT '[]'::jsonb,

  -- Progress tracking
  progress_percent integer NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
  current_step text,
  steps_completed integer NOT NULL DEFAULT 0,
  total_steps integer NOT NULL DEFAULT 1,

  -- Performance metrics
  tokens_prompt integer NOT NULL DEFAULT 0,
  tokens_completion integer NOT NULL DEFAULT 0,
  cost_usd numeric(12,6) NOT NULL DEFAULT 0,
  started_at timestamptz,
  completed_at timestamptz,
  duration_ms integer,

  -- Error tracking
  error_code text,
  error_message text,
  retry_count integer NOT NULL DEFAULT 0,

  -- Timestamps
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  expires_at timestamptz NOT NULL DEFAULT (timezone('utc', now()) + interval '24 hours'),

  -- Metadata
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  tags text[]
);

COMMIT;

-- =============================================
-- STEP 2: 创建索引
-- =============================================

CREATE INDEX IF NOT EXISTS deep_research_tasks_user_idx
  ON public.deep_research_tasks (user_id, created_at DESC)
  WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS deep_research_tasks_session_idx
  ON public.deep_research_tasks (client_session_id, created_at DESC)
  WHERE client_session_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS deep_research_tasks_status_idx
  ON public.deep_research_tasks (status, created_at DESC);

CREATE INDEX IF NOT EXISTS deep_research_tasks_conversation_idx
  ON public.deep_research_tasks (conversation_id, created_at DESC)
  WHERE conversation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS deep_research_tasks_expires_idx
  ON public.deep_research_tasks (expires_at)
  WHERE status IN ('pending', 'running');

CREATE INDEX IF NOT EXISTS deep_research_tasks_pending_idx
  ON public.deep_research_tasks (created_at)
  WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS deep_research_tasks_running_idx
  ON public.deep_research_tasks (user_id, created_at)
  WHERE status = 'running';

CREATE INDEX IF NOT EXISTS deep_research_tasks_completed_idx
  ON public.deep_research_tasks (user_id, created_at DESC)
  WHERE status = 'completed';

-- =============================================
-- STEP 3: 启用 RLS 并创建策略
-- =============================================

ALTER TABLE public.deep_research_tasks ENABLE ROW LEVEL SECURITY;

-- 删除旧策略（如果存在）
DROP POLICY IF EXISTS "Users can view their own research tasks" ON public.deep_research_tasks;
DROP POLICY IF EXISTS "Users can create their own research tasks" ON public.deep_research_tasks;
DROP POLICY IF EXISTS "Users can update their own research tasks" ON public.deep_research_tasks;
DROP POLICY IF EXISTS "Service role can manage all research tasks" ON public.deep_research_tasks;

-- 创建新策略
CREATE POLICY "Users can view their own research tasks"
  ON public.deep_research_tasks FOR SELECT
  USING (
    auth.uid() IS NOT NULL
    AND (
      user_id = auth.uid()
      OR conversation_id IN (
        SELECT id FROM public.conversations WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can create their own research tasks"
  ON public.deep_research_tasks FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own research tasks"
  ON public.deep_research_tasks FOR UPDATE
  USING (user_id = auth.uid());

-- 关键: Service Role 完全访问权限（API 使用此角色）
CREATE POLICY "Service role can manage all research tasks"
  ON public.deep_research_tasks FOR ALL
  USING (auth.role() = 'service_role');

-- =============================================
-- STEP 4: 创建辅助函数
-- =============================================

CREATE OR REPLACE FUNCTION public.update_research_progress(
  p_task_id uuid,
  p_status text,
  p_progress_percent integer DEFAULT NULL,
  p_current_step text DEFAULT NULL,
  p_steps_completed integer DEFAULT NULL,
  p_result jsonb DEFAULT NULL,
  p_error_code text DEFAULT NULL,
  p_error_message text DEFAULT NULL,
  p_tokens_prompt integer DEFAULT NULL,
  p_tokens_completion integer DEFAULT NULL,
  p_cost_usd numeric DEFAULT NULL
)
RETURNS void AS $$
DECLARE
  v_updates text[] := array[]::text[];
  v_values text[] := array[]::text[];
BEGIN
  IF p_status IS NOT NULL THEN
    v_updates := array_append(v_updates, 'status = $1');
    v_values := array_append(v_values, p_status);
  END IF;

  IF p_progress_percent IS NOT NULL THEN
    v_updates := array_append(v_updates, 'progress_percent = $2');
    v_values := array_append(v_values, p_progress_percent::text);
  END IF;

  IF p_current_step IS NOT NULL THEN
    v_updates := array_append(v_updates, 'current_step = $3');
    v_values := array_append(v_values, p_current_step);
  END IF;

  IF p_steps_completed IS NOT NULL THEN
    v_updates := array_append(v_updates, 'steps_completed = $4');
    v_values := array_append(v_values, p_steps_completed::text);
  END IF;

  IF p_result IS NOT NULL THEN
    v_updates := array_append(v_updates, 'result = $5');
    v_values := array_append(v_values, p_result::text);
  END IF;

  IF p_error_code IS NOT NULL THEN
    v_updates := array_append(v_updates, 'error_code = $6');
    v_values := array_append(v_values, p_error_code);
  END IF;

  IF p_error_message IS NOT NULL THEN
    v_updates := array_append(v_updates, 'error_message = $7');
    v_values := array_append(v_values, p_error_message);
  END IF;

  IF p_tokens_prompt IS NOT NULL THEN
    v_updates := array_append(v_updates, 'tokens_prompt = $8');
    v_values := array_append(v_values, p_tokens_prompt::text);
  END IF;

  IF p_tokens_completion IS NOT NULL THEN
    v_updates := array_append(v_updates, 'tokens_completion = $9');
    v_values := array_append(v_values, p_tokens_completion::text);
  END IF;

  IF p_cost_usd IS NOT NULL THEN
    v_updates := array_append(v_updates, 'cost_usd = $10');
    v_values := array_append(v_values, p_cost_usd::text);
  END IF;

  v_updates := array_append(v_updates, 'updated_at = timezone(''utc''::text, now())');

  IF array_length(v_updates, 1) > 0 THEN
    EXECUTE format(
      'UPDATE public.deep_research_tasks SET %s WHERE id = $11',
      array_to_string(v_updates, ', ')
    ) USING
      p_status,
      p_progress_percent,
      p_current_step,
      p_steps_completed,
      p_result,
      p_error_code,
      p_error_message,
      p_tokens_prompt,
      p_tokens_completion,
      p_cost_usd,
      p_task_id;
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- STEP 5: 创建分析视图
-- =============================================

CREATE OR REPLACE VIEW public.deep_research_stats_daily AS
SELECT
  date_trunc('day'::text, created_at) AS date,
  user_id,
  status,
  research_depth,
  count(*) AS total_tasks,
  sum(cost_usd) AS total_cost_usd,
  avg(progress_percent) AS avg_progress,
  avg(duration_ms) AS avg_duration_ms,
  sum(tokens_prompt + tokens_completion) AS total_tokens
FROM public.deep_research_tasks
WHERE created_at >= now() - interval '30 days'
GROUP BY
  date_trunc('day'::text, created_at),
  user_id,
  status,
  research_depth
ORDER BY date DESC, total_cost_usd DESC;

CREATE OR REPLACE VIEW public.deep_research_active_tasks AS
SELECT
  id,
  user_id,
  query,
  status,
  progress_percent,
  current_step,
  steps_completed,
  total_steps,
  model_provider,
  created_at,
  started_at,
  (now() - created_at) AS age
FROM public.deep_research_tasks
WHERE status IN ('pending', 'running')
  AND expires_at > now()
ORDER BY created_at DESC;

-- =============================================
-- STEP 6: 验证迁移结果
-- =============================================

DO $$
DECLARE
  table_exists boolean;
  policy_count integer;
BEGIN
  -- 检查表是否存在
  SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'deep_research_tasks'
  ) INTO table_exists;
  
  -- 检查 RLS 策略数量
  SELECT count(*) FROM pg_policies 
  WHERE tablename = 'deep_research_tasks' 
  INTO policy_count;
  
  IF table_exists AND policy_count >= 4 THEN
    RAISE NOTICE '✅ 迁移成功! deep_research_tasks 表已创建，%个 RLS 策略已配置', policy_count;
  ELSE
    RAISE WARNING '⚠️ 迁移可能不完整: 表存在=%，策略数量=%', table_exists, policy_count;
  END IF;
END $$;

-- =============================================
-- 完成!
-- 执行后请运行以下命令验证:
-- curl -s -X GET "https://web3search-api.marovole.workers.dev/api/v1/deep-research"
-- 应该返回 {"tasks":[],"total":0,...} 而不是 500 错误
-- =============================================
