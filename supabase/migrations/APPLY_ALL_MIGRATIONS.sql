/***********************************************
 * Combined Database Migration Script
 * Run this in Supabase Dashboard SQL Editor
 * Project: hxxnkbxyjhhorfeodiji
 **********************************************/

-- =============================================
-- STEP 1: Create Conversations and Messages Tables
-- =============================================
-- File: 20251109_create_conversations_and_messages.sql
-- =============================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = timezone('utc', now());
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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

CREATE INDEX IF NOT EXISTS conversations_user_updated_idx
  ON public.conversations (user_id, updated_at DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS conversations_session_updated_idx
  ON public.conversations (client_session_id, updated_at DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS conversations_last_message_idx
  ON public.conversations (last_message_at DESC) WHERE deleted_at IS NULL;

CREATE TRIGGER conversations_touch_updated_at
  BEFORE UPDATE ON public.conversations
  FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

CREATE TABLE IF NOT EXISTS public.messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  seq bigint GENERATED ALWAYS AS IDENTITY,
  conversation_id uuid NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  parent_message_id uuid REFERENCES public.messages(id) ON DELETE SET NULL,
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  role text NOT NULL CHECK (role IN ('system','user','assistant','tool')),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','streaming','completed','failed')),
  segment_index integer NOT NULL DEFAULT 0,
  is_final boolean NOT NULL DEFAULT false,
  content text,
  content_delta jsonb,
  content_json jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  model text,
  model_parameters jsonb,
  tool_name text,
  tool_call_id text,
  error_message text,
  token_count_prompt integer NOT NULL DEFAULT 0,
  token_count_completion integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  deleted_at timestamptz,
  CONSTRAINT messages_content_presence CHECK (
    content IS NOT NULL OR content_json IS NOT NULL OR content_delta IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS messages_conversation_seq_idx
  ON public.messages (conversation_id, seq DESC);

CREATE INDEX IF NOT EXISTS messages_conversation_created_idx
  ON public.messages (conversation_id, created_at DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS messages_user_created_idx
  ON public.messages (user_id, created_at DESC) WHERE user_id IS NOT NULL AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS messages_parent_segment_idx
  ON public.messages (parent_message_id, segment_index) WHERE parent_message_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS messages_status_pending_idx
  ON public.messages (status) WHERE status IN ('pending','streaming');

CREATE TRIGGER messages_touch_updated_at
  BEFORE UPDATE ON public.messages
  FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

CREATE OR REPLACE FUNCTION public.bump_conversation_counters()
RETURNS TRIGGER AS $$
DECLARE
  target uuid := COALESCE(NEW.conversation_id, OLD.conversation_id);
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.conversations
       SET total_messages = total_messages + 1,
           total_user_messages = total_user_messages + CASE WHEN NEW.role = 'user' THEN 1 ELSE 0 END,
           last_message_at = greatest(COALESCE(last_message_at, NEW.created_at), NEW.created_at),
           updated_at = timezone('utc', now())
     WHERE id = target;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.conversations
       SET total_messages = greatest(total_messages - 1, 0),
           total_user_messages = CASE WHEN OLD.role = 'user'
                                      THEN greatest(total_user_messages - 1, 0)
                                      ELSE total_user_messages END
     WHERE id = target;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS messages_bump_conversation_counters ON public.messages;
CREATE TRIGGER messages_bump_conversation_counters
  AFTER INSERT OR DELETE ON public.messages
  FOR EACH ROW EXECUTE FUNCTION public.bump_conversation_counters();

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.current_client_session_id()
RETURNS uuid AS $$
DECLARE
  claims jsonb := COALESCE(NULLIF(current_setting('request.jwt.claims', TRUE), ''), '{}')::jsonb;
  session_text text := claims ->> 'client_session_id';
BEGIN
  IF session_text IS NULL THEN
    RETURN NULL;
  END IF;
  RETURN session_text::uuid;
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE POLICY conversations_select_own
  ON public.conversations
  FOR SELECT
  USING (
    auth.role() = 'service_role'
    OR (user_id IS NOT NULL AND user_id = auth.uid())
    OR (client_session_id IS NOT NULL AND client_session_id = public.current_client_session_id())
  );

CREATE POLICY conversations_mutate_own
  ON public.conversations
  FOR ALL
  USING (
    auth.role() = 'service_role'
    OR (user_id IS NOT NULL AND user_id = auth.uid())
    OR (client_session_id IS NOT NULL AND client_session_id = public.current_client_session_id())
  )
  WITH CHECK (
    (user_id IS NOT NULL AND user_id = auth.uid())
    OR (client_session_id IS NOT NULL AND client_session_id = public.current_client_session_id())
  );

CREATE POLICY messages_select_conversation
  ON public.messages
  FOR SELECT
  USING (
    auth.role() = 'service_role'
    OR EXISTS (
      SELECT 1
        FROM public.conversations c
       WHERE c.id = messages.conversation_id
         AND (
           (c.user_id IS NOT NULL AND c.user_id = auth.uid())
           OR (c.client_session_id IS NOT NULL AND c.client_session_id = public.current_client_session_id())
         )
    )
  );

CREATE POLICY messages_mutate_conversation
  ON public.messages
  FOR ALL
  USING (
    auth.role() = 'service_role'
    OR EXISTS (
      SELECT 1
        FROM public.conversations c
       WHERE c.id = messages.conversation_id
         AND (
           (c.user_id IS NOT NULL AND c.user_id = auth.uid())
           OR (c.client_session_id IS NOT NULL AND c.client_session_id = public.current_client_session_id())
         )
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
        FROM public.conversations c
       WHERE c.id = messages.conversation_id
         AND (
           (c.user_id IS NOT NULL AND c.user_id = auth.uid())
           OR (c.client_session_id IS NOT NULL AND c.client_session_id = public.current_client_session_id())
         )
    )
  );

COMMIT;

-- =============================================
-- STEP 2: Create Deep Research Tasks Table
-- =============================================
-- File: 20251110_create_deep_research_tasks.sql
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

-- Indexes for query performance
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

-- Partial indexes for common filters
CREATE INDEX IF NOT EXISTS deep_research_tasks_pending_idx
  ON public.deep_research_tasks (created_at)
  WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS deep_research_tasks_running_idx
  ON public.deep_research_tasks (user_id, created_at)
  WHERE status = 'running';

CREATE INDEX IF NOT EXISTS deep_research_tasks_completed_idx
  ON public.deep_research_tasks (user_id, created_at DESC)
  WHERE status = 'completed';

-- Enable Row Level Security
ALTER TABLE public.deep_research_tasks ENABLE ROW LEVEL SECURITY;

-- RLS Policies
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

CREATE POLICY "Service role can manage all research tasks"
  ON public.deep_research_tasks FOR ALL
  USING (auth.role() = 'service_role');

-- Functions for task management
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
  -- Build dynamic update statement
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

  -- Always update the updated_at timestamp
  v_updates := array_append(v_updates, 'updated_at = timezone(''utc''::text, now())');

  -- Execute the update
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

-- Views for analytics
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

COMMIT;

-- =============================================
-- MIGRATION COMPLETE!
-- =============================================
-- Summary:
-- ✓ Created conversations table
-- ✓ Created messages table
-- ✓ Set up RLS policies
-- ✓ Created deep_research_tasks table
-- ✓ Created indexes for performance
-- ✓ Created update_research_progress function
-- ✓ Created analytics views
-- =============================================
