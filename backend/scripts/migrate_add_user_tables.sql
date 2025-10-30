-- ============================================
-- 用户账号系统数据库迁移脚本
-- 添加用户相关表结构
-- ============================================
-- 
-- 执行说明:
-- 1. 备份现有数据库
-- 2. 在PostgreSQL中执行此脚本
-- 3. 或者使用: psql -U username -d database_name -f migrate_add_user_tables.sql
--
-- 注意: 此脚本会修改现有表结构，请在生产环境谨慎操作
-- ============================================

BEGIN;

-- ============================================
-- 1. 创建users表
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
CREATE INDEX IF NOT EXISTS ix_users_email_verification_token ON users(email_verification_token);
CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users(password_reset_token);
CREATE INDEX IF NOT EXISTS ix_users_deleted_at ON users(deleted_at);

-- ============================================
-- 2. 创建user_preferences表
-- ============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL,
    preferences JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_preferences_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_user_preferences_user_id ON user_preferences(user_id);

-- ============================================
-- 3. 创建sessions表
-- ============================================
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    device_info JSONB,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_sessions_refresh_token_hash ON sessions(refresh_token_hash);
CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_sessions_user_expires ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS ix_sessions_revoked_expires ON sessions(is_revoked, expires_at);
CREATE INDEX IF NOT EXISTS ix_sessions_expires_at ON sessions(expires_at);

-- ============================================
-- 4. 修改conversations表，添加user_id外键
-- ============================================
-- 注意: 如果表不存在，可能需要先创建表

-- 如果user_id列不存在，先添加（允许NULL）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversations' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE conversations ADD COLUMN user_id VARCHAR(36);
        CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations(user_id);
    END IF;
END $$;

-- 将user_id改为外键（如果还没有设置）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_conversations_user' 
        AND table_name = 'conversations'
    ) THEN
        ALTER TABLE conversations 
        ADD CONSTRAINT fk_conversations_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- 确保索引存在
CREATE INDEX IF NOT EXISTS ix_conversations_user_created ON conversations(user_id, created_at);

-- ============================================
-- 5. 修改reports表，添加user_id外键
-- ============================================
-- 如果user_id列不存在，先添加（允许NULL）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'reports' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE reports ADD COLUMN user_id VARCHAR(36);
        CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports(user_id);
    END IF;
END $$;

-- 将user_id改为外键（如果还没有设置）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_reports_user' 
        AND table_name = 'reports'
    ) THEN
        ALTER TABLE reports 
        ADD CONSTRAINT fk_reports_user 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- 确保索引存在
CREATE INDEX IF NOT EXISTS ix_reports_user_created ON reports(user_id, created_at);

-- ============================================
-- 6. 创建更新时间触发器函数（PostgreSQL）
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为users表添加触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为user_preferences表添加触发器
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为sessions表添加触发器
DROP TRIGGER IF EXISTS update_sessions_last_used_at ON sessions;
CREATE TRIGGER update_sessions_last_used_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- ============================================
-- 迁移完成
-- ============================================
-- 验证:
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('users', 'user_preferences', 'sessions');
-- ============================================

