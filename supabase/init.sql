-- Web3search Supabase 初始化脚本
-- 在 Supabase Dashboard 的 SQL Editor 中运行此脚本

-- ============================================
-- 扩展
-- ============================================
create extension if not exists "pgcrypto";

-- ============================================
-- Conversations 表（聊天会话）
-- ============================================
create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete set null,
  client_session_id uuid,
  title text,
  summary text,
  metadata jsonb not null default '{}'::jsonb,
  model_preset text,
  model_config jsonb not null default '{}'::jsonb,
  status text not null default 'active' check (status in ('active','archived','closed')),
  is_archived boolean not null default false,
  total_messages integer not null default 0,
  total_user_messages integer not null default 0,
  token_usage jsonb not null default '{}'::jsonb,
  last_message_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  deleted_at timestamptz,
  constraint conversations_owner_chk check (user_id is not null or client_session_id is not null)
);

create index if not exists conversations_user_updated_idx
  on public.conversations (user_id, updated_at desc) where deleted_at is null;

create index if not exists conversations_session_updated_idx
  on public.conversations (client_session_id, updated_at desc) where deleted_at is null;

-- ============================================
-- Messages 表（聊天消息）
-- ============================================
create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  seq bigint generated always as identity,
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  parent_message_id uuid references public.messages(id) on delete set null,
  user_id uuid references auth.users(id) on delete set null,
  role text not null check (role in ('system','user','assistant','tool')),
  status text not null default 'pending' check (status in ('pending','streaming','completed','failed')),
  segment_index integer not null default 0,
  is_final boolean not null default false,
  content text,
  content_delta jsonb,
  content_json jsonb,
  metadata jsonb not null default '{}'::jsonb,
  model text,
  model_parameters jsonb,
  tool_name text,
  tool_call_id text,
  error_message text,
  token_count_prompt integer not null default 0,
  token_count_completion integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  deleted_at timestamptz
);

create index if not exists messages_conversation_seq_idx
  on public.messages (conversation_id, seq desc);

create index if not exists messages_conversation_created_idx
  on public.messages (conversation_id, created_at desc) where deleted_at is null;

create index if not exists messages_status_pending_idx
  on public.messages (status) where status in ('pending','streaming');

-- ============================================
-- Deep Research Tasks 表
-- ============================================
create table if not exists public.deep_research_tasks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  client_session_id uuid,
  conversation_id uuid references public.conversations(id) on delete cascade,
  query text not null,
  status text not null default 'pending' check (status in ('pending', 'running', 'completed', 'failed', 'cancelled')),
  research_depth text not null default 'standard' check (research_depth in ('quick', 'standard', 'comprehensive')),
  max_sources integer not null default 10,
  focus_areas text[],
  model_id text,
  model_provider text check (model_provider in ('qwen', 'deepseek', 'anthropic', 'openai')),
  temperature numeric(3,2) default 0.7,
  result jsonb,
  summary text,
  answer text,
  sources jsonb not null default '[]'::jsonb,
  citations jsonb not null default '[]'::jsonb,
  progress_percent integer not null default 0 check (progress_percent between 0 and 100),
  current_step text,
  steps_completed integer not null default 0,
  total_steps integer not null default 1,
  tokens_prompt integer not null default 0,
  tokens_completion integer not null default 0,
  cost_usd numeric(12,6) not null default 0,
  started_at timestamptz,
  completed_at timestamptz,
  duration_ms integer,
  error_code text,
  error_message text,
  retry_count integer not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  expires_at timestamptz not null default (timezone('utc', now()) + interval '24 hours'),
  metadata jsonb not null default '{}'::jsonb,
  tags text[]
);

create index if not exists deep_research_tasks_status_idx
  on public.deep_research_tasks (status, created_at desc);

create index if not exists deep_research_tasks_user_idx
  on public.deep_research_tasks (user_id, created_at desc)
  where user_id is not null;

-- ============================================
-- Reports 表
-- ============================================
create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  topic text not null,
  sections jsonb not null,
  content jsonb not null,
  metadata jsonb,
  user_id uuid,
  status text not null default 'completed' check (status in ('generating', 'completed', 'failed')),
  created_at timestamptz not null default current_timestamp,
  updated_at timestamptz not null default current_timestamp
);

create index if not exists reports_created_at_idx
  on public.reports (created_at desc);

create index if not exists reports_status_idx
  on public.reports (status);

-- ============================================
-- API Calls Telemetry 表（可选，用于监控）
-- ============================================
create table if not exists public.api_calls_telemetry (
  id uuid primary key default gen_random_uuid(),
  endpoint text not null,
  method text not null,
  provider text,
  model text,
  status_code integer,
  latency_ms integer,
  tokens_prompt integer,
  tokens_completion integer,
  cost_usd numeric(12,6),
  error_message text,
  metadata jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists api_calls_telemetry_created_idx
  on public.api_calls_telemetry (created_at desc);

create index if not exists api_calls_telemetry_endpoint_idx
  on public.api_calls_telemetry (endpoint, created_at desc);

-- ============================================
-- Healthcheck Events 表
-- ============================================
create table if not exists public.healthcheck_events (
  id uuid primary key default gen_random_uuid(),
  check_name text not null,
  status text not null check (status in ('healthy', 'degraded', 'down')),
  latency_ms integer,
  error_message text,
  details jsonb,
  observed_at timestamptz not null default timezone('utc', now())
);

create index if not exists healthcheck_events_observed_idx
  on public.healthcheck_events (observed_at desc);

create index if not exists healthcheck_events_check_name_idx
  on public.healthcheck_events (check_name, observed_at desc);

-- ============================================
-- 辅助函数
-- ============================================
create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$ language plpgsql;

create trigger conversations_touch_updated_at
  before update on public.conversations
  for each row execute function public.touch_updated_at();

create trigger messages_touch_updated_at
  before update on public.messages
  for each row execute function public.touch_updated_at();

create trigger deep_research_tasks_touch_updated_at
  before update on public.deep_research_tasks
  for each row execute function public.touch_updated_at();

create trigger reports_touch_updated_at
  before update on public.reports
  for each row execute function public.touch_updated_at();

-- ============================================
-- RLS 策略（允许 service_role 完全访问）
-- ============================================
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.deep_research_tasks enable row level security;
alter table public.reports enable row level security;
alter table public.api_calls_telemetry enable row level security;
alter table public.healthcheck_events enable row level security;

-- service_role 可以访问所有表
create policy "Service role can access conversations"
  on public.conversations for all using (auth.role() = 'service_role');

create policy "Service role can access messages"
  on public.messages for all using (auth.role() = 'service_role');

create policy "Service role can access deep_research_tasks"
  on public.deep_research_tasks for all using (auth.role() = 'service_role');

create policy "Service role can access reports"
  on public.reports for all using (auth.role() = 'service_role');

create policy "Service role can access api_calls_telemetry"
  on public.api_calls_telemetry for all using (auth.role() = 'service_role');

create policy "Service role can access healthcheck_events"
  on public.healthcheck_events for all using (auth.role() = 'service_role');

-- ============================================
-- 验证
-- ============================================
select 'Tables created successfully!' as status;
select table_name from information_schema.tables where schema_name = 'public' order by table_name;
