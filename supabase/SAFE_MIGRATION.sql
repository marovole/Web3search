-- =============================================
-- 安全的数据库迁移脚本
-- 此脚本可以安全地重复执行（幂等性）
-- =============================================

BEGIN;

-- =============================================
-- STEP 1: 清理可能冲突的触发器
-- =============================================

DROP TRIGGER IF EXISTS conversations_touch_updated_at ON public.conversations;
DROP TRIGGER IF EXISTS messages_touch_updated_at ON public.messages;
DROP TRIGGER IF EXISTS background_tasks_touch_updated_at ON public.background_tasks;
DROP TRIGGER IF EXISTS deep_research_tasks_touch_updated_at ON public.deep_research_tasks;

-- =============================================
-- STEP 2: 创建或替换函数
-- =============================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = timezone('utc', now());
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- STEP 3: 创建核心表（如果不存在）
-- =============================================

-- 3.1 Conversations Table
CREATE TABLE IF NOT EXISTS public.conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  client_session_id uuid,
  title text,
  summary text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  model_preset text,
  model_config jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived','closed')),
  is_archived boolean NOT NULL DEFAULT false,
  total_messages integer NOT NULL DEFAULT 0,
  total_user_messages integer NOT NULL DEFAULT 0,
  token_usage jsonb NOT NULL DEFAULT '{}'::jsonb,
  last_message_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  deleted_at timestamptz,
  CONSTRAINT conversations_owner_chk CHECK (user_id IS NOT NULL OR client_session_id IS NOT NULL)
);

-- 3.2 Messages Table
CREATE TABLE IF NOT EXISTS public.messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('system','user','assistant','function','tool')),
  content text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  model_id text,
  prompt_tokens integer,
  completion_tokens integer,
  total_tokens integer,
  finish_reason text,
  tool_calls jsonb,
  function_call jsonb,
  error_message text,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

-- 3.3 Projects Table
CREATE TABLE IF NOT EXISTS public.projects (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(20) UNIQUE NOT NULL,
  name VARCHAR(200) NOT NULL,
  coingecko_id VARCHAR(100) UNIQUE,
  description TEXT,
  blockchain VARCHAR(50),
  categories JSONB DEFAULT '[]',
  tags JSONB DEFAULT '[]',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3.4 Background Tasks Table
CREATE TABLE IF NOT EXISTS public.background_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_type text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','failed','cancelled')),
  priority integer NOT NULL DEFAULT 0,
  max_retries integer NOT NULL DEFAULT 3,
  retry_count integer NOT NULL DEFAULT 0,
  scheduled_at timestamptz,
  started_at timestamptz,
  completed_at timestamptz,
  error_message text,
  result jsonb,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

-- 3.5 Deep Research Tasks Table
CREATE TABLE IF NOT EXISTS public.deep_research_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text NOT NULL,
  query text NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','failed','cancelled')),
  progress_percent integer NOT NULL DEFAULT 0,
  current_step text,
  model_id text,
  model_provider text,
  result jsonb,
  error_message text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  completed_at timestamptz
);

-- 3.6 Reports Table
CREATE TABLE IF NOT EXISTS public.reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  project_id integer REFERENCES public.projects(id) ON DELETE CASCADE,
  title text NOT NULL,
  content text NOT NULL,
  report_type text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  is_public boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

-- 3.7 API Calls Telemetry Table
CREATE TABLE IF NOT EXISTS public.api_calls_telemetry (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  endpoint text NOT NULL,
  method text NOT NULL,
  status_code integer NOT NULL,
  duration_ms integer NOT NULL,
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  ip_address inet,
  user_agent text,
  error_message text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

-- =============================================
-- STEP 4: 创建索引（如果不存在）
-- =============================================

-- Conversations indexes
CREATE INDEX IF NOT EXISTS conversations_user_updated_idx
  ON public.conversations (user_id, updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS conversations_session_updated_idx
  ON public.conversations (client_session_id, updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS conversations_deleted_idx
  ON public.conversations (deleted_at) WHERE deleted_at IS NOT NULL;

-- Messages indexes
CREATE INDEX IF NOT EXISTS messages_conversation_created_idx
  ON public.messages (conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS messages_role_idx
  ON public.messages (role);

-- Projects indexes
CREATE INDEX IF NOT EXISTS ix_projects_symbol ON public.projects(symbol);
CREATE INDEX IF NOT EXISTS ix_projects_coingecko_id ON public.projects(coingecko_id);

-- Background tasks indexes
CREATE INDEX IF NOT EXISTS background_tasks_status_idx
  ON public.background_tasks (status, scheduled_at);
CREATE INDEX IF NOT EXISTS background_tasks_type_status_idx
  ON public.background_tasks (task_type, status);

-- Deep research tasks indexes
CREATE INDEX IF NOT EXISTS deep_research_tasks_status_idx
  ON public.deep_research_tasks (status, created_at DESC);
CREATE INDEX IF NOT EXISTS deep_research_tasks_symbol_idx
  ON public.deep_research_tasks (symbol, created_at DESC);

-- API telemetry indexes
CREATE INDEX IF NOT EXISTS api_calls_endpoint_idx
  ON public.api_calls_telemetry (endpoint, created_at DESC);
CREATE INDEX IF NOT EXISTS api_calls_created_idx
  ON public.api_calls_telemetry (created_at DESC);

-- =============================================
-- STEP 5: 重新创建触发器
-- =============================================

CREATE TRIGGER conversations_touch_updated_at
  BEFORE UPDATE ON public.conversations
  FOR EACH ROW
  EXECUTE FUNCTION public.touch_updated_at();

CREATE TRIGGER messages_touch_updated_at
  BEFORE UPDATE ON public.messages
  FOR EACH ROW
  EXECUTE FUNCTION public.touch_updated_at();

CREATE TRIGGER background_tasks_touch_updated_at
  BEFORE UPDATE ON public.background_tasks
  FOR EACH ROW
  EXECUTE FUNCTION public.touch_updated_at();

CREATE TRIGGER deep_research_tasks_touch_updated_at
  BEFORE UPDATE ON public.deep_research_tasks
  FOR EACH ROW
  EXECUTE FUNCTION public.touch_updated_at();

-- =============================================
-- STEP 6: 启用行级安全（RLS）
-- =============================================

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

-- 允许所有认证用户读取公开报告
DROP POLICY IF EXISTS "reports_public_read" ON public.reports;
CREATE POLICY "reports_public_read" ON public.reports
  FOR SELECT
  USING (is_public = true);

-- 允许用户读取自己的对话
DROP POLICY IF EXISTS "conversations_user_read" ON public.conversations;
CREATE POLICY "conversations_user_read" ON public.conversations
  FOR SELECT
  USING (
    user_id = auth.uid()
    OR client_session_id IS NOT NULL
  );

-- 允许用户创建对话
DROP POLICY IF EXISTS "conversations_user_insert" ON public.conversations;
CREATE POLICY "conversations_user_insert" ON public.conversations
  FOR INSERT
  WITH CHECK (
    user_id = auth.uid()
    OR user_id IS NULL
  );

-- =============================================
-- STEP 7: 插入测试数据（可选）
-- =============================================

-- 插入Bitcoin项目（如果不存在）
INSERT INTO public.projects (symbol, name, coingecko_id, description, blockchain, categories, tags)
VALUES (
  'BTC',
  'Bitcoin',
  'bitcoin',
  'Bitcoin is a decentralized digital currency',
  'Bitcoin',
  '["Currency"]'::jsonb,
  '["pow","store-of-value"]'::jsonb
)
ON CONFLICT (symbol) DO NOTHING;

-- 插入Ethereum项目（如果不存在）
INSERT INTO public.projects (symbol, name, coingecko_id, description, blockchain, categories, tags)
VALUES (
  'ETH',
  'Ethereum',
  'ethereum',
  'Ethereum is a decentralized platform for smart contracts',
  'Ethereum',
  '["Platform"]'::jsonb,
  '["smart-contracts","defi"]'::jsonb
)
ON CONFLICT (symbol) DO NOTHING;

COMMIT;

-- =============================================
-- 验证查询
-- =============================================

-- 查看所有创建的表
SELECT
  schemaname,
  tablename,
  tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 查看conversations表结构
SELECT
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'conversations'
ORDER BY ordinal_position;
