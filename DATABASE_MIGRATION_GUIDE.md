# 数据库迁移执行指南

## 🚨 当前问题

Worker API 报错：
```
Could not find the table 'public.deep_research_tasks' in the schema cache
Could not find the 'client_session_id' column of 'conversations' in the schema cache
```

## 📋 需要执行的迁移

### 迁移文件清单

1. **`supabase/migrations/20251109_create_conversations_and_messages.sql`**
   - 创建 conversations 表
   - 创建 messages 表
   - RLS 策略

2. **`supabase/migrations/20251110_create_api_calls_telemetry.sql`**
   - 创建 api_calls 表 (427行)
   - 14个性能索引
   - 3个分析视图
   - 2个存储函数

3. **`supabase/migrations/20251110_create_deep_research_tasks.sql`**
   - 创建 deep_research_tasks 表 (230行)
   - 8个性能索引
   - RLS 策略
   - update_research_progress 函数
   - 2个分析视图

## 🚀 执行步骤

### 方法 1: Supabase Dashboard (推荐)

**步骤 1**: 访问 Supabase Dashboard
```
https://supabase.com/dashboard/project/hxxnkbxyjhhorfeodiji/sql
```

**步骤 2**: 登录
- 使用 GitHub 账号登录
- 选择项目: hxxnkbxyjhhorfeodiji

**步骤 3**: 执行 SQL
1. 点击 "New query"
2. 粘贴第一个迁移文件内容 (20251109...)
3. 点击 "Run"
4. 等待完成 (约 10-30秒)
5. 重复步骤 2-4 为其他迁移文件

**步骤 4**: 验证
```sql
-- 检查表是否存在
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
  'conversations', 'messages', 'api_calls', 'deep_research_tasks'
);

-- 应该返回 4 行

-- 检查 RLS 是否启用
SELECT relname, relrowsecurity
FROM pg_class
WHERE relname IN (
  'conversations', 'messages', 'api_calls', 'deep_research_tasks'
);

-- 所有值应该为 true
```

### 方法 2: Supabase CLI

**前提**: 需要 Supabase Access Token (格式: sbp_xxxxx)

**步骤 1**: 安装/更新 Supabase CLI
```bash
# macOS (Homebrew)
brew install supabase/tap/supabase

# Or update
brew upgrade supabase

# Verify installation
supabase --version
# Should be 2.x.x
```

**步骤 2**: 设置 Access Token
```bash
# Method 1: Interactive
supabase login
# Will open browser and ask for login

# Method 2: Environment variable
export SUPABASE_ACCESS_TOKEN="sbp_your_token_here"
```

**步骤 3**: 链接项目
```bash
cd /Users/marovole/GitHub/Web3search

supabase link --project-ref hxxnkbxyjhhorfeodiji
```

**预期输出**:
```
Finished supabase link.
```

**步骤 4**: 推送迁移
```bash
supabase db push

# Or with confirmation
supabase db push --debug
```

**预期输出**:
```
Applying migration 20251109_create_conversations_and_messages.sql...
Applying migration 20251110_create_api_calls_telemetry.sql...
Applying migration 20251110_create_deep_research_tasks.sql...
Finished supabase db push.
```

**步骤 5**: 验证
```bash
supabase db remote commit

# Should show no differences
```

### 方法 3: 直接 psql 连接

**步骤 1**: 获取连接字符串
```bash
# From Supabase Dashboard
Project Settings → Database → Connection pooling

# Connection string format:
postgresql://postgres:[PASSWORD]@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres

# Password: kaJtGrK8s54jOw56 (from your credentials)
```

**步骤 2**: 安装 psql (如果没有)
```bash
# macOS
brew install postgresql

# Or use Docker
docker run -it --rm postgres psql ...
```

**步骤 3**: 执行迁移
```bash
# Run each migration file
psql "postgresql://postgres:kaJtGrK8s54jOw56@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres" \
  -f supabase/migrations/20251109_create_conversations_and_messages.sql

psql "postgresql://postgres:kaJtGrK8s54jOw56@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres" \
  -f supabase/migrations/20251110_create_api_calls_telemetry.sql

psql "postgresql://postgres:kaJtGrK8s54jOw56@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres" \
  -f supabase/migrations/20251110_create_deep_research_tasks.sql
```

## ✅ 验证清单

迁移执行后，请验证以下内容：

### 数据库表存在
```bash
# Test using API
curl https://web3search-api.marovole.workers.dev/api/v1/deep-research \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "Test research"}'

# Should return: 202 Accepted with task_id
# Not: 500 error with "table not found"
```

### Worker 日志正常
```bash
# In Worker logs, should NOT see:
❌ "Could not find the table 'public.deep_research_tasks'"
❌ "Could not find the 'client_session_id' column"

# Should see:
✅ "Research task created successfully"
✅ "Research task XXXXX completed successfully"
```

### API 端点可用
```bash
# All these should work:
curl https://web3search-api.marovole.workers.dev/api/v1/health
curl https://web3search-api.marovole.workers.dev/api/v2/chat/quick-chat
curl https://web3search-api.marovole.workers.dev/api/v1/deep-research
```

## 🔧 常见问题

### 问题 1: "Could not find the table"
**原因**: 迁移未应用
**解决**: 执行上述迁移步骤

### 问题 2: Permission denied
**原因**: RLS 策略未正确设置
**解决**: 重新执行迁移文件中的 RLS 部分

### 问题 3: Connection timeout
**原因**: 网络问题或 Supabase 区域问题
**解决**: 使用 connection pooling (端口 6543)

### 问题 4: Column not found
**原因**: migrations 中的 ALTER TABLE 未在所有表上执行
**解决**: 手动检查每个迁移文件的执行状态

## 📊 迁移执行后状态

| Item | Status After Migration |
|------|------------------------|
| conversations table | ✅ Exists (with client_session_id) |
| messages table | ✅ Exists |
| api_calls table | ✅ Exists |
| deep_research_tasks table | ✅ Exists |
| RLS Policies | ✅ Enabled |
| Indexes | ✅ Created |
| Functions | ✅ Created |
| Views | ✅ Created |

## 📝 备注

- **backup before migration**: 生产环境建议先备份
- **test migrations locally**: 建议在本地测试通过再生产执行
- **monitor performance**: 迁移后关注查询性能
- **check RLS**: 确保 Row Level Security 正确配置
