-- 20251110_switch_conversations_to_uuid.sql
-- Fix UUID vs Integer mismatch in conversations and related tables
BEGIN;

-- Ensure pgcrypto extension is available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Add UUID column and backfill existing rows
ALTER TABLE public.conversations
  ADD COLUMN id_v2 UUID DEFAULT gen_random_uuid();

UPDATE public.conversations
SET id_v2 = gen_random_uuid()
WHERE id_v2 IS NULL;

ALTER TABLE public.conversations
  ALTER COLUMN id_v2 SET NOT NULL;

-- 2. Add UUID FK columns on dependent tables
ALTER TABLE public.messages
  ADD COLUMN conversation_id_v2 UUID;

UPDATE public.messages m
SET conversation_id_v2 = c.id_v2
FROM public.conversations c
WHERE m.conversation_id::text = c.id::text;

ALTER TABLE public.messages
  ALTER COLUMN conversation_id_v2 SET NOT NULL;

-- Check if reports table has conversation_id before modifying it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports'
        AND column_name = 'conversation_id'
    ) THEN
        ALTER TABLE public.reports
          ADD COLUMN conversation_id_v2 UUID;

        UPDATE public.reports r
        SET conversation_id_v2 = c.id_v2
        FROM public.conversations c
        WHERE r.conversation_id::text = c.id::text;
    END IF;
END $$;

-- 3. Drop legacy constraints and indexes
ALTER TABLE public.messages DROP CONSTRAINT IF EXISTS messages_conversation_id_fkey;
DROP INDEX IF EXISTS ix_messages_conversation_id;
DROP INDEX IF EXISTS ix_messages_conversation_created;

-- Drop reports constraint if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'reports'
        AND constraint_name = 'reports_conversation_id_fkey'
    ) THEN
        ALTER TABLE public.reports DROP CONSTRAINT reports_conversation_id_fkey;
        DROP INDEX IF EXISTS ix_reports_conversation_id;
    END IF;
END $$;

-- 4. Replace primary key + column names
ALTER TABLE public.conversations DROP CONSTRAINT IF EXISTS conversations_pkey;
ALTER TABLE public.conversations ALTER COLUMN id DROP DEFAULT;

ALTER TABLE public.conversations RENAME COLUMN id TO id_legacy_int;
ALTER TABLE public.conversations RENAME COLUMN id_v2 TO id;

ALTER TABLE public.messages RENAME COLUMN conversation_id TO conversation_id_legacy_int;
ALTER TABLE public.messages RENAME COLUMN conversation_id_v2 TO conversation_id;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports'
        AND column_name = 'conversation_id'
    ) THEN
        ALTER TABLE public.reports RENAME COLUMN conversation_id TO conversation_id_legacy_int;
        ALTER TABLE public.reports RENAME COLUMN conversation_id_v2 TO conversation_id;
    END IF;
END $$;

ALTER TABLE public.conversations
  ADD PRIMARY KEY (id);
ALTER TABLE public.conversations
  ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- 5. Re-create FK + indexes
ALTER TABLE public.messages
  ADD CONSTRAINT messages_conversation_id_fkey
  FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;

CREATE INDEX ix_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX ix_messages_conversation_created ON public.messages(conversation_id, created_at);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports'
        AND column_name = 'conversation_id'
    ) THEN
        ALTER TABLE public.reports
          ADD CONSTRAINT reports_conversation_id_fkey
          FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;
        CREATE INDEX ix_reports_conversation_id ON public.reports(conversation_id);
    END IF;
END $$;

-- 6. Drop legacy columns/sequence
ALTER TABLE public.messages DROP COLUMN conversation_id_legacy_int;
ALTER TABLE public.conversations DROP COLUMN id_legacy_int;
DROP SEQUENCE IF EXISTS public.conversations_id_seq;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reports'
        AND column_name = 'conversation_id_legacy_int'
    ) THEN
        ALTER TABLE public.reports DROP COLUMN conversation_id_legacy_int;
    END IF;
END $$;

COMMIT;