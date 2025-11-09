-- ============================================
-- Chat System Tables - Week 2 Migration
-- Conversations and Messages for AI Chat
-- ============================================

BEGIN;

-- ============================================
-- Conversations Table
-- Stores chat conversations with optional user association
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,  -- Optional: for future user authentication
    title TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS ix_conversations_created_at ON conversations(created_at DESC);

-- ============================================
-- Messages Table
-- Stores individual messages in conversations
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS ix_messages_conversation_created ON messages(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages(created_at DESC);

-- ============================================
-- Trigger: Update conversations.updated_at
-- Automatically update updated_at when conversation is modified
-- ============================================
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation_timestamp
    AFTER INSERT OR UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- ============================================
-- Row Level Security (RLS) - Optional
-- Enable when user authentication is implemented
-- ============================================
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Users can view their own conversations"
--     ON conversations FOR SELECT
--     USING (user_id = auth.uid() OR user_id IS NULL);

-- CREATE POLICY "Users can insert their own conversations"
--     ON conversations FOR INSERT
--     WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

-- CREATE POLICY "Users can view messages in their conversations"
--     ON messages FOR SELECT
--     USING (conversation_id IN (
--         SELECT id FROM conversations WHERE user_id = auth.uid() OR user_id IS NULL
--     ));

-- CREATE POLICY "Users can insert messages in their conversations"
--     ON messages FOR INSERT
--     WITH CHECK (conversation_id IN (
--         SELECT id FROM conversations WHERE user_id = auth.uid() OR user_id IS NULL
--     ));

COMMIT;

-- ============================================
-- Verification Queries
-- ============================================
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name IN ('conversations', 'messages')
-- ORDER BY table_name, ordinal_position;

-- SELECT tablename, indexname FROM pg_indexes
-- WHERE tablename IN ('conversations', 'messages');
