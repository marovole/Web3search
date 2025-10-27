# 监控运维指南

Web3 Search API 监控系统完整运维手册。

## 目录

1. [监控概览](#监控概览)
2. [Sentry使用](#sentry使用)
3. [告警处理](#告警处理)
4. [常见问题](#常见问题)
5. [应急响应](#应急响应)
6. [最佳实践](#最佳实践)

---

## 监控概览

### 监控架构

```
┌──────────────────┐
│   Application    │
│   (FastAPI)      │
└─────────┬────────┘
          │
    ┌─────┴─────┐
    │           │
┌───▼───┐   ┌──▼──────┐
│Sentry │   │Structured│
│       │   │  Logs    │
└───┬───┘   └──┬──────┘
    │          │
┌───▼──────────▼───┐
│  Alert System     │
│  (Slack/Email)    │
└──────────────────┘
```

### 监控层级

| 层级 | 工具 | 指标 |
|------|------|------|
| **错误追踪** | Sentry | 异常、错误率、堆栈追踪 |
| **性能监控** | Sentry | P95延迟、事务追踪、慢查询 |
| **业务指标** | Custom Metrics | 报告生成、数据采集、用户行为 |
| **日志分析** | Structured Logs | request_id、上下文信息 |

---

## Sentry使用

### 1. Dashboard访问

**生产环境Dashboard**：
- URL: https://sentry.io/organizations/web3search/issues/
- 关键指标Dashboard：查看错误率、P95延迟、请求量
- 完整Dashboard：查看所有监控指标

**查看方式**：
1. 登录Sentry控制台
2. 选择项目：`web3search-api`
3. 导航到Dashboards → "Web3 Search - 关键指标"

### 2. Issues查看

**筛选条件**：
- 环境：production
- 时间范围：Last 24h
- 优先级：High/Medium

**关键字段**：
- `error.type`：错误类型
- `transaction`：API端点
- `user.id`：用户ID（如有）
- `environment`：运行环境

**快速操作**：
- 点击Issue查看详情
- 查看Breadcrumbs了解上下文
- 查看堆栈追踪定位代码
- 点击"Assign to"分配给负责人

### 3. Performance监控

**事务类型**：
| 事务 | 描述 | 正常范围 |
|------|------|---------|
| `/api/v1/chat/quick-chat` | Quick Chat API | < 3s |
| `deep_research` | Deep Research | < 30s |
| `data_collection` | 数据采集 | < 5s |
| `llm_call` | LLM调用 | < 5s |

**查看方式**：
1. Performance → Transactions
2. 选择事务类型
3. 查看P50/P75/P95/P99百分位数
4. 点击慢事务查看详情

### 4. Custom Metrics

**业务指标**：
- `report_generation`：报告生成成功率
- `data_collection`：数据源采集成功率
- `user_action`：用户行为追踪
- `cache_operation`：缓存命中率

**查看方式**：
1. Insights → Custom Metrics
2. 选择指标类型
3. 筛选时间范围和环境
4. 导出数据（如需）

---

## 告警处理

### 告警分类

#### 🔴 P0 - 紧急（立即处理）

**触发条件**：
- 错误率 > 5%
- P95延迟 > 3s
- 数据库/Redis连接失败

**处理流程**：
1. **确认问题**（1分钟内）
   - 检查Sentry Dashboard
   - 查看最近部署
   - 检查外部服务状态

2. **临时止血**（5分钟内）
   - 回滚最近部署（如需）
   - 重启服务（如需）
   - 切换到备用数据源

3. **根因分析**（30分钟内）
   - 查看详细日志
   - 分析错误堆栈
   - 定位问题代码

4. **修复上线**（2小时内）
   - 编写修复代码
   - 部署到staging验证
   - 部署到production
   - 验证问题解决

#### 🟡 P1 - 重要（24小时内）

**触发条件**：
- 数据源采集失败
- LLM调用失败（非致命）
- 新错误类型出现

**处理流程**：
1. 记录Issue到Jira/GitHub
2. 分配给相关负责人
3. 安排修复时间
4. 部署修复并验证

#### 🟢 P2 - 一般（本周内）

**触发条件**：
- 频繁重复错误（但不影响核心功能）
- 性能略有下降（未超阈值）
- 非关键功能故障

**处理流程**：
1. 添加到backlog
2. 下次sprint规划时处理
3. 优先级排序

### 告警示例及处理

#### 告警1：高错误率

**Slack通知**：
```
🔴 [ALERT] 高错误率
环境: production
错误率: 8.5% (阈值: 5%)
时间: 2025-01-27 14:30 UTC
查看: [链接]
```

**处理步骤**：
1. 点击链接进入Sentry
2. 查看错误类型分布（Top 3）
3. 查看是否集中在某个端点
4. 检查最近代码变更（`git log -5`）
5. 如果是新部署导致 → 立即回滚
6. 如果是外部服务问题 → 启用降级策略
7. 修复后发送"✅ RESOLVED"消息到Slack

#### 告警2：P95延迟过高

**Slack通知**：
```
🟡 [WARNING] P95延迟过高
端点: /api/v1/chat/deep-research
P95: 35s (阈值: 30s)
原因: LLM响应慢
建议: 考虑切换模型或增加超时
```

**处理步骤**：
1. 查看Performance Dashboard
2. 确认是否所有LLM调用都慢
3. 检查OpenRouter API状态
4. 临时切换到更快的模型
5. 优化Prompt（如需）
6. 监控是否恢复正常

#### 告警3：数据源失败

**Slack通知**：
```
🔴 [CRITICAL] 数据源失败
数据源: CoinGecko API
错误: 429 Too Many Requests
影响: 价格数据无法更新
```

**处理步骤**：
1. 确认是否超过API限额
2. 启用fallback数据源（CoinMarketCap）
3. 检查缓存是否有效
4. 调整采集频率（如需）
5. 联系CoinGecko支持（如持续）

---

## 常见问题

### Q1：Sentry中看到大量健康检查错误

**原因**：负载均衡器或监控工具频繁调用`/health`端点

**解决**：
- 已在`before_send_filter()`中过滤`/health`错误
- 如仍出现，检查过滤规则是否生效

### Q2：告警频繁触发但问题不明显

**原因**：阈值设置过低或存在瞬时波动

**解决**：
1. 查看告警规则配置（`app/config/sentry_alerts.json`）
2. 调整阈值或时间窗口
3. 增加"连续N次"条件

### Q3：Performance数据缺失

**原因**：`traces_sample_rate`设置过低

**解决**：
1. 检查环境变量：`SENTRY_DSN`是否配置
2. 临时提高采样率：`traces_sample_rate=1.0`（开发环境）
3. 生产环境建议：0.1-0.3

### Q4：Slack通知未收到

**检查清单**：
- [ ] `SLACK_WEBHOOK_URL`环境变量是否配置
- [ ] Slack webhook是否有效（测试发送）
- [ ] Sentry告警规则是否启用
- [ ] Slack频道是否正确（#alerts）

**测试方法**：
```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Sentry告警测试"}'
```

### Q5：配额耗尽

**现象**：Sentry返回429错误

**临时措施**：
1. 降低采样率（`sample_rate=0.5`, `traces_sample_rate=0.1`）
2. 添加更多过滤规则
3. 暂时禁用非关键告警

**长期方案**：
- 升级Sentry计划
- 优化错误处理（减少错误数）
- 使用自托管Sentry（成本更低）

---

## 应急响应

### 服务中断流程

**1. 发现问题**（1分钟）
- 告警通知
- 用户报告
- 监控发现

**2. 快速评估**（5分钟）
- 影响范围：全部用户 / 部分功能
- 严重程度：P0 / P1 / P2
- 根本原因：代码 / 基础设施 / 外部服务

**3. 止血措施**（15分钟）
- **代码问题**：回滚到上一稳定版本
- **基础设施**：重启服务、扩容资源
- **外部服务**：启用fallback、缓存降级

**4. 恢复服务**（30分钟）
- 验证服务可用性
- 检查关键功能
- 通知利益相关方

**5. 事后分析**（24小时内）
- 编写事故报告
- 根因分析（RCA）
- 改进措施

### 回滚流程

**条件判断**：
- 新部署后错误率激增
- 核心功能不可用
- 性能严重下降

**Railway回滚**：
```bash
# 查看最近部署
railway logs

# 回滚到上一版本
cd backend
git reset --hard HEAD~1
railway up --yes
```

**Render回滚**：
1. 登录Render Dashboard
2. 选择服务 → Manual Deploy
3. 选择上一个成功的commit
4. 点击Deploy

**验证**：
```bash
# 检查健康状态
curl https://web3search-api.onrender.com/health

# 测试Quick Chat
curl -X POST https://web3search-api.onrender.com/api/v1/chat/quick-chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'
```

---

## 最佳实践

### 监控清单

**每日检查**（5分钟）：
- [ ] 查看Sentry Dashboard（错误率、P95延迟）
- [ ] 检查未解决的P0/P1 Issues
- [ ] 查看Slack #alerts频道

**每周检查**（30分钟）：
- [ ] 分析错误趋势（week-over-week）
- [ ] 检查性能回归
- [ ] 审查告警规则有效性
- [ ] 更新runbook（如有新问题）

**每月检查**（2小时）：
- [ ] 审查配额使用情况
- [ ] 优化采样率
- [ ] 清理已解决的Issues
- [ ] 团队培训（新成员onboarding）

### 运维技巧

**1. 使用标签（Tags）**
```python
from app.core.monitoring import trace_operation

with trace_operation("data_fetch", {
    "source": "coingecko",
    "symbol": "BTC",
    "env": "production"
}):
    data = fetch_data()
```

**2. 添加面包屑（Breadcrumbs）**
```python
import sentry_sdk

sentry_sdk.add_breadcrumb(
    category='query',
    message='User searched for BTC',
    level='info',
)
```

**3. 设置用户上下文**（未来实现认证后）
```python
sentry_sdk.set_user({"id": user_id, "email": user_email})
```

**4. 自定义指标**
```python
from app.core.monitoring import metrics

metrics.record_user_action(
    action_type="report_generated",
    user_id=user_id,
    metadata={"symbol": "BTC", "type": "deep_research"}
)
```

### 告警优化

**减少噪音**：
- 合并相似Issue
- 调整阈值（避免误报）
- 使用"连续N次"触发条件
- 过滤非关键错误

**提高覆盖率**：
- 为每个关键功能设置告警
- 监控外部依赖（数据源、LLM）
- 设置业务指标告警（报告生成失败率）

**告警分级**：
- P0：立即通知（Slack + Email + SMS）
- P1：工作时间通知（Slack + Email）
- P2：每日摘要（Email）

---

## 参考资源

### 内部文档
- [Sentry配置指南](./SENTRY_SETUP.md)
- [故障排查指南](./TROUBLESHOOTING.md)
- [部署指南](./DEPLOYMENT.md)

### 外部资源
- [Sentry官方文档](https://docs.sentry.io/)
- [FastAPI最佳实践](https://fastapi.tiangolo.com/best-practices/)
- [SRE Book](https://sre.google/books/)

### 紧急联系

- **On-Call工程师**：查看PagerDuty轮值表
- **团队Slack**：#engineering, #on-call
- **支持邮箱**：support@web3search.com

---

**版本**：v1.0.0
**最后更新**：2025-01-27
**维护者**：Web3Search SRE Team
**反馈渠道**：Slack #sre
