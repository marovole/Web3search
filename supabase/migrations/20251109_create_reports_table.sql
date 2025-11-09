-- ============================================
-- Reports Table - Week 3 Day 11-12 Migration
-- Research Reports Storage
-- ============================================

BEGIN;

-- ============================================
-- Reports Table
-- Stores generated research reports
-- ============================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    sections JSONB NOT NULL, -- Array of section definitions
    content JSONB NOT NULL, -- Map of section_id -> content
    metadata JSONB, -- { model, tokens_used, generation_time_ms, etc. }
    user_id UUID, -- Optional: for future user authentication
    status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('generating', 'completed', 'failed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS ix_reports_topic ON reports USING gin(to_tsvector('english', topic));
CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_reports_status ON reports(status);

-- ============================================
-- Trigger: Update updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_reports_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE reports
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_reports_timestamp
    AFTER INSERT OR UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_reports_timestamp();

-- ============================================
-- Row Level Security (RLS) - Optional
-- ============================================
-- ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Users can view their own reports"
--     ON reports FOR SELECT
--     USING (user_id = auth.uid() OR user_id IS NULL);

-- CREATE POLICY "Users can insert their own reports"
--     ON reports FOR INSERT
--     WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

COMMIT;

-- ============================================
-- Verification Queries
-- ============================================
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'reports'
-- ORDER BY ordinal_position;

-- SELECT tablename, indexname FROM pg_indexes
-- WHERE tablename = 'reports';