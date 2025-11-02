-- Migration: Add index to messages
CREATE INDEX CONCURRENTLY idx_messages_conversation_id_created_at 
ON messages(conversation_id, created_at);