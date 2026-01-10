# Proposal: Add Proactive AI Agent System

## Why

Web3search 目前是一个**被动响应式**的研究平台——用户必须主动发起查询才能获得分析结果。这种模式存在以下痛点：

1. **错过时机**: 用户无法24/7监控市场，可能错过重要的价格变动或风险事件
2. **重复劳动**: 用户需要反复手动检查关注的项目状态
3. **信息过载**: 用户难以持续跟踪多个项目的动态
4. **价值上限**: 平台粘性有限，用户完成研究后缺乏持续使用的理由

**解决方案**: 引入**主动AI Agent系统**，实现：
- 持续监控用户关注的代币和项目
- 在满足条件时主动推送通知
- 通过自然语言对话配置监控规则（Level 3）
- 定期生成分析报告
- 免费/付费分层的商业模式

## What Changes

### 新增功能模块

| 模块 | 描述 | 优先级 |
|------|------|--------|
| **用户认证系统** | Supabase Auth 集成，用户注册/登录/会话管理 | P0 |
| **订阅付费系统** | Stripe 集成，Free/Pro/Team 三档定价 | P0 |
| **Watchlist** | 代币/项目收藏和批量管理 | P0 |
| **配额系统** | 用量限制和执行，防止滥用 | P0 |
| **Agent 任务系统** | 价格预警、风险监控、新闻速报等 Agent | P1 |
| **通知系统** | 浏览器推送（Web Push API） | P1 |
| **持仓诊断 Agent** | 定期生成持仓健康报告 | P2 |
| **机会发现 Agent** | 基于用户偏好推荐项目 | P2 |
| **对话式 Agent** | 自然语言配置监控规则 | P2 |
| **Agent Activity Log** | 扩展 Glass Box Panel，实时执行日志 | P2 |

### 数据库变更

**新增表:**
- `user_profiles` - 用户配置扩展（扩展 Supabase Auth）
- `watchlist` - 监控列表
- `agent_tasks` - Agent 任务配置
- `agent_runs` - Agent 执行日志
- `notifications` - 通知记录
- `user_quotas` - 用户配额追踪
- `push_subscriptions` - 浏览器推送订阅

**RLS 策略:** 所有新表启用 Row Level Security，确保用户数据隔离

### API 变更

**新增端点组:**

```
/api/v1/auth/*           # 认证代理
/api/v1/users/*          # 用户管理
/api/v1/watchlist/*      # 监控列表 CRUD
/api/v1/agents/*         # Agent 任务管理
/api/v1/agents/conversation/* # 对话式 Agent
/api/v1/notifications/*  # 通知管理
/api/v1/push/*           # 推送订阅管理
/api/v1/billing/*        # Stripe 订阅付费
```

### Cron 任务变更

**新增触发器:**

| Cron 表达式 | 任务 | 描述 |
|-------------|------|------|
| `*/5 * * * *` | price-check | 价格预警检查 |
| `0 * * * *` | news-brief | 新闻速报推送 |
| `0 0 * * 1` | weekly-portfolio | 每周持仓诊断 |
| `0 0 * * *` | quota-daily-reset | 每日配额重置 |
| `0 0 1 * *` | quota-monthly-reset | 每月配额重置 |

## Impact

### 受影响的现有模块

| 模块 | 影响程度 | 说明 |
|------|----------|------|
| `workers-api/src/index.ts` | 中等 | 新增路由和 Auth 中间件 |
| `workers-api/wrangler.toml` | 低 | 新增 Cron 触发器配置 |
| `frontend/src/App.tsx` | 中等 | 新增页面路由 |
| `frontend/src/components/` | 高 | 新增多个组件 |
| `supabase/migrations/` | 高 | 新增多个表迁移 |

### 新增依赖

**后端 (workers-api):**
- `web-push` - 浏览器推送通知
- `stripe` - 支付集成

**前端:**
- `@supabase/auth-helpers-react` - Auth UI 辅助（可选）

### 定价策略

| 功能 | Free | Pro ($9.9/月) | Team ($29.9/月) |
|------|------|---------------|-----------------|
| Watchlist | 5个代币 | 50个代币 | 无限制 |
| 价格预警 | 3个活跃 | 30个活跃 | 无限制 |
| 巨鲸追踪 | ❌ | ✅ 10个代币 | ✅ 无限制 |
| 风险监控 | 基础评分 | 实时+历史趋势 | 实时+历史+对比 |
| 新闻速报 | 每日1次 | 实时推送 | 实时+自定义源 |
| 持仓诊断 | ❌ | 每周1次 | 每日+自定义 |
| 机会发现 | ❌ | 每周3个 | 每日无限 |
| 对话式Agent | ❌ | 10次/月 | 100次/月 |
| Deep Research | 3次/天 | 20次/天 | 无限制 |
| 通知 | 浏览器推送 | +Email | +Webhook |
| 历史数据 | 7天 | 90天 | 365天 |

### 成本影响

| 项目 | 预估成本 |
|------|----------|
| Supabase (Free Plan) | $0 |
| Stripe 交易手续费 | 2.9% + $0.30/交易 |
| 额外 API 调用 | $10-50/月 (取决于用户量) |
| 总预估月成本 | $10-100/月 |

### 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 配额系统绕过 | 低 | 高 | 服务端双重验证 |
| 推送权限被拒 | 中 | 低 | 优雅降级，显示应用内通知 |
| Agent 无限循环 | 低 | 中 | 最大迭代次数限制 (5次) |
| Stripe Webhook 失败 | 低 | 高 | 重试队列 + 手动对账 |
| LLM Intent 误解 | 中 | 中 | 低置信度时要求用户确认 |

## Timeline

| Phase | 内容 | 预估工期 |
|-------|------|----------|
| Phase 1 | 用户认证 + 配额 + 订阅 | 2周 |
| Phase 2 | Watchlist + Agent 框架 | 1周 |
| Phase 3 | 价格预警 + 风险监控 Agent | 1.5周 |
| Phase 4 | 新闻速报 + 推送通知 | 1周 |
| Phase 5 | 持仓诊断 + 机会发现 | 1.5周 |
| Phase 6 | 对话式 Agent | 2周 |
| Phase 7 | Agent Activity Log | 1周 |
| Phase 8 | 测试 + 优化 + 文档 | 1周 |

**总计: 约 11 周**

## References

- [Supabase Auth 文档](https://supabase.com/docs/guides/auth)
- [Stripe Billing 文档](https://stripe.com/docs/billing)
- [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
