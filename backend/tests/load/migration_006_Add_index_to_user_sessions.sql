-- Migration: Add index to user_sessions
CREATE INDEX CONCURRENTLY idx_user_sessions_session_id_expires_at 
ON user_sessions(session_id, expires_at);