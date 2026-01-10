# Design: Proactive AI Agent System

## Context

Web3search 需要从被动响应式平台升级为主动智能平台。本设计文档定义了 Agent 系统的核心架构和技术决策。

### 背景

- **现有能力**: Deep Research Pipeline 已实现 ReAct 式循环，Glass Box Panel 提供实时可视化
- **基础设施**: Cloudflare Workers + Supabase + OpenRouter，已有 Cron 触发器
- **目标用户**: 加密货币投资者和研究人员
- **商业目标**: 通过订阅付费实现可持续收入

## Goals

1. 用户可以通过自然语言配置监控规则（对话式 Agent）
2. Agent 持续运行，满足条件时主动通知用户
3. 系统可扩展，易于添加新类型的 Agent
4. 成本可控，通过配额和分层管理资源
5. 用户体验透明，可查看 Agent 执行过程

## Non-Goals

1. **不实现自动交易功能** - 风险过高，需要单独的安全框架
2. **不连接用户钱包** - 避免私钥管理责任
3. **不存储用户私钥** - 安全红线
4. **不实现邮件/Telegram 通知** - Phase 1 仅浏览器推送

## Decisions

### Decision 1: 使用 Supabase Auth 而非自建认证

**选择**: Supabase Auth

**理由**:
- 已使用 Supabase 作为数据库，零额外成本
- 内置 JWT 生成和验证
- 与 RLS (Row Level Security) 无缝集成
- 支持多种登录方式 (Email, OAuth)
- 减少开发和维护工作量

**替代方案**:
| 方案 | 优点 | 缺点 |
|------|------|------|
| Auth0 | 功能强大，企业级 | 有成本，额外依赖 |
| 自建 JWT | 完全控制 | 开发成本高，安全风险 |
| Clerk | 现代 UI | 有成本，需要额外集成 |

### Decision 2: 使用 Web Push 而非 WebSocket

**选择**: Web Push API (Service Worker)

**理由**:
- 即使页面关闭也能收到通知
- 符合 PWA 标准，移动端体验好
- Cloudflare Workers 原生支持发送
- 无需维护长连接

**替代方案**:
| 方案 | 优点 | 缺点 |
|------|------|------|
| WebSocket | 实时性高 | 需要页面保持打开 |
| Supabase Realtime | 易集成 | 不支持离线通知 |
| Firebase FCM | 移动端成熟 | 额外依赖 Google |

### Decision 3: Agent 执行采用 Cron 轮询

**选择**: Cloudflare Cron Triggers + 批量处理

**理由**:
- 简化架构，无需消息队列
- Cloudflare Workers 原生支持
- 对于价格监控场景，5 分钟轮询足够
- 可预测的成本和资源使用

**替代方案**:
| 方案 | 优点 | 缺点 |
|------|------|------|
| 事件驱动 Webhook | 真正实时 | 依赖外部服务稳定性 |
| Temporal | 强大的工作流 | 增加基础设施复杂度 |
| Inngest | 现代事件驱动 | 额外服务依赖 |

### Decision 4: 对话式 Intent 解析使用 LLM

**选择**: 使用现有 OpenRouter LLM 进行 Intent 解析

**理由**:
- 复用现有基础设施和 API Key
- 自然语言理解能力强
- 可处理模糊和复杂的用户指令
- 易于迭代和优化 Prompt

**风险缓解**:
- 低置信度 (< 0.8) 时要求用户确认
- 解析结果进行结构化验证
- 限制 Agent 可执行的操作类型（只能监控，不能交易）

### Decision 5: 订阅付费使用 Stripe

**选择**: Stripe Billing

**理由**:
- 行业标准，可靠稳定
- Webhook 机制成熟
- 支持订阅、试用、升降级
- 文档完善，社区资源丰富

**替代方案**:
| 方案 | 优点 | 缺点 |
|------|------|------|
| Paddle | 处理税务 | 手续费更高 |
| LemonSqueezy | 简单 | 功能相对有限 |
| 自建 | 无手续费 | 合规复杂度高 |

## Architecture

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │  Auth Pages  │ │  Watchlist   │ │ Agent Config │ │ Notification Center│  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────────┘  │
│                              │                                               │
│  ┌───────────────────────────┴───────────────────────────────────────────┐  │
│  │                    Conversational Agent Chat                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                              │                                               │
│  ┌───────────────────────────┴───────────────────────────────────────────┐  │
│  │                    Web Push + Service Worker                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Workers API (Hono)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Auth Middleware (Supabase JWT)                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Quota Middleware                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                       │                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐    │
│  │ /watchlist  │ │  /agents    │ │   /push     │ │    /billing         │    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘    │
│                                       │                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     Agent Execution Engine                             │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐   │  │
│  │  │  ReAct    │  │   Tool    │  │  Memory   │  │   Quota           │   │  │
│  │  │  Loop     │  │  Registry │  │  Manager  │  │   Enforcer        │   │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘   │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                Conversational Intent Parser                      │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     Push Notification Service                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────────┐
         ▼                             ▼                                 ▼
┌─────────────────┐          ┌─────────────────┐              ┌─────────────────┐
│    Supabase     │          │ Cloudflare Cron │              │  External APIs  │
│  - user_profiles│          │  */5 * * * *    │              │  - CoinGecko    │
│  - watchlist    │          │  0 * * * *      │              │  - GoPlus       │
│  - agent_tasks  │          │  0 9 * * 1      │              │  - CryptoPanic  │
│  - notifications│          └─────────────────┘              │  - Stripe       │
└─────────────────┘                                           └─────────────────┘
```

### 数据库 Schema

```sql
-- 用户配置扩展
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  plan TEXT DEFAULT 'free',
  notification_settings JSONB,
  risk_preference TEXT DEFAULT 'moderate',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 监控列表
CREATE TABLE watchlist (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  token_symbol TEXT NOT NULL,
  contract_address TEXT,
  chain TEXT DEFAULT 'ethereum',
  added_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent 任务
CREATE TABLE agent_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  task_type TEXT NOT NULL,
  config JSONB NOT NULL,
  natural_language_instruction TEXT,
  status TEXT DEFAULT 'active',
  next_run_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent 执行日志
CREATE TABLE agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES agent_tasks(id),
  user_id UUID REFERENCES auth.users(id),
  status TEXT DEFAULT 'running',
  iterations JSONB DEFAULT '[]',
  result JSONB,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- 通知
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  agent_task_id UUID REFERENCES agent_tasks(id),
  type TEXT NOT NULL,
  severity TEXT DEFAULT 'info',
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用户配额
CREATE TABLE user_quotas (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id),
  daily_deep_research_used INTEGER DEFAULT 0,
  monthly_agent_conversations_used INTEGER DEFAULT 0,
  daily_reset_at TIMESTAMPTZ,
  monthly_reset_at TIMESTAMPTZ
);

-- 推送订阅
CREATE TABLE push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  endpoint TEXT NOT NULL,
  p256dh_key TEXT NOT NULL,
  auth_key TEXT NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Data Flow

### 对话式 Agent 创建流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 用户输入: "帮我监控AAVE，如果TVL下降超过10%就通知我"          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Intent Parser (LLM)                                          │
│    - 提取 token: AAVE                                           │
│    - 提取 metric: TVL                                           │
│    - 提取 condition: decrease > 10%                             │
│    - 生成 confidence: 0.92                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Validator                                                    │
│    - 验证 AAVE 在 DefiLlama 有 TVL 数据                         │
│    - 获取当前 TVL 作为基准: $12.5B                              │
│    - 检查用户配额: OK                                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Confirmation (confidence < 0.8 时触发)                       │
│    Agent: "我将为您监控AAVE的TVL变化。当前TVL为$12.5B，          │
│            我会在TVL下降超过10%时通知您。确认创建吗？"           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Task Creation                                                │
│    INSERT INTO agent_tasks (                                    │
│      task_type: 'tvl_alert',                                    │
│      config: {token: 'AAVE', threshold: -10, baseline: 12.5B},  │
│      next_run_at: NOW() + 5min                                  │
│    )                                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Response                                                     │
│    "✅ 监控任务已创建！我会每5分钟检查一次AAVE的TVL，             │
│     一旦下降超过10%会立即通知您。"                               │
└─────────────────────────────────────────────────────────────────┘
```

### Agent 执行流程 (Cron)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Cron Trigger (*/5 * * * *)                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 查询待执行任务                                                │
│    SELECT * FROM agent_tasks                                    │
│    WHERE status = 'active' AND next_run_at <= NOW()             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 批量获取数据 (减少 API 调用)                                  │
│    - 聚合所有任务需要的代币列表                                  │
│    - 批量调用 CoinGecko/DefiLlama                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 评估条件 (并行处理)                                           │
│    FOR each task:                                               │
│      - 获取当前值                                               │
│      - 与阈值比较                                               │
│      - 记录 agent_run                                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 触发通知 (条件满足时)                                         │
│    - 创建 notification 记录                                     │
│    - 查询用户 push_subscription                                 │
│    - 发送 Web Push                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. 更新任务状态                                                  │
│    UPDATE agent_tasks SET next_run_at = NOW() + interval        │
└─────────────────────────────────────────────────────────────────┘
```

## Security

### 认证和授权

1. **JWT 验证**: 所有 `/api/v1/*` 端点（除 `/auth/*`）需要有效 JWT
2. **RLS 策略**: 所有用户数据表启用 `auth.uid() = user_id`
3. **服务端配额执行**: 配额检查在 middleware 层，无法绕过

### 推送安全

1. **VAPID 私钥**: 存储在 Cloudflare Secrets，不暴露给客户端
2. **订阅绑定**: `push_subscriptions` 绑定 `user_id`，防止跨用户推送
3. **端点验证**: 只向经过验证的端点发送推送

### 支付安全

1. **Webhook 签名验证**: 验证 Stripe webhook 签名
2. **幂等处理**: 处理重复 webhook 事件
3. **状态同步**: 订阅状态以 Stripe 为准，Webhook 触发同步

### Agent 安全

1. **操作限制**: Agent 只能执行预定义的安全操作（监控、通知）
2. **迭代限制**: ReAct 循环最大 5 次迭代，防止无限循环
3. **Intent 验证**: 解析结果必须通过结构化验证

## Risks / Trade-offs

| 决策 | Trade-off | 接受理由 |
|------|-----------|----------|
| Cron 轮询而非实时 | 最高 5 分钟延迟 | 大幅简化架构，对于投资监控场景可接受 |
| LLM Intent 解析 | 可能误解用户意图 | 通过确认流程缓解，用户体验优先 |
| 仅浏览器推送 | 需要用户授权 | Phase 1 快速交付，后续可扩展 |
| Stripe 手续费 | 2.9% + $0.30 | 行业标准，开发成本低 |

## Migration Plan

### Phase 1 完成后的数据库状态

1. 新增 7 个表，全部启用 RLS
2. 现有表不变，无破坏性变更
3. 新增 5 个 Cron 触发器

### 回滚策略

1. **数据库**: 保留迁移脚本，可执行 `DROP TABLE` 回滚
2. **Cron**: 删除 `wrangler.toml` 中的触发器配置
3. **前端**: 功能模块隔离，可独立禁用

## Open Questions

1. **Email 通知**: 是否需要作为浏览器推送的备份？如果需要，推荐使用 Resend 或 SendGrid？

2. **对话配额**: 对话式 Agent 的 LLM 调用是否计入用户配额？建议: 是，计入 `monthly_agent_conversations`

3. **数据保留**: Free 用户的数据保留期 7 天是否合理？建议: 可接受，Agent 执行日志更重要

4. **API 限流**: 是否需要额外的 IP 级别限流？建议: Phase 1 依赖配额系统，Phase 2 考虑添加

5. **国际化**: Agent 对话是否需要支持多语言？建议: Phase 1 仅中文，后续根据用户分布决定
