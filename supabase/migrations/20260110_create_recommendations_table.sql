-- ============================================
-- Phase 5.2: Opportunity Discovery Agent Tables
-- Part of: add-proactive-ai-agent-system
-- Date: 2026-01-10
-- ============================================

BEGIN;

-- ============================================
-- PART 1: User Preferences Table
-- Tracks user investment preferences for recommendations
-- ============================================

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    
    risk_tolerance VARCHAR(20) DEFAULT 'medium' CHECK (risk_tolerance IN (
        'conservative',
        'medium', 
        'aggressive',
        'very_aggressive'
    )),
    
    investment_horizon VARCHAR(20) DEFAULT 'medium' CHECK (investment_horizon IN (
        'short',
        'medium',
        'long'
    )),
    
    preferred_sectors JSONB DEFAULT '[]',
    
    excluded_sectors JSONB DEFAULT '[]',
    
    preferred_chains JSONB DEFAULT '[]',
    
    min_market_cap VARCHAR(20) DEFAULT 'any' CHECK (min_market_cap IN (
        'any',
        'micro',
        'small',
        'medium',
        'large'
    )),
    
    interest_tags JSONB DEFAULT '[]',
    
    notification_enabled BOOLEAN DEFAULT TRUE,
    
    discovery_frequency VARCHAR(20) DEFAULT 'weekly' CHECK (discovery_frequency IN (
        'daily',
        'weekly',
        'biweekly'
    )),
    
    max_recommendations_per_batch INTEGER DEFAULT 5,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);

ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own preferences"
    ON user_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences"
    ON user_preferences FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences"
    ON user_preferences FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- PART 2: Recommendations Table
-- Stores AI-generated project recommendations
-- ============================================

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    task_id UUID REFERENCES agent_tasks(id) ON DELETE SET NULL,
    run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    
    token_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    
    coingecko_id VARCHAR(100),
    logo_url VARCHAR(500),
    
    recommendation_type VARCHAR(50) NOT NULL CHECK (recommendation_type IN (
        'trending',
        'undervalued',
        'new_listing',
        'sector_match',
        'similar_to_holdings',
        'high_potential',
        'recovery_play',
        'ai_picked'
    )),
    
    confidence_score INTEGER DEFAULT 50 CHECK (confidence_score >= 0 AND confidence_score <= 100),
    
    match_reasons JSONB DEFAULT '[]',
    
    market_data JSONB DEFAULT '{}',
    
    ai_analysis TEXT,
    
    risk_level VARCHAR(20) DEFAULT 'medium' CHECK (risk_level IN (
        'low',
        'medium',
        'high',
        'very_high'
    )),
    
    potential_upside DECIMAL(10, 2),
    potential_downside DECIMAL(10, 2),
    
    time_horizon VARCHAR(20),
    
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN (
        'active',
        'viewed',
        'liked',
        'disliked',
        'dismissed',
        'expired'
    )),
    
    user_feedback VARCHAR(20) CHECK (user_feedback IN (
        'like',
        'dislike',
        'not_interested',
        'already_own',
        'will_research'
    )),
    feedback_at TIMESTAMP WITH TIME ZONE,
    feedback_notes TEXT,
    
    viewed_at TIMESTAMP WITH TIME ZONE,
    
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days'),
    
    batch_id UUID,
    batch_position INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_status ON recommendations(user_id, status);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_active ON recommendations(user_id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_recommendations_token ON recommendations(token_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_created ON recommendations(created_at);
CREATE INDEX IF NOT EXISTS idx_recommendations_batch ON recommendations(batch_id);

ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own recommendations"
    ON recommendations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own recommendations"
    ON recommendations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own recommendations"
    ON recommendations FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- PART 3: Recommendation History Table
-- Tracks which tokens have been recommended to avoid repetition
-- ============================================

CREATE TABLE IF NOT EXISTS recommendation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_id VARCHAR(100) NOT NULL,
    
    recommendation_id UUID REFERENCES recommendations(id) ON DELETE SET NULL,
    
    recommended_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    outcome VARCHAR(20) CHECK (outcome IN (
        'pending',
        'success',
        'neutral',
        'loss'
    )),
    
    price_at_recommendation DECIMAL(20, 8),
    price_at_outcome DECIMAL(20, 8),
    
    UNIQUE(user_id, token_id, recommended_at)
);

CREATE INDEX IF NOT EXISTS idx_rec_history_user ON recommendation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_rec_history_user_token ON recommendation_history(user_id, token_id);
CREATE INDEX IF NOT EXISTS idx_rec_history_recent ON recommendation_history(user_id, recommended_at);

ALTER TABLE recommendation_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own recommendation history"
    ON recommendation_history FOR SELECT
    USING (auth.uid() = user_id);

-- ============================================
-- PART 4: Triggers
-- ============================================

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- PART 5: Add recommendation type to notifications
-- ============================================

ALTER TABLE notifications 
DROP CONSTRAINT IF EXISTS notifications_type_check;

ALTER TABLE notifications
ADD CONSTRAINT notifications_type_check CHECK (type IN (
    'price_alert',
    'risk_alert',
    'news_brief',
    'portfolio_update',
    'recommendation',
    'system',
    'promo'
));

COMMIT;
