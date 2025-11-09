-- 20251110_add_messages_metadata.sql
-- Add missing metadata column to messages table
BEGIN;

ALTER TABLE public.messages
  ADD COLUMN metadata JSONB;

-- Create GIN index for efficient JSONB queries (optional)
CREATE INDEX IF NOT EXISTS ix_messages_metadata_gin
  ON public.messages USING GIN (metadata);

COMMIT;