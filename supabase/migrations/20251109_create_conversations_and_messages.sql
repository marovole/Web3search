-- migrations/20251109_create_conversations_and_messages.sql
-- chat history schema for Supabase + Workers architecture
-- Part of Week 2 T12: Message Storage Extension

begin;

create extension if not exists "pgcrypto";

create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$ language plpgsql;

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

create index if not exists conversations_last_message_idx
  on public.conversations (last_message_at desc) where deleted_at is null;

create trigger conversations_touch_updated_at
  before update on public.conversations
  for each row execute function public.touch_updated_at();

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
  deleted_at timestamptz,
  constraint messages_content_presence check (
    content is not null or content_json is not null or content_delta is not null
  )
);

create index if not exists messages_conversation_seq_idx
  on public.messages (conversation_id, seq desc);

create index if not exists messages_conversation_created_idx
  on public.messages (conversation_id, created_at desc) where deleted_at is null;

create index if not exists messages_user_created_idx
  on public.messages (user_id, created_at desc) where user_id is not null and deleted_at is null;

create index if not exists messages_parent_segment_idx
  on public.messages (parent_message_id, segment_index) where parent_message_id is not null;

create index if not exists messages_status_pending_idx
  on public.messages (status) where status in ('pending','streaming');

create trigger messages_touch_updated_at
  before update on public.messages
  for each row execute function public.touch_updated_at();

create or replace function public.bump_conversation_counters()
returns trigger as $$
declare
  target uuid := coalesce(new.conversation_id, old.conversation_id);
begin
  if tg_op = 'INSERT' then
    update public.conversations
       set total_messages = total_messages + 1,
           total_user_messages = total_user_messages + case when new.role = 'user' then 1 else 0 end,
           last_message_at = greatest(coalesce(last_message_at, new.created_at), new.created_at),
           updated_at = timezone('utc', now())
     where id = target;
  elsif tg_op = 'DELETE' then
    update public.conversations
       set total_messages = greatest(total_messages - 1, 0),
           total_user_messages = case when old.role = 'user'
                                      then greatest(total_user_messages - 1, 0)
                                      else total_user_messages end
     where id = target;
  end if;
  return null;
end;
$$ language plpgsql;

drop trigger if exists messages_bump_conversation_counters on public.messages;
create trigger messages_bump_conversation_counters
  after insert or delete on public.messages
  for each row execute function public.bump_conversation_counters();

alter table public.conversations enable row level security;
alter table public.messages enable row level security;

create or replace function public.current_client_session_id()
returns uuid as $$
declare
  claims jsonb := coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb;
  session_text text := claims ->> 'client_session_id';
begin
  if session_text is null then
    return null;
  end if;
  return session_text::uuid;
exception
  when others then
    return null;
end;
$$ language plpgsql stable;

create policy conversations_select_own
  on public.conversations
  for select
  using (
    auth.role() = 'service_role'
    or (user_id is not null and user_id = auth.uid())
    or (client_session_id is not null and client_session_id = public.current_client_session_id())
  );

create policy conversations_mutate_own
  on public.conversations
  for all
  using (
    auth.role() = 'service_role'
    or (user_id is not null and user_id = auth.uid())
    or (client_session_id is not null and client_session_id = public.current_client_session_id())
  )
  with check (
    (user_id is not null and user_id = auth.uid())
    or (client_session_id is not null and client_session_id = public.current_client_session_id())
  );

create policy messages_select_conversation
  on public.messages
  for select
  using (
    auth.role() = 'service_role'
    or exists (
      select 1
        from public.conversations c
       where c.id = messages.conversation_id
         and (
           (c.user_id is not null and c.user_id = auth.uid())
           or (c.client_session_id is not null and c.client_session_id = public.current_client_session_id())
         )
    )
  );

create policy messages_mutate_conversation
  on public.messages
  for all
  using (
    auth.role() = 'service_role'
    or exists (
      select 1
        from public.conversations c
       where c.id = messages.conversation_id
         and (
           (c.user_id is not null and c.user_id = auth.uid())
           or (c.client_session_id is not null and c.client_session_id = public.current_client_session_id())
         )
    )
  )
  with check (
    exists (
      select 1
        from public.conversations c
       where c.id = messages.conversation_id
         and (
           (c.user_id is not null and c.user_id = auth.uid())
           or (c.client_session_id is not null and c.client_session_id = public.current_client_session_id())
         )
    )
  );

commit;
