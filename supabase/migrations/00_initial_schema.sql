-- ============================================
-- Web3search Database Schema - Complete Migration
-- For Supabase PostgreSQL
-- ============================================
--
-- 执行说明:
-- 1. 在 Supabase SQL Editor 中执行此脚本
-- 2. 或使用 Supabase CLI: supabase db push
--
-- 注意: 此脚本创建全新的数据库结构
-- ============================================

BEGIN;

-- ============================================
-- PART 1: 核心数据表
-- ============================================

-- 1.1 Projects Table (加密货币项目)
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    coingecko_id VARCHAR(100) UNIQUE,
    description TEXT,
    website VARCHAR(500),
    whitepaper_url VARCHAR(500),
    blockchain VARCHAR(50),
    contract_addresses JSONB DEFAULT '{}',
    twitter_handle VARCHAR(100),
    telegram_url VARCHAR(200),
    discord_url VARCHAR(200),
    reddit_url VARCHAR(200),
    categories JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_projects_symbol ON projects(symbol);
CREATE INDEX IF NOT EXISTS ix_projects_coingecko_id ON projects(coingecko_id);
CREATE INDEX IF NOT EXISTS ix_projects_symbol_name ON projects(symbol, name);
CREATE INDEX IF NOT EXISTS ix_projects_blockchain ON projects(blockchain);

-- 1.2 Project Snapshots Table (项目数据快照)
-- ============================================
CREATE TABLE IF NOT EXISTS project_snapshots (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 市场数据
    price_usd DOUBLE PRECISION,
    price_btc DOUBLE PRECISION,
    market_cap DOUBLE PRECISION,
    total_volume_24h DOUBLE PRECISION,
    circulating_supply DOUBLE PRECISION,
    total_supply DOUBLE PRECISION,
    max_supply DOUBLE PRECISION,
    price_change_24h DOUBLE PRECISION,
    price_change_7d DOUBLE PRECISION,
    price_change_30d DOUBLE PRECISION,
    market_cap_rank INTEGER,

    -- 链上数据
    holder_count INTEGER,
    total_transactions INTEGER,
    transaction_count_24h INTEGER,
    active_addresses_24h INTEGER,

    -- 社交数据
    twitter_followers INTEGER,
    twitter_mentions_24h INTEGER,
    reddit_subscribers INTEGER,
    reddit_active_users INTEGER,

    -- 情感分析
    sentiment_score DOUBLE PRECISION,
    sentiment_volume INTEGER,

    -- 原始数据
    raw_market_data JSONB,
    raw_onchain_data JSONB,
    raw_social_data JSONB
);

CREATE INDEX IF NOT EXISTS ix_project_snapshots_project_id ON project_snapshots(project_id);
CREATE INDEX IF NOT EXISTS ix_snapshots_timestamp ON project_snapshots(timestamp);
CREATE INDEX IF NOT EXISTS ix_snapshots_project_timestamp ON project_snapshots(project_id, timestamp);

-- ============================================
-- PART 2: 用户系统表
-- ============================================

-- 2.1 Users Table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token VARCHAR(64),
    password_reset_token VARCHAR(64),
    password_reset_expires_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_email_active ON users(email, is_active);
CREATE INDEX IF NOT EXISTS ix_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

-- 2.2 User Preferences Table
-- ============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferences JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_user_preferences_user_id ON user_preferences(user_id);

-- 2.3 Sessions Table
-- ============================================
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    device_info JSONB,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_sessions_refresh_token_hash ON sessions(refresh_token_hash);
CREATE INDEX IF NOT EXISTS ix_sessions_user_expires ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS ix_sessions_revoked_expires ON sessions(is_revoked, expires_at);
CREATE INDEX IF NOT EXISTS ix_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS ix_sessions_last_used_at ON sessions(last_used_at);

-- ============================================
-- PART 3: 对话系统表
-- ============================================

-- 3.1 Conversations Table
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500),
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    message_count INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    extra_metadata TEXT,  -- JSON string
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS ix_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS ix_conversations_last_activity ON conversations(last_activity);
CREATE INDEX IF NOT EXISTS ix_conversations_is_active ON conversations(is_active);
CREATE INDEX IF NOT EXISTS ix_conversations_user_created ON conversations(user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_conversations_active ON conversations(is_active, last_activity);

-- 3.2 Messages Table
-- ============================================
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    model VARCHAR(100),
    token_count INTEGER,
    generation_time TEXT,  -- 存储浮点数的文本表示
    report_id INTEGER,  -- 稍后添加外键
    is_streaming BOOLEAN NOT NULL DEFAULT FALSE,
    is_error BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS ix_messages_conversation_created ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS ix_messages_report_id ON messages(report_id);

-- ============================================
-- PART 4: 报告系统表
-- ============================================

CREATE TYPE report_type AS ENUM ('quick_chat', 'deep_research');
CREATE TYPE report_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    report_type report_type NOT NULL,
    status report_status NOT NULL DEFAULT 'pending',
    query TEXT NOT NULL,
    title VARCHAR(500),
    content_markdown TEXT,
    tldr TEXT,
    sections JSONB,
    data_sources JSONB,
    models_used JSONB,
    generation_time_seconds JSONB,  -- 存储浮点数
    token_usage JSONB,
    quality_score INTEGER,
    error_message TEXT,
    pdf_path VARCHAR(500),
    share_token VARCHAR(64) UNIQUE,
    share_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    share_expires_at TIMESTAMP,
    symbol VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_reports_project_id ON reports(project_id);
CREATE INDEX IF NOT EXISTS ix_reports_conversation_id ON reports(conversation_id);
CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS ix_reports_report_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS ix_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS ix_reports_share_token ON reports(share_token);
CREATE INDEX IF NOT EXISTS ix_reports_symbol ON reports(symbol);
CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports(created_at);
CREATE INDEX IF NOT EXISTS ix_reports_project_created ON reports(project_id, created_at);
CREATE INDEX IF NOT EXISTS ix_reports_type_status ON reports(report_type, status);
CREATE INDEX IF NOT EXISTS ix_reports_symbol_created ON reports(symbol, created_at);
CREATE INDEX IF NOT EXISTS ix_reports_status_created ON reports(status, created_at);
CREATE INDEX IF NOT EXISTS ix_reports_symbol_type_status ON reports(symbol, report_type, status);
CREATE INDEX IF NOT EXISTS ix_reports_user_created ON reports(user_id, created_at);

-- 添加 messages 表的外键（之前创建时报告表还不存在）
ALTER TABLE messages
ADD CONSTRAINT fk_messages_report
FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE SET NULL;

-- ============================================
-- PART 5: 数据库触发器和函数
-- ============================================

-- 自动更新 updated_at 字段的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为 users 表添加触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为 user_preferences 表添加触发器
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为 projects 表添加触发器
DROP TRIGGER IF EXISTS update_projects_last_updated ON projects;
CREATE TRIGGER update_projects_last_updated
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 自动更新 conversation.last_activity 的触发器函数
CREATE OR REPLACE FUNCTION update_conversation_last_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET last_activity = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_conversation_on_message ON messages;
CREATE TRIGGER update_conversation_on_message
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_last_activity();

-- ============================================
-- PART 6: 辅助表（统计、日志等）
-- ============================================

-- API 日志表（用于统计）
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    user_id VARCHAR(36),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_api_logs_created_at ON api_logs(created_at);
CREATE INDEX IF NOT EXISTS ix_api_logs_endpoint ON api_logs(endpoint);
CREATE INDEX IF NOT EXISTS ix_api_logs_status_code ON api_logs(status_code);

-- 统计表（用于 pg_cron 定时任务）
CREATE TABLE IF NOT EXISTS statistics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_statistics_date ON statistics(date);
CREATE INDEX IF NOT EXISTS ix_statistics_metric_name ON statistics(metric_name);
CREATE INDEX IF NOT EXISTS ix_statistics_date_metric ON statistics(date, metric_name);

-- 任务日志表（用于 pg_cron 监控）
CREATE TABLE IF NOT EXISTS task_logs (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_task_logs_created_at ON task_logs(created_at);
CREATE INDEX IF NOT EXISTS ix_task_logs_task_name ON task_logs(task_name);

COMMIT;

-- ============================================
-- 迁移完成！
-- ============================================
-- 验证表创建成功:
-- SELECT table_name
-- FROM information_schema.tables
-- WHERE table_schema = 'public'
-- ORDER BY table_name;
-- ============================================
