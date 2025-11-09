-- migrations/20251110_create_api_calls_telemetry.sql
-- API call telemetry for OpenRouter integration
-- Part of Week 2 T6: Call Telemetry and Billing Logs

begin;

create extension if not exists "pgcrypto";

-- Enhanced api_calls table for comprehensive logging
create table if not exists public.api_calls (
  id uuid primary key default gen_random_uuid(),

  -- Request metadata
  conversation_id uuid references public.conversations(id) on delete set null,
  message_id uuid references public.messages(id) on delete set null,
  client_session_id uuid,
  user_id uuid references auth.users(id) on delete set null,

  -- Routing information
  model_id text not null,
  model_name text not null,
  provider text not null check (provider in ('qwen', 'deepseek', 'anthropic', 'openai', 'other')),
  use_case text check (use_case in ('quick-chat', 'deep-research', 'summarization', 'code-assist', 'other')),

  -- Request details
  request_method text not null,
  request_path text not null,
  request_headers jsonb not null default '{}'::jsonb,
  request_body jsonb,
  prompt_tokens integer not null default 0,

  -- Response details
  response_status integer,
  response_headers jsonb,
  response_body jsonb,
  completion_tokens integer not null default 0,
  finish_reason text,

  -- Error tracking
  error_code text,
  error_message text,
  error_details jsonb,

  -- Performance metrics
  latency_ms integer not null default 0,
  retry_count integer not null default 0,
  circuit_state text check (circuit_state in ('closed', 'open', 'half_open')),

  -- Cost tracking
  cost_usd numeric(12,6) not null default 0,
  cost_currency text default 'USD',

  -- Metadata fields
  metadata jsonb not null default '{}'::jsonb,
  tags text[],

  -- Security and compliance
  ip_address inet,
  country_code text,
  user_agent text,

  -- Timestamps
  created_at timestamptz not null default timezone('utc', now()),
  started_at timestamptz,
  completed_at timestamptz
);

-- Indexes for query performance

create index if not exists api_calls_conversation_idx
  on public.api_calls (conversation_id, created_at desc)
  where conversation_id is not null;

create index if not exists api_calls_user_idx
  on public.api_calls (user_id, created_at desc)
  where user_id is not null;

create index if not exists api_calls_session_idx
  on public.api_calls (client_session_id, created_at desc)
  where client_session_id is not null;

create index if not exists api_calls_model_idx
  on public.api_calls (model_id, created_at desc);

create index if not exists api_calls_provider_idx
  on public.api_calls (provider, created_at desc);

create index if not exists api_calls_use_case_idx
  on public.api_calls (use_case, created_at desc)
  where use_case is not null;

create index if not exists api_calls_latency_idx
  on public.api_calls (latency_ms desc)
  where latency_ms > 0;

create index if not exists api_calls_cost_idx
  on public.api_calls (cost_usd desc)
  where cost_usd > 0;

create index if not exists api_calls_error_idx
  on public.api_calls (error_code, created_at desc)
  where error_code is not null;

create index if not exists api_calls_date_idx
  on public.api_calls (date_trunc('hour'::text, created_at) desc);

-- Cost analysis indexes

create index if not exists api_calls_daily_cost_idx
  on public.api_calls (date_trunc('day'::text, created_at), provider)
  where cost_usd > 0;

-- Security and compliance indexes

create index if not exists api_calls_ip_idx
  on public.api_calls (ip_address, created_at desc)
  where ip_address is not null;

create index if not exists api_calls_country_idx
  on public.api_calls (country_code, created_at desc)
  where country_code is not null;

-- Partial indexes for common queries

create index if not exists api_calls_success_idx
  on public.api_calls (created_at desc)
  where response_status between 200 and 299;

create index if not exists api_calls_errors_idx
  on public.api_calls (created_at desc)
  where response_status not between 200 and 299 or error_code is not null;

-- Enable Row Level Security

alter table public.api_calls enable row level security;

-- RLS Policies

create policy "Users can view their own API calls"
  on public.api_calls for select
  using (
    auth.uid() is not null
    and (
      user_id = auth.uid()
      or conversation_id in (
        select id from public.conversations where user_id = auth.uid()
      )
    )
  );

create policy "Service role can manage all API calls"
  on public.api_calls for all
  using (auth.role() = 'service_role');

-- Views for analytics

create or replace view public.api_calls_daily_summary as
select
  date_trunc('day'::text, created_at) as date,
  provider,
  model_name,
  use_case,
  count(*) as total_requests,
  count(case when response_status between 200 and 299 then 1 end) as successful_requests,
  count(case when response_status not between 200 and 299 then 1 end) as failed_requests,
  sum(prompt_tokens) as total_prompt_tokens,
  sum(completion_tokens) as total_completion_tokens,
  sum(cost_usd) as total_cost_usd,
  avg(latency_ms) as avg_latency_ms,
  percentile_cont(0.5) within group (order by latency_ms) as p50_latency_ms,
  percentile_cont(0.95) within group (order by latency_ms) as p95_latency_ms,
  percentile_cont(0.99) within group (order by latency_ms) as p99_latency_ms
from public.api_calls
where created_at >= now() - interval '30 days'
group by
  date_trunc('day'::text, created_at),
  provider,
  model_name,
  use_case
order by
  date desc,
  total_cost_usd desc;

create or replace view public.api_calls_hourly_errors as
select
  date_trunc('hour'::text, created_at) as hour,
  error_code,
  model_name,
  count(*) as error_count,
  avg(latency_ms) as avg_latency_ms
from public.api_calls
where
  error_code is not null
  and created_at >= now() - interval '24 hours'
group by
  date_trunc('hour'::text, created_at),
  error_code,
  model_name
order by
  hour desc,
  error_count desc;

create or replace view public.api_cost_by_user as
select
  user_id,
  date_trunc('day'::text, created_at) as date,
  sum(cost_usd) as total_cost_usd,
  count(*) as total_requests,
  avg(latency_ms) as avg_latency_ms
from public.api_calls
where
  user_id is not null
  and created_at >= now() - interval '30 days'
group by
  user_id,
  date_trunc('day'::text, created_at)
order by
  date desc,
  total_cost_usd desc;

-- Functions for analytics

create or replace function public.get_api_usage_stats(
  start_date timestamptz,
  end_date timestamptz
)
returns table (
  provider text,
  total_requests bigint,
  avg_latency_ms numeric,
  total_cost_usd numeric,
  error_rate numeric
) as $$
begin
  return query
  select
    ac.provider,
    count(*) as total_requests,
    avg(ac.latency_ms)::numeric(10,2) as avg_latency_ms,
    sum(ac.cost_usd)::numeric(12,6) as total_cost_usd,
    (count(case when ac.response_status not between 200 and 299 then 1 end)::numeric /
      count(*)::numeric * 100)::numeric(5,2) as error_rate
  from public.api_calls ac
  where
    ac.created_at >= start_date
    and ac.created_at <= end_date
  group by ac.provider
  order by total_cost_usd desc;
end;
$$ language plpgsql stable;

create or replace function public.track_api_call(
  p_conversation_id uuid,
  p_message_id uuid,
  p_client_session_id uuid,
  p_model_id text,
  p_model_name text,
  p_provider text,
  p_use_case text,
  p_request_method text,
  p_request_path text,
  p_request_headers jsonb,
  p_request_body jsonb,
  p_prompt_tokens integer,
  p_response_status integer,
  p_response_headers jsonb,
  p_response_body jsonb,
  p_completion_tokens integer,
  p_finish_reason text,
  p_error_code text,
  p_error_message text,
  p_error_details jsonb,
  p_latency_ms integer,
  p_retry_count integer,
  p_circuit_state text,
  p_cost_usd numeric,
  p_metadata jsonb,
  p_tags text[],
  p_ip_address text,
  p_country_code text,
  p_user_agent text,
  p_started_at timestamptz,
  p_completed_at timestamptz
)
returns uuid as $$
declare
  v_call_id uuid;
begin
  insert into public.api_calls (
    conversation_id,
    message_id,
    client_session_id,
    user_id,
    model_id,
    model_name,
    provider,
    use_case,
    request_method,
    request_path,
    request_headers,
    request_body,
    prompt_tokens,
    response_status,
    response_headers,
    response_body,
    completion_tokens,
    finish_reason,
    error_code,
    error_message,
    error_details,
    latency_ms,
    retry_count,
    circuit_state,
    cost_usd,
    metadata,
    tags,
    ip_address,
    country_code,
    user_agent,
    started_at,
    completed_at
  )
  values (
    p_conversation_id,
    p_message_id,
    p_client_session_id,
    auth.uid(),
    p_model_id,
    p_model_name,
    p_provider,
    p_use_case,
    p_request_method,
    p_request_path,
    p_request_headers,
    p_request_body,
    p_prompt_tokens,
    p_response_status,
    p_response_headers,
    p_response_body,
    p_completion_tokens,
    p_finish_reason,
    p_error_code,
    p_error_message,
    p_error_details,
    p_latency_ms,
    p_retry_count,
    p_circuit_state,
    p_cost_usd,
    p_metadata,
    p_tags,
    nullif(p_ip_address, '')::inet,
    p_country_code,
    p_user_agent,
    p_started_at,
    p_completed_at
  )
  returning id into v_call_id;

  return v_call_id;
end;
$$ language plpgsql security definer;

commit;
