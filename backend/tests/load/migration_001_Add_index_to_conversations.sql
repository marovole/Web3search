-- Migration: Add index to conversations
CREATE INDEX CONCURRENTLY idx_conversations_user_id_last_activity 
ON conversations(user_id, last_activity);