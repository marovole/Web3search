-- =============================================
-- 清理并重建数据库脚本
-- 此脚本会先删除所有表，然后重新创建
-- ⚠️ 警告：会删除所有数据！
-- =============================================

-- 开始事务
BEGIN;

-- =============================================
-- STEP 1: 删除所有可能存在的表（按依赖顺序）
-- =============================================

-- 先删除依赖其他表的表
DROP TABLE IF EXISTS public.api_calls_telemetry CASCADE;
DROP TABLE IF EXISTS public.reports CASCADE;
DROP TABLE IF EXISTS public.messages CASCADE;
DROP TABLE IF EXISTS public.deep_research_tasks CASCADE;
DROP TABLE IF EXISTS public.background_tasks CASCADE;
DROP TABLE IF EXISTS public.conversations CASCADE;
DROP TABLE IF EXISTS public.project_snapshots CASCADE;
DROP TABLE IF EXISTS public.projects CASCADE;

-- 删除函数
DROP FUNCTION IF EXISTS public.touch_updated_at() CASCADE;

-- =============================================
-- STEP 2: 创建扩展和函数
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
-- STEP 3: 创建所有表
-- =============================================

-- 3.1 Projects Table
CREATE TABLE public.projects (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(20) UNIQUE NOT NULL,
  name VARCHAR(200) NOT NULL,
  coingecko_id VARCHAR(100) UNIQUE,
  description TEXT,
  blockchain VARCHAR(50),
  categories JSONB DEFAULT '[]'::jsonb,
  tags JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3.2 Conversations Table
CREATE TABLE public.conversations (
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

-- 3.3 Messages Table
CREATE TABLE public.messages (
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

-- 3.4 Background Tasks Table
CREATE TABLE public.background_tasks (
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
CREATE TABLE public.deep_research_tasks (
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
CREATE TABLE public.reports (
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
CREATE TABLE public.api_calls_telemetry (
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
-- STEP 4: 创建索引
-- =============================================

-- Projects indexes
CREATE INDEX ix_projects_symbol ON public.projects(symbol);
CREATE INDEX ix_projects_coingecko_id ON public.projects(coingecko_id);

-- Conversations indexes
CREATE INDEX conversations_user_updated_idx
  ON public.conversations (user_id, updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX conversations_session_updated_idx
  ON public.conversations (client_session_id, updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX conversations_deleted_idx
  ON public.conversations (deleted_at) WHERE deleted_at IS NOT NULL;

-- Messages indexes
CREATE INDEX messages_conversation_created_idx
  ON public.messages (conversation_id, created_at DESC);
CREATE INDEX messages_role_idx
  ON public.messages (role);

-- Background tasks indexes
CREATE INDEX background_tasks_status_idx
  ON public.background_tasks (status, scheduled_at);
CREATE INDEX background_tasks_type_status_idx
  ON public.background_tasks (task_type, status);

-- Deep research tasks indexes
CREATE INDEX deep_research_tasks_status_idx
  ON public.deep_research_tasks (status, created_at DESC);
CREATE INDEX deep_research_tasks_symbol_idx
  ON public.deep_research_tasks (symbol, created_at DESC);

-- API telemetry indexes
CREATE INDEX api_calls_endpoint_idx
  ON public.api_calls_telemetry (endpoint, created_at DESC);
CREATE INDEX api_calls_created_idx
  ON public.api_calls_telemetry (created_at DESC);

-- =============================================
-- STEP 5: 创建触发器
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
-- STEP 6: 配置行级安全
-- =============================================

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略
CREATE POLICY "reports_public_read" ON public.reports
  FOR SELECT
  USING (is_public = true);

CREATE POLICY "conversations_user_read" ON public.conversations
  FOR SELECT
  USING (
    user_id = auth.uid()
    OR client_session_id IS NOT NULL
  );

CREATE POLICY "conversations_user_insert" ON public.conversations
  FOR INSERT
  WITH CHECK (
    user_id = auth.uid()
    OR user_id IS NULL
  );

-- =============================================
-- STEP 7: 插入测试数据
-- =============================================

INSERT INTO public.projects (symbol, name, coingecko_id, description, blockchain, categories, tags)
VALUES
  (
    'BTC',
    'Bitcoin',
    'bitcoin',
    'Bitcoin is a decentralized digital currency',
    'Bitcoin',
    '["Currency"]'::jsonb,
    '["pow","store-of-value"]'::jsonb
  ),
  (
    'ETH',
    'Ethereum',
    'ethereum',
    'Ethereum is a decentralized platform for smart contracts',
    'Ethereum',
    '["Platform"]'::jsonb,
    '["smart-contracts","defi"]'::jsonb
  );

-- 提交事务
COMMIT;

-- =============================================
-- STEP 8: 验证结果
-- =============================================

-- 显示所有创建的表
SELECT
  '✅ 表已创建' as status,
  tablename as table_name
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'projects',
    'conversations',
    'messages',
    'background_tasks',
    'deep_research_tasks',
    'reports',
    'api_calls_telemetry'
  )
ORDER BY tablename;

-- 显示数据统计
SELECT '📊 数据统计' as info, 'projects' as table_name, COUNT(*) as count FROM public.projects
UNION ALL
SELECT '📊 数据统计', 'conversations', COUNT(*) FROM public.conversations
UNION ALL
SELECT '📊 数据统计', 'messages', COUNT(*) FROM public.messages;

-- 显示项目数据
SELECT
  '🪙 项目数据' as info,
  symbol,
  name
FROM public.projects
ORDER BY symbol;
