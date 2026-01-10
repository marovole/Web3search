-- ============================================
-- Phase 5: Holdings (Portfolio) Table Migration
-- Part of: add-proactive-ai-agent-system
-- Date: 2026-01-10
-- ============================================

BEGIN;

-- ============================================
-- PART 1: Holdings Table
-- ============================================

CREATE TABLE IF NOT EXISTS holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    token_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    
    coingecko_id VARCHAR(100),
    logo_url VARCHAR(500),
    
    quantity DECIMAL(30, 18) NOT NULL DEFAULT 0,
    
    avg_buy_price DECIMAL(30, 18),
    
    total_cost_basis DECIMAL(30, 18),
    
    notes TEXT,
    
    tags JSONB DEFAULT '[]',
    
    acquisition_date DATE,
    
    is_staked BOOLEAN DEFAULT FALSE,
    staking_platform VARCHAR(100),
    staking_apy DECIMAL(10, 4),
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, token_id)
);

CREATE INDEX IF NOT EXISTS idx_holdings_user ON holdings(user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_token ON holdings(token_id);
CREATE INDEX IF NOT EXISTS idx_holdings_user_symbol ON holdings(user_id, symbol);

ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own holdings"
    ON holdings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own holdings"
    ON holdings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own holdings"
    ON holdings FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own holdings"
    ON holdings FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- PART 2: Portfolio Snapshots Table
-- ============================================

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    snapshot_date DATE NOT NULL,
    
    total_value_usd DECIMAL(30, 2) NOT NULL,
    
    total_cost_basis_usd DECIMAL(30, 2),
    
    total_pnl_usd DECIMAL(30, 2),
    total_pnl_percent DECIMAL(10, 4),
    
    holdings_count INTEGER NOT NULL DEFAULT 0,
    
    holdings_breakdown JSONB NOT NULL DEFAULT '[]',
    
    top_gainers JSONB DEFAULT '[]',
    top_losers JSONB DEFAULT '[]',
    
    concentration_metrics JSONB DEFAULT '{}',
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_user ON portfolio_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON portfolio_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_user_date ON portfolio_snapshots(user_id, snapshot_date DESC);

ALTER TABLE portfolio_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own portfolio snapshots"
    ON portfolio_snapshots FOR SELECT
    USING (auth.uid() = user_id);

-- ============================================
-- PART 3: Portfolio Diagnosis Reports Table
-- ============================================

CREATE TABLE IF NOT EXISTS portfolio_diagnoses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES agent_tasks(id) ON DELETE SET NULL,
    run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    
    diagnosis_date DATE NOT NULL,
    
    overall_health_score INTEGER CHECK (overall_health_score >= 0 AND overall_health_score <= 100),
    
    diversification_score INTEGER CHECK (diversification_score >= 0 AND diversification_score <= 100),
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    performance_score INTEGER CHECK (performance_score >= 0 AND performance_score <= 100),
    
    summary TEXT NOT NULL,
    
    strengths JSONB DEFAULT '[]',
    weaknesses JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    
    sector_allocation JSONB DEFAULT '{}',
    
    correlation_analysis JSONB DEFAULT '{}',
    
    risk_factors JSONB DEFAULT '[]',
    
    performance_vs_benchmarks JSONB DEFAULT '{}',
    
    full_report TEXT,
    
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_diagnoses_user ON portfolio_diagnoses(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_diagnoses_date ON portfolio_diagnoses(diagnosis_date);
CREATE INDEX IF NOT EXISTS idx_portfolio_diagnoses_user_date ON portfolio_diagnoses(user_id, diagnosis_date DESC);

ALTER TABLE portfolio_diagnoses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own portfolio diagnoses"
    ON portfolio_diagnoses FOR SELECT
    USING (auth.uid() = user_id);

-- ============================================
-- PART 4: Triggers
-- ============================================

CREATE TRIGGER update_holdings_updated_at
    BEFORE UPDATE ON holdings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
