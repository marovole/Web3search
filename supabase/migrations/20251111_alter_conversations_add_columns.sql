-- migrations/20251111_alter_conversations_add_columns.sql
-- Reconcile the production conversations schema with the expected structure and fix the RLS policy conflicts.

begin;

alter table if exists public.conversations
  add column if not exists client_session_id uuid,
  add column if not exists summary text,
  add column if not exists metadata jsonb not null default '{}'::jsonb,
  add column if not exists model_preset text,
  add column if not exists model_config jsonb not null default '{}'::jsonb,
  add column if not exists status text not null default 'active' check (status in ('active','archived','closed')),
  add column if not exists is_archived boolean not null default false,
  add column if not exists total_messages integer not null default 0,
  add column if not exists total_user_messages integer not null default 0,
  add column if not exists token_usage jsonb not null default '{}'::jsonb,
  add column if not exists last_message_at timestamptz,
  add column if not exists deleted_at timestamptz;

create index if not exists conversations_user_updated_idx
  on public.conversations (user_id, updated_at desc)
  where deleted_at is null;

create index if not exists conversations_session_updated_idx
  on public.conversations (client_session_id, updated_at desc)
  where deleted_at is null;

create index if not exists conversations_last_message_idx
  on public.conversations (last_message_at desc)
  where deleted_at is null;

drop trigger if exists conversations_touch_updated_at on public.conversations;
create trigger conversations_touch_updated_at
  before update on public.conversations
  for each row execute function public.touch_updated_at();

alter table if exists public.deep_research_tasks enable row level security;
drop policy if exists "Users can view their own research tasks" on public.deep_research_tasks;
drop policy if exists "Users can create their own research tasks" on public.deep_research_tasks;
drop policy if exists "Users can update their own research tasks" on public.deep_research_tasks;
drop policy if exists "Service role can manage all research tasks" on public.deep_research_tasks;

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

commit;
