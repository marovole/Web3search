-- migrations/20251110_create_deep_research_tasks.sql
-- Deep Research async task management
-- Part of Week 2 T11: Deep Research async pipeline

begin;

create extension if not exists "pgcrypto";

-- Deep Research Tasks Table
create table if not exists public.deep_research_tasks (
  id uuid primary key default gen_random_uuid(),

  -- Task metadata
  user_id uuid references auth.users(id) on delete cascade,
  client_session_id uuid,
  conversation_id uuid references public.conversations(id) on delete cascade,

  -- Task details
  query text not null,
  status text not null default 'pending' check (status in ('pending', 'running', 'completed', 'failed', 'cancelled')),

  -- Research configuration
  research_depth text not null default 'standard' check (research_depth in ('quick', 'standard', 'comprehensive')),
  max_sources integer not null default 10,
  focus_areas text[],

  -- Model configuration
  model_id text,
  model_provider text check (model_provider in ('qwen', 'deepseek', 'anthropic', 'openai')),
  temperature numeric(3,2) default 0.7,

  -- Results
  result jsonb,
  summary text,
  answer text,
  sources jsonb not null default '[]'::jsonb,
  citations jsonb not null default '[]'::jsonb,

  -- Progress tracking
  progress_percent integer not null default 0 check (progress_percent between 0 and 100),
  current_step text,
  steps_completed integer not null default 0,
  total_steps integer not null default 1,

  -- Performance metrics
  tokens_prompt integer not null default 0,
  tokens_completion integer not null default 0,
  cost_usd numeric(12,6) not null default 0,
  started_at timestamptz,
  completed_at timestamptz,
  duration_ms integer,

  -- Error tracking
  error_code text,
  error_message text,
  retry_count integer not null default 0,

  -- Timestamps
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  expires_at timestamptz not null default (timezone('utc', now()) + interval '24 hours'),

  -- Metadata
  metadata jsonb not null default '{}'::jsonb,
  tags text[]
);

-- Indexes for query performance

create index if not exists deep_research_tasks_user_idx
  on public.deep_research_tasks (user_id, created_at desc)
  where user_id is not null;

create index if not exists deep_research_tasks_session_idx
  on public.deep_research_tasks (client_session_id, created_at desc)
  where client_session_id is not null;

create index if not exists deep_research_tasks_status_idx
  on public.deep_research_tasks (status, created_at desc);

create index if not exists deep_research_tasks_conversation_idx
  on public.deep_research_tasks (conversation_id, created_at desc)
  where conversation_id is not null;

create index if not exists deep_research_tasks_expires_idx
  on public.deep_research_tasks (expires_at)
  where status in ('pending', 'running');

-- Partial indexes for common filters

create index if not exists deep_research_tasks_pending_idx
  on public.deep_research_tasks (created_at)
  where status = 'pending';

create index if not exists deep_research_tasks_running_idx
  on public.deep_research_tasks (user_id, created_at)
  where status = 'running';

create index if not exists deep_research_tasks_completed_idx
  on public.deep_research_tasks (user_id, created_at desc)
  where status = 'completed';

-- Enable Row Level Security

alter table public.deep_research_tasks enable row level security;

-- RLS Policies

create policy "Users can view their own research tasks"
  on public.deep_research_tasks for select
  using (
    auth.uid() is not null
    and (
      user_id = auth.uid()
      or conversation_id in (
        select id from public.conversations where user_id = auth.uid()
      )
    )
  );

create policy "Users can create their own research tasks"
  on public.deep_research_tasks for insert
  with check (user_id = auth.uid());

create policy "Users can update their own research tasks"
  on public.deep_research_tasks for update
  using (user_id = auth.uid());

create policy "Service role can manage all research tasks"
  on public.deep_research_tasks for all
  using (auth.role() = 'service_role');

-- Functions for task management

create or replace function public.update_research_progress(
  p_task_id uuid,
  p_status text,
  p_progress_percent integer default null,
  p_current_step text default null,
  p_steps_completed integer default null,
  p_result jsonb default null,
  p_error_code text default null,
  p_error_message text default null,
  p_tokens_prompt integer default null,
  p_tokens_completion integer default null,
  p_cost_usd numeric default null
)
returns void as $$
declare
  v_updates text[] := array[]::text[];
  v_values text[] := array[]::text[];
begin
  -- Build dynamic update statement
  if p_status is not null then
    v_updates := array_append(v_updates, 'status = $1');
    v_values := array_append(v_values, p_status);
  end if;

  if p_progress_percent is not null then
    v_updates := array_append(v_updates, 'progress_percent = $2');
    v_values := array_append(v_values, p_progress_percent::text);
  end if;

  if p_current_step is not null then
    v_updates := array_append(v_updates, 'current_step = $3');
    v_values := array_append(v_values, p_current_step);
  end if;

  if p_steps_completed is not null then
    v_updates := array_append(v_updates, 'steps_completed = $4');
    v_values := array_append(v_values, p_steps_completed::text);
  end if;

  if p_result is not null then
    v_updates := array_append(v_updates, 'result = $5');
    v_values := array_append(v_values, p_result::text);
  end if;

  if p_error_code is not null then
    v_updates := array_append(v_updates, 'error_code = $6');
    v_values := array_append(v_values, p_error_code);
  end if;

  if p_error_message is not null then
    v_updates := array_append(v_updates, 'error_message = $7');
    v_values := array_append(v_values, p_error_message);
  end if;

  if p_tokens_prompt is not null then
    v_updates := array_append(v_updates, 'tokens_prompt = $8');
    v_values := array_append(v_values, p_tokens_prompt::text);
  end if;

  if p_tokens_completion is not null then
    v_updates := array_append(v_updates, 'tokens_completion = $9');
    v_values := array_append(v_values, p_tokens_completion::text);
  end if;

  if p_cost_usd is not null then
    v_updates := array_append(v_updates, 'cost_usd = $10');
    v_values := array_append(v_values, p_cost_usd::text);
  end if;

  -- Always update the updated_at timestamp
  v_updates := array_append(v_updates, 'updated_at = timezone(''utc''::text, now())');

  -- Execute the update
  if array_length(v_updates, 1) > 0 then
    execute format(
      'update public.deep_research_tasks set %s where id = $11',
      array_to_string(v_updates, ', ')
    ) using
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
  end if;
end;
$$ language plpgsql security definer;

-- Views for analytics

create or replace view public.deep_research_stats_daily as
select
  date_trunc('day'::text, created_at) as date,
  user_id,
  status,
  research_depth,
  count(*) as total_tasks,
  sum(cost_usd) as total_cost_usd,
  avg(progress_percent) as avg_progress,
  avg(duration_ms) as avg_duration_ms,
  sum(tokens_prompt + tokens_completion) as total_tokens
from public.deep_research_tasks
where created_at >= now() - interval '30 days'
group by
  date_trunc('day'::text, created_at),
  user_id,
  status,
  research_depth
order by date desc, total_cost_usd desc;

create or replace view public.deep_research_active_tasks as
select
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
  (now() - created_at) as age
from public.deep_research_tasks
where status in ('pending', 'running')
  and expires_at > now()
order by created_at desc;

commit;
