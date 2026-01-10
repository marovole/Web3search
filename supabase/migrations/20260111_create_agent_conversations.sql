-- Migration: Create agent_conversations table for conversational AI chat history
-- Part of Phase 6.2: Conversational Agent System

-- ============================================
-- Agent Conversations Table
-- ============================================
CREATE TABLE IF NOT EXISTS agent_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  intent JSONB,
  task_result JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_agent_conversations_user 
  ON agent_conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_agent_conversations_conv 
  ON agent_conversations(conversation_id);

CREATE INDEX IF NOT EXISTS idx_agent_conversations_created 
  ON agent_conversations(created_at DESC);

-- Composite index for fetching conversation history
CREATE INDEX IF NOT EXISTS idx_agent_conversations_user_conv 
  ON agent_conversations(user_id, conversation_id, created_at ASC);

-- ============================================
-- Row Level Security
-- ============================================
ALTER TABLE agent_conversations ENABLE ROW LEVEL SECURITY;

-- Users can only view their own conversations
CREATE POLICY "Users can view own conversations"
  ON agent_conversations FOR SELECT
  USING (auth.uid() = user_id);

-- Users can create their own conversation messages
CREATE POLICY "Users can create own messages"
  ON agent_conversations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can delete their own conversations
CREATE POLICY "Users can delete own conversations"
  ON agent_conversations FOR DELETE
  USING (auth.uid() = user_id);

-- Service role has full access (for backend operations)
CREATE POLICY "Service role full access"
  ON agent_conversations FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================
-- Comments
-- ============================================
COMMENT ON TABLE agent_conversations IS 'Stores conversational AI chat history for the agent system';
COMMENT ON COLUMN agent_conversations.conversation_id IS 'Groups related messages in a single conversation thread';
COMMENT ON COLUMN agent_conversations.role IS 'Message author: user, assistant, or system';
COMMENT ON COLUMN agent_conversations.intent IS 'Parsed intent from user message (JSON)';
COMMENT ON COLUMN agent_conversations.task_result IS 'Result of task execution if applicable (JSON)';
