-- ============================================
-- Agent System Core Tables Migration
-- Part of: add-proactive-ai-agent-system
-- Date: 2026-01-09
-- ============================================
--
-- This migration creates the foundational tables for:
-- 1. User profiles (extends Supabase auth.users)
-- 2. User quotas (subscription-based limits)
-- 3. Subscriptions (Stripe integration)
--
-- Prerequisites:
-- - Supabase Auth enabled
-- - SUPABASE_JWT_SECRET configured in Workers
-- ============================================

BEGIN;

-- ============================================
-- PART 1: User Profiles (extends auth.users)
-- ============================================

-- user_profiles extends Supabase Auth users with app-specific data
CREATE TABLE IF NOT EXISTS user_profiles (
    -- Primary key references Supabase Auth
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Display info
    username VARCHAR(50) UNIQUE,
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    
    -- Subscription info
    plan VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'team')),
    stripe_customer_id VARCHAR(100) UNIQUE,
    
    -- Preferences
    risk_preference VARCHAR(20) DEFAULT 'moderate' CHECK (risk_preference IN ('conservative', 'moderate', 'aggressive')),
    notification_settings JSONB DEFAULT '{
        "price_alerts": true,
        "risk_alerts": true,
        "news_briefs": true,
        "portfolio_updates": true,
        "push_enabled": false
    }'::jsonb,
    
    -- App settings
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    theme VARCHAR(20) DEFAULT 'system' CHECK (theme IN ('light', 'dark', 'system')),
    
    -- Metadata
    onboarding_completed BOOLEAN DEFAULT FALSE,
    last_active_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_plan ON user_profiles(plan);
CREATE INDEX IF NOT EXISTS idx_user_profiles_stripe_customer ON user_profiles(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username) WHERE username IS NOT NULL;

-- ============================================
-- PART 2: User Quotas
-- ============================================

-- user_quotas tracks usage against subscription limits
CREATE TABLE IF NOT EXISTS user_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Watchlist quota
    watchlist_count INTEGER DEFAULT 0,
    watchlist_limit INTEGER DEFAULT 5,  -- Free: 5, Pro: 50, Team: unlimited
    
    -- Agent quota
    agent_count INTEGER DEFAULT 0,
    agent_limit INTEGER DEFAULT 2,  -- Free: 2, Pro: 20, Team: 100
    
    -- Daily quotas (reset at midnight UTC)
    daily_alerts_sent INTEGER DEFAULT 0,
    daily_alerts_limit INTEGER DEFAULT 10,  -- Free: 10, Pro: 100, Team: 500
    daily_deep_research INTEGER DEFAULT 0,
    daily_deep_research_limit INTEGER DEFAULT 3,  -- Free: 3, Pro: 30, Team: 100
    daily_quick_chat INTEGER DEFAULT 0,
    daily_quick_chat_limit INTEGER DEFAULT 50,  -- Free: 50, Pro: 500, Team: 2000
    
    -- Monthly quotas (reset on billing cycle)
    monthly_reports INTEGER DEFAULT 0,
    monthly_reports_limit INTEGER DEFAULT 5,  -- Free: 5, Pro: 50, Team: 200
    
    -- Reset timestamps
    daily_reset_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_DATE + INTERVAL '1 day'),
    monthly_reset_at TIMESTAMP WITH TIME ZONE DEFAULT (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- Indexes for user_quotas
CREATE INDEX IF NOT EXISTS idx_user_quotas_user ON user_quotas(user_id);
CREATE INDEX IF NOT EXISTS idx_user_quotas_daily_reset ON user_quotas(daily_reset_at);
CREATE INDEX IF NOT EXISTS idx_user_quotas_monthly_reset ON user_quotas(monthly_reset_at);

-- ============================================
-- PART 3: Subscriptions (Stripe sync)
-- ============================================

-- subscriptions stores Stripe subscription state
CREATE TABLE IF NOT EXISTS subscriptions (
    id VARCHAR(100) PRIMARY KEY,  -- Stripe Subscription ID (sub_xxx)
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Subscription details
    status VARCHAR(30) NOT NULL CHECK (status IN (
        'active', 'trialing', 'past_due', 'canceled', 
        'incomplete', 'incomplete_expired', 'unpaid', 'paused'
    )),
    price_id VARCHAR(100) NOT NULL,  -- Stripe Price ID
    product_id VARCHAR(100),  -- Stripe Product ID
    
    -- Billing info
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    
    -- Trial info
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for subscriptions
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON subscriptions(current_period_end);

-- ============================================
-- PART 4: Row Level Security (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- user_profiles policies
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- user_quotas policies
CREATE POLICY "Users can view own quota"
    ON user_quotas FOR SELECT
    USING (auth.uid() = user_id);

-- Note: Quota updates should only happen via service role (backend)
-- No user-facing UPDATE policy

-- subscriptions policies
CREATE POLICY "Users can view own subscriptions"
    ON subscriptions FOR SELECT
    USING (auth.uid() = user_id);

-- Note: Subscription changes only via Stripe webhooks (service role)
-- No user-facing INSERT/UPDATE/DELETE policies

-- ============================================
-- PART 5: Triggers and Functions
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to tables
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_quotas_updated_at
    BEFORE UPDATE ON user_quotas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to create user_profiles and user_quotas on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Create user profile
    INSERT INTO public.user_profiles (id)
    VALUES (NEW.id)
    ON CONFLICT (id) DO NOTHING;
    
    -- Create user quota with free tier limits
    INSERT INTO public.user_quotas (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile and quota on user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- Function to update quotas when plan changes
CREATE OR REPLACE FUNCTION update_quota_limits_on_plan_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.plan != OLD.plan THEN
        UPDATE user_quotas
        SET 
            watchlist_limit = CASE NEW.plan
                WHEN 'free' THEN 5
                WHEN 'pro' THEN 50
                WHEN 'team' THEN 1000  -- Effectively unlimited
            END,
            agent_limit = CASE NEW.plan
                WHEN 'free' THEN 2
                WHEN 'pro' THEN 20
                WHEN 'team' THEN 100
            END,
            daily_alerts_limit = CASE NEW.plan
                WHEN 'free' THEN 10
                WHEN 'pro' THEN 100
                WHEN 'team' THEN 500
            END,
            daily_deep_research_limit = CASE NEW.plan
                WHEN 'free' THEN 3
                WHEN 'pro' THEN 30
                WHEN 'team' THEN 100
            END,
            daily_quick_chat_limit = CASE NEW.plan
                WHEN 'free' THEN 50
                WHEN 'pro' THEN 500
                WHEN 'team' THEN 2000
            END,
            monthly_reports_limit = CASE NEW.plan
                WHEN 'free' THEN 5
                WHEN 'pro' THEN 50
                WHEN 'team' THEN 200
            END,
            updated_at = NOW()
        WHERE user_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update quotas when plan changes
CREATE TRIGGER on_user_plan_changed
    AFTER UPDATE OF plan ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_quota_limits_on_plan_change();

-- ============================================
-- PART 6: Quota Reset Functions (for Cron)
-- ============================================

-- Function to reset daily quotas
CREATE OR REPLACE FUNCTION reset_daily_quotas()
RETURNS void AS $$
BEGIN
    UPDATE user_quotas
    SET 
        daily_alerts_sent = 0,
        daily_deep_research = 0,
        daily_quick_chat = 0,
        daily_reset_at = CURRENT_DATE + INTERVAL '1 day',
        updated_at = NOW()
    WHERE daily_reset_at <= NOW();
    
    -- Log the reset
    INSERT INTO task_logs (task_name, status, message)
    VALUES ('reset_daily_quotas', 'success', 
        format('Reset daily quotas for %s users', (SELECT COUNT(*) FROM user_quotas WHERE daily_reset_at <= NOW() + INTERVAL '1 day')));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to reset monthly quotas
CREATE OR REPLACE FUNCTION reset_monthly_quotas()
RETURNS void AS $$
BEGIN
    UPDATE user_quotas
    SET 
        monthly_reports = 0,
        monthly_reset_at = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month',
        updated_at = NOW()
    WHERE monthly_reset_at <= NOW();
    
    -- Log the reset
    INSERT INTO task_logs (task_name, status, message)
    VALUES ('reset_monthly_quotas', 'success',
        format('Reset monthly quotas for %s users', (SELECT COUNT(*) FROM user_quotas WHERE monthly_reset_at <= NOW() + INTERVAL '1 month')));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Schedule daily quota reset (run at 00:00 UTC every day)
-- Note: Requires pg_cron extension to be enabled
-- SELECT cron.schedule('reset-daily-quotas', '0 0 * * *', 'SELECT reset_daily_quotas()');

-- Schedule monthly quota reset (run at 00:00 UTC on 1st of each month)
-- SELECT cron.schedule('reset-monthly-quotas', '0 0 1 * *', 'SELECT reset_monthly_quotas()');

COMMIT;
