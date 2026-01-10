-- ============================================
-- Phase 2: Watchlist and Agent Tables Migration
-- Part of: add-proactive-ai-agent-system
-- Date: 2026-01-09
-- ============================================

BEGIN;

-- ============================================
-- PART 1: Watchlist Table
-- ============================================

CREATE TABLE IF NOT EXISTS watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    token_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    
    coingecko_id VARCHAR(100),
    logo_url VARCHAR(500),
    
    notes TEXT,
    tags JSONB DEFAULT '[]',
    
    alert_settings JSONB DEFAULT '{
        "price_alert_enabled": false,
        "price_above": null,
        "price_below": null,
        "percent_change_enabled": false,
        "percent_change_threshold": null,
        "percent_change_period": "24h"
    }'::jsonb,
    
    position INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, token_id)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_token ON watchlist(token_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_user_position ON watchlist(user_id, position);

ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own watchlist"
    ON watchlist FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own watchlist"
    ON watchlist FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own watchlist"
    ON watchlist FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own watchlist"
    ON watchlist FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- PART 2: Agent Tasks Table
-- ============================================

CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'price_alert',
        'risk_monitor',
        'news_brief',
        'portfolio_health',
        'opportunity_finder',
        'custom'
    )),
    
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN (
        'active',
        'paused',
        'completed',
        'failed',
        'cancelled'
    )),
    
    config JSONB NOT NULL DEFAULT '{}',
    
    schedule VARCHAR(100),
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    expires_at TIMESTAMP WITH TIME ZONE,
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_user ON agent_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_type ON agent_tasks(type);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_next_run ON agent_tasks(next_run_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_agent_tasks_user_status ON agent_tasks(user_id, status);

ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own tasks"
    ON agent_tasks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tasks"
    ON agent_tasks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tasks"
    ON agent_tasks FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own tasks"
    ON agent_tasks FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- PART 3: Agent Runs Table
-- ============================================

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN (
        'running',
        'completed',
        'failed',
        'cancelled'
    )),
    
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    duration_ms INTEGER,
    
    input JSONB DEFAULT '{}',
    output JSONB DEFAULT '{}',
    
    steps JSONB DEFAULT '[]',
    
    error_message TEXT,
    error_code VARCHAR(50),
    
    tokens_used INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    
    triggered_by VARCHAR(50) DEFAULT 'schedule' CHECK (triggered_by IN (
        'schedule',
        'manual',
        'condition',
        'webhook'
    )),
    
    notification_sent BOOLEAN DEFAULT FALSE,
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_task ON agent_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_user ON agent_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_started ON agent_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_agent_runs_task_status ON agent_runs(task_id, status);

ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own runs"
    ON agent_runs FOR SELECT
    USING (auth.uid() = user_id);

-- ============================================
-- PART 4: Notifications Table
-- ============================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'price_alert',
        'risk_alert',
        'news_brief',
        'portfolio_update',
        'system',
        'promo'
    )),
    
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    
    data JSONB DEFAULT '{}',
    
    source_type VARCHAR(50),
    source_id UUID,
    
    read_at TIMESTAMP WITH TIME ZONE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    
    expires_at TIMESTAMP WITH TIME ZONE,
    
    push_sent BOOLEAN DEFAULT FALSE,
    push_sent_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notifications"
    ON notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications"
    ON notifications FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own notifications"
    ON notifications FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- PART 5: Push Subscriptions Table
-- ============================================

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    endpoint TEXT NOT NULL UNIQUE,
    
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    
    user_agent TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    last_used_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_push_subs_user ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subs_active ON push_subscriptions(user_id, is_active) WHERE is_active = TRUE;

ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own push subscriptions"
    ON push_subscriptions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own push subscriptions"
    ON push_subscriptions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own push subscriptions"
    ON push_subscriptions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own push subscriptions"
    ON push_subscriptions FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- PART 6: Triggers
-- ============================================

CREATE TRIGGER update_watchlist_updated_at
    BEFORE UPDATE ON watchlist
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_tasks_updated_at
    BEFORE UPDATE ON agent_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_push_subscriptions_updated_at
    BEFORE UPDATE ON push_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- PART 7: Helper Functions
-- ============================================

CREATE OR REPLACE FUNCTION increment_watchlist_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_quotas
    SET watchlist_count = watchlist_count + 1, updated_at = NOW()
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrement_watchlist_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_quotas
    SET watchlist_count = GREATEST(0, watchlist_count - 1), updated_at = NOW()
    WHERE user_id = OLD.user_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_watchlist_insert
    AFTER INSERT ON watchlist
    FOR EACH ROW
    EXECUTE FUNCTION increment_watchlist_count();

CREATE TRIGGER on_watchlist_delete
    AFTER DELETE ON watchlist
    FOR EACH ROW
    EXECUTE FUNCTION decrement_watchlist_count();

CREATE OR REPLACE FUNCTION increment_agent_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_quotas
    SET agent_count = agent_count + 1, updated_at = NOW()
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrement_agent_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_quotas
    SET agent_count = GREATEST(0, agent_count - 1), updated_at = NOW()
    WHERE user_id = OLD.user_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_agent_task_insert
    AFTER INSERT ON agent_tasks
    FOR EACH ROW
    EXECUTE FUNCTION increment_agent_count();

CREATE TRIGGER on_agent_task_delete
    AFTER DELETE ON agent_tasks
    FOR EACH ROW
    EXECUTE FUNCTION decrement_agent_count();

COMMIT;
