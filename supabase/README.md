# Supabase 数据库迁移指南

本指南将帮助你完成从 Render PostgreSQL 到 Supabase 的数据库迁移。

## 📋 前提条件

1. Supabase 账户（免费）：https://supabase.com/
2. 访问现有 Render PostgreSQL 数据库的权限
3. PostgreSQL 客户端工具：`psql` 或 `pg_dump`
4. Supabase CLI（可选但推荐）

## 🚀 Part 1: 创建 Supabase 项目

### Step 1: 创建项目

1. 登录 https://app.supabase.com
2. 点击 "New Project"
3. 填写项目信息：
   - **Name**: `web3search`
   - **Database Password**: 生成一个强密码（保存好！）
   - **Region**: 选择最近的区域（推荐 `ap-northeast-1` 亚太地区）
   - **Pricing Plan**: Free（免费层）

4. 等待项目创建完成（约 2 分钟）

### Step 2: 获取连接信息

项目创建完成后，转到 **Settings** > **Database**：

```bash
# 保存以下信息：
Project URL: https://<project-ref>.supabase.co
Anon Key: <your-anon-key>
Service Role Key: <your-service-role-key>  # ⚠️ 保密！

# Database Connection String:
postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
```

## 📦 Part 2: 导出 Render 数据库

### Step 1: 导出 Schema

从你的本地机器连接到 Render 数据库并导出 schema：

```bash
# 获取 Render 数据库连接信息
# 在 Render Dashboard > Database > External Database URL

# 导出 schema（不包含数据）
pg_dump \
  -h <render-host>.render.com \
  -U <render-user> \
  -d <render-database> \
  --schema-only \
  --no-owner \
  --no-privileges \
  -f render_schema_backup.sql

# 提示输入密码
```

### Step 2: 导出数据

```bash
# 导出所有数据（可能需要一些时间）
pg_dump \
  -h <render-host>.render.com \
  -U <render-user> \
  -d <render-database> \
  --data-only \
  --no-owner \
  --no-privileges \
  -f render_data_backup.sql
```

### Step 3: 备份到云存储（可选但推荐）

```bash
# 压缩备份文件
tar -czf render_backup_$(date +%Y%m%d).tar.gz \
  render_schema_backup.sql \
  render_data_backup.sql

# 上传到云存储（例如：AWS S3, Google Cloud Storage）
# aws s3 cp render_backup_*.tar.gz s3://your-backup-bucket/
```

## 🔧 Part 3: 导入到 Supabase

### 方法 A: 使用 Supabase SQL Editor（推荐，无需额外工具）

1. 打开 Supabase Dashboard
2. 进入 **SQL Editor**
3. 执行迁移脚本：
   - 复制 `migrations/00_initial_schema.sql` 的内容
   - 粘贴到 SQL Editor
   - 点击 **Run**
4. 验证表已创建：

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### 方法 B: 使用 psql 命令行

```bash
# 连接到 Supabase 数据库
psql "postgresql://postgres:<your-password>@db.<project-ref>.supabase.co:5432/postgres"

# 执行迁移脚本
\i migrations/00_initial_schema.sql

# 验证
\dt
```

### Step 4: 导入数据（如果有现有数据）

```bash
# 使用 psql 导入数据
psql "postgresql://postgres:<your-password>@db.<project-ref>.supabase.co:5432/postgres" \
  -f render_data_backup.sql
```

**注意**：如果遇到外键约束错误，可以临时禁用：

```sql
-- 禁用所有外键约束
SET session_replication_role = 'replica';

-- 导入数据...

-- 重新启用外键约束
SET session_replication_role = 'origin';
```

## ✅ Part 4: 验证迁移

### Step 1: 检查表结构

```sql
-- 查看所有表
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 应该看到以下表：
-- api_logs
-- conversations
-- messages
-- project_snapshots
-- projects
-- reports
-- sessions
-- statistics
-- task_logs
-- user_preferences
-- users
```

### Step 2: 检查数据完整性

```sql
-- 检查关键表的行数
SELECT 'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'reports', COUNT(*) FROM reports;

-- 对比 Render 数据库的行数
```

### Step 3: 测试查询性能

```sql
-- 测试一个简单查询
EXPLAIN ANALYZE
SELECT * FROM conversations
WHERE user_id = '<test-user-id>'
ORDER BY created_at DESC
LIMIT 10;

-- 应该看到使用了索引扫描（Index Scan）
```

## 🔒 Part 5: 配置安全性（可选）

### 启用 Row Level Security (RLS)

如果需要用户数据隔离，启用 RLS：

```sql
-- 为敏感表启用 RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- 创建 RLS 策略示例
CREATE POLICY "Users can view own conversations"
ON conversations FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY "Users can insert own conversations"
ON conversations FOR INSERT
WITH CHECK (user_id = auth.uid());
```

## 📊 Part 6: 配置 pg_cron（定时任务）

### 启用 pg_cron 扩展

```sql
-- 在 Supabase SQL Editor 中执行
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 验证
SELECT * FROM cron.job;
```

### 创建数据清理任务

```sql
-- 创建清理函数
CREATE OR REPLACE FUNCTION cleanup_old_conversations()
RETURNS void AS $$
BEGIN
    DELETE FROM messages WHERE conversation_id IN (
        SELECT id FROM conversations
        WHERE created_at < NOW() - INTERVAL '30 days'
    );
    DELETE FROM conversations WHERE created_at < NOW() - INTERVAL '30 days';

    INSERT INTO task_logs (task_name, status, message)
    VALUES ('cleanup_old_conversations', 'success', 'Cleaned old conversations');
END;
$$ LANGUAGE plpgsql;

-- 调度每天凌晨 2 点执行
SELECT cron.schedule(
    'cleanup-conversations',
    '0 2 * * *',
    'SELECT cleanup_old_conversations();'
);
```

## 🎯 Part 7: 配置环境变量

将 Supabase 连接信息添加到你的项目环境变量：

### 对于 Cloudflare Workers:

```bash
# 使用 wrangler 设置 secrets
wrangler secret put SUPABASE_URL
# 输入: https://<project-ref>.supabase.co

wrangler secret put SUPABASE_ANON_KEY
# 输入: <your-anon-key>

wrangler secret put SUPABASE_SERVICE_ROLE_KEY
# 输入: <your-service-role-key>  # ⚠️ 仅在需要时使用
```

### 对于前端（Cloudflare Pages）:

在 Cloudflare Pages 设置中添加环境变量：
- `VITE_SUPABASE_URL`: `https://<project-ref>.supabase.co`
- `VITE_SUPABASE_ANON_KEY`: `<your-anon-key>`

## 📝 迁移检查清单

- [ ] Supabase 项目已创建
- [ ] 获取并保存所有连接信息
- [ ] Render 数据库 schema 已导出
- [ ] Render 数据库数据已导出
- [ ] 备份文件已保存到云存储
- [ ] 数据库 schema 已在 Supabase 中创建
- [ ] 数据已导入到 Supabase
- [ ] 表数量和行数已验证
- [ ] 关键查询性能已测试
- [ ] pg_cron 扩展已启用
- [ ] 环境变量已配置

## 🚨 故障排除

### 问题 1: 连接超时

```bash
# 检查网络连接
ping db.<project-ref>.supabase.co

# 检查防火墙设置
# Supabase 需要出站连接到 5432 端口
```

### 问题 2: 导入数据时外键错误

```sql
-- 临时禁用外键检查
SET session_replication_role = 'replica';

-- 导入数据...

-- 重新启用
SET session_replication_role = 'origin';
```

### 问题 3: 权限错误

```sql
-- 确保使用 service_role key 而不是 anon key
-- 或在 SQL Editor 中直接执行（自动使用 postgres 用户）
```

## 📚 相关文档

- [Supabase 数据库文档](https://supabase.com/docs/guides/database)
- [pg_dump 文档](https://www.postgresql.org/docs/current/app-pgdump.html)
- [PostgreSQL Migration Best Practices](https://www.postgresql.org/docs/current/backup.html)

## ✅ 下一步

完成数据库迁移后，继续 **Week 1 Day 3-4: Cloudflare Workers 项目搭建**
