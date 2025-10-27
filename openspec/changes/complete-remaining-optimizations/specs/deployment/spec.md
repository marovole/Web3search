# Deployment Specification - Phase 14 Deltas

## MODIFIED Requirements

### Requirement: Production Monitoring
The system SHALL implement comprehensive monitoring and alerting in production environment to ensure rapid problem detection and resolution. Monitoring SHALL cover application performance, error tracking, business metrics, and infrastructure health.

系统必须在生产环境实现全面的监控和告警，确保快速发现和解决问题。监控覆盖应用性能、错误追踪、业务指标和基础设施健康。

**监控目标**：
- **故障发现时间（MTTD）**: <5分钟
- **故障修复时间（MTTR）**: <15分钟
- **告警准确率**: >90%（减少误报）
- **监控覆盖率**: 100%关键路径

**监控工具**：
- Sentry（错误追踪 + 性能监控）
- Railway/Render自带监控（基础设施）
- 自定义指标（业务KPI）

#### Scenario: Error detection and alerting
- **WHEN** 生产环境发生未捕获异常
- **THEN** Sentry自动捕获错误
- **AND** 生成错误报告（堆栈、上下文、用户影响）
- **AND** 发送Slack通知到#alerts频道
- **AND** 开发团队在5分钟内收到告警

#### Scenario: Performance degradation detection
- **WHEN** API P95延迟超过3秒（持续5分钟）
- **THEN** Sentry告警规则触发
- **AND** 发送Slack通知："⚠️ API响应时间异常（P95: 3.2s）"
- **AND** Dashboard显示受影响的端点和时间段
- **AND** 开发团队查看性能追踪，定位瓶颈

#### Scenario: Data source failure detection
- **WHEN** CoinGecko成功率<90%（10分钟窗口）
- **THEN** 自定义告警触发
- **AND** 发送Slack通知："🔴 CoinGecko API成功率: 85%"
- **AND** Dashboard显示失败原因分布（超时/限流/5xx）
- **AND** 系统自动切换到fallback数据源

### Requirement: Infrastructure Health Checks
The system SHALL provide health check endpoints for monitoring service availability and dependency status.

系统必须提供健康检查端点，用于监控服务可用性和依赖项状态。

**健康检查端点**：
- `/health` - 基础健康检查（HTTP 200）
- `/health/database` - 数据库连接状态
- `/health/redis` - Redis连接状态
- `/health/dependencies` - 外部API状态（CoinGecko、OpenRouter）

#### Scenario: Full health check success
- **WHEN** 调用GET /health/dependencies
- **THEN** 系统检查所有依赖项
- **AND** 返回200 OK
- **AND** 响应体包含：
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-10-26T15:30:00Z",
    "dependencies": {
      "database": {"status": "up", "latency_ms": 5},
      "redis": {"status": "up", "latency_ms": 2},
      "coingecko": {"status": "up", "latency_ms": 150},
      "openrouter": {"status": "up", "latency_ms": 200}
    }
  }
  ```

#### Scenario: Partial health check failure
- **WHEN** 调用GET /health/dependencies
- **AND** Redis连接失败
- **THEN** 返回503 Service Unavailable
- **AND** 响应体包含：
  ```json
  {
    "status": "degraded",
    "timestamp": "2025-10-26T15:30:00Z",
    "dependencies": {
      "database": {"status": "up", "latency_ms": 5},
      "redis": {"status": "down", "error": "Connection timeout"},
      "coingecko": {"status": "up", "latency_ms": 150},
      "openrouter": {"status": "up", "latency_ms": 200}
    }
  }
  ```

#### Scenario: Health check timeout
- **WHEN** 调用GET /health/database
- **AND** 数据库查询超过5秒
- **THEN** 健康检查超时
- **AND** 返回503 Service Unavailable
- **AND** 记录错误日志："health_check_timeout", component="database"

## ADDED Requirements

### Requirement: Sentry Dashboard Configuration
The system SHALL configure Sentry Dashboard to display key business metrics and performance data.

系统必须配置Sentry Dashboard，显示关键业务指标和性能数据。

**Dashboard组成**：
1. **Overview**: 错误率、P95延迟、请求量、可用性
2. **API Performance**: 各端点响应时间、吞吐量
3. **Data Sources**: 各数据源成功率、响应时间、fallback频率
4. **Business Metrics**: Quick Chat使用量、Deep Research完成率、用户满意度

#### Scenario: Dashboard显示实时指标
- **WHEN** 开发团队打开Sentry Dashboard
- **THEN** 显示过去24小时的数据
- **AND** Overview面板显示：
  - 错误率: 0.5%（绿色）
  - P95延迟: 1.2秒（绿色）
  - 请求量: 15,000次
  - 可用性: 99.8%
- **AND** 数据每分钟自动刷新

#### Scenario: Dashboard钻取分析
- **WHEN** 用户点击"API Performance"面板
- **AND** 选择"/api/v1/quick-chat"端点
- **THEN** 显示该端点的详细数据：
  - P50/P95/P99延迟趋势图
  - 错误率时间序列
  - 慢请求样本（>2秒）
  - 地域分布（如果有CDN）

### Requirement: Alert Rules Configuration
The system SHALL configure reasonable alert rules to balance timeliness and accuracy.

系统必须配置合理的告警规则，平衡及时性和准确性。

**告警规则**：

| 指标 | 阈值 | 窗口 | 通道 | 优先级 |
|------|------|------|------|--------|
| 错误率 | >5% | 1分钟 | Slack #alerts | P1 |
| P95延迟 | >3秒 | 5分钟 | Slack #alerts | P2 |
| 数据源成功率 | <90% | 10分钟 | Slack #alerts | P2 |
| 可用性 | <99% | 30分钟 | Email + Slack | P1 |
| 磁盘空间 | >90% | 5分钟 | Slack #ops | P3 |

#### Scenario: Critical alert - high error rate
- **WHEN** 错误率在1分钟内超过5%
- **THEN** 触发P1告警
- **AND** 发送Slack通知到#alerts：
  ```
  🚨 P1 CRITICAL: High Error Rate
  Current: 7.2% (threshold: 5%)
  Affected: /api/v1/quick-chat
  Time: 2025-10-26 15:30:00
  Dashboard: https://sentry.io/...
  ```
- **AND** @mention on-call工程师

#### Scenario: Warning alert - high latency
- **WHEN** P95延迟在5分钟内超过3秒
- **THEN** 触发P2告警
- **AND** 发送Slack通知到#alerts：
  ```
  ⚠️ P2 WARNING: High API Latency
  Current P95: 3.2s (threshold: 3s)
  Affected: /api/v1/deep-research
  Time: 2025-10-26 15:30:00
  Investigate: https://sentry.io/...
  ```

#### Scenario: Alert resolution
- **WHEN** 错误率降回5%以下
- **AND** 持续5分钟
- **THEN** 自动解决告警
- **AND** 发送Slack通知："✅ RESOLVED: High Error Rate (持续时间: 12分钟)"

### Requirement: Custom Business Metrics
The system SHALL track and record key business metrics for product decisions and performance optimization.

系统必须追踪和记录业务关键指标，用于产品决策和性能优化。

**业务指标**：
- `quick_chat.request_count` - Quick Chat请求数（按symbol、时段）
- `quick_chat.cache_hit_rate` - 缓存命中率
- `quick_chat.positive_feedback_rate` - 用户正面反馈率
- `deep_research.completion_rate` - Deep Research完成率
- `deep_research.avg_duration` - 平均生成时间
- `data_source.success_rate` - 各数据源成功率
- `data_source.fallback_count` - Fallback触发次数

#### Scenario: Record Quick Chat metrics
- **WHEN** Quick Chat请求成功
- **THEN** 记录指标：
  ```python
  metrics.incr("quick_chat.request_count", tags={"symbol": "BTC", "hour": "15"})
  metrics.distribution("quick_chat.response_time", value=1200, unit="millisecond")
  metrics.incr("quick_chat.cache_hit" if cached else "quick_chat.cache_miss")
  ```

#### Scenario: Calculate daily metrics
- **WHEN** 每天UTC 00:00
- **THEN** Celery定时任务计算昨日指标：
  - Quick Chat总请求数
  - 缓存命中率
  - 平均响应时间
  - 用户满意度（正面反馈率）
- **AND** 存储到数据库
- **AND** 发送日报到Slack #metrics

#### Scenario: Business metric alerting
- **WHEN** Quick Chat正面反馈率<70%（7天移动平均）
- **THEN** 触发业务告警
- **AND** 发送Slack通知到#product：
  ```
  📊 Business Alert: Quick Chat Satisfaction Declining
  7-day avg positive feedback: 65% (threshold: 70%)
  Previous period: 78%
  Action: Review recent prompt changes
  ```

### Requirement: Log Aggregation and Search
The system SHALL provide structured logs with support for fast querying and analysis.

系统必须提供结构化日志，支持快速查询和分析。

**日志格式**：JSON格式（structlog）
**日志级别**：DEBUG（开发）、INFO（生产）、ERROR（错误）
**日志字段**：
- `timestamp` - ISO 8601格式
- `level` - 日志级别
- `event` - 事件名称（如"quick_chat_request"）
- `request_id` - UUID追踪请求
- `user_id` - 用户ID（如有）
- `symbol` - 加密货币符号
- `duration_ms` - 操作耗时
- `error` - 错误消息（如有）

#### Scenario: Query logs by request_id
- **WHEN** 开发团队调查用户报告的问题
- **AND** 用户提供request_id="550e8400-e29b..."
- **THEN** 在日志系统中搜索：
  ```
  request_id:"550e8400-e29b-41d4-a716-446655440000"
  ```
- **AND** 返回该请求的所有日志事件（按时间排序）：
  1. quick_chat_request (15:30:00.000)
  2. fetching_market_data (15:30:00.100)
  3. data_fetch_success (15:30:00.350)
  4. generating_answer (15:30:00.400)
  5. quick_chat_success (15:30:01.200)

#### Scenario: Query logs by error type
- **WHEN** 开发团队分析CoinGecko失败原因
- **THEN** 搜索日志：
  ```
  event:"data_fetch_failed" AND source:"coingecko"
  ```
- **AND** 按error字段聚合：
  - "rate_limit": 45次（60%）
  - "timeout": 20次（27%）
  - "500_error": 10次（13%）
- **AND** 识别主要问题：rate limit

#### Scenario: Real-time log streaming
- **WHEN** 开发团队需要实时查看生产日志
- **THEN** 使用Railway/Render日志流功能
- **AND** 过滤特定条件："level:ERROR"
- **AND** 实时显示错误日志

### Requirement: Deployment Documentation
The system SHALL provide complete deployment and operations documentation to reduce maintenance cost.

系统必须提供完整的部署和运维文档，降低维护成本。

**文档内容**：
1. **API文档** (docs/api.md)
   - 所有8个端点的详细说明
   - 请求/响应示例（curl、Python、JavaScript）
   - 错误码完整列表
   - 认证和授权指南

2. **运维文档** (docs/operations.md)
   - 部署指南（Railway、Render、Vercel）
   - 监控和告警配置
   - 故障排查手册（10+常见问题）
   - 数据库维护（备份、恢复、迁移）
   - 扩容指南

3. **开发文档** (docs/development.md)
   - 本地开发环境设置
   - 代码规范和审查清单
   - 测试编写指南
   - 贡献指南

#### Scenario: Developer查阅API文档
- **WHEN** 第三方开发者想集成Quick Chat API
- **THEN** 访问docs/api.md
- **AND** 找到"/api/v1/quick-chat"端点说明
- **AND** 看到完整的curl示例：
  ```bash
  curl -X POST https://api.web3search.ai/api/v1/quick-chat \
    -H "Content-Type: application/json" \
    -d '{"query": "BTC价格如何？", "symbol": "BTC"}'
  ```
- **AND** 理解响应格式和错误码
- **AND** 成功集成API

#### Scenario: 运维工程师排查问题
- **WHEN** 生产环境出现"数据库连接池耗尽"错误
- **THEN** 访问docs/operations.md故障排查手册
- **AND** 找到"数据库连接问题"章节
- **AND** 按步骤排查：
  1. 检查连接池配置（max_size=50）
  2. 查看当前活跃连接数（Railway Dashboard）
  3. 检查是否有慢查询（Sentry Performance）
  4. 检查是否有连接泄漏（代码审查）
- **AND** 定位问题：某个查询未正确关闭连接
- **AND** 应用修复（增加超时控制）

#### Scenario: 新工程师入职
- **WHEN** 新工程师加入团队
- **THEN** 阅读docs/development.md
- **AND** 按步骤设置本地环境：
  1. 克隆仓库
  2. 安装依赖（Python 3.11、PostgreSQL、Redis）
  3. 配置环境变量（.env.local）
  4. 运行数据库迁移
  5. 启动开发服务器
  6. 运行测试套件
- **AND** 在1小时内完成环境搭建
- **AND** 能够开始开发

### Requirement: Automated Deployment Pipeline
The system SHALL implement automated deployment pipeline to ensure fast and reliable version releases.

系统必须实现自动化部署流程，确保快速、可靠的版本发布。

**部署流程**：
1. **开发阶段**: 本地开发 → 提交PR
2. **CI阶段**: GitHub Actions运行测试和linting
3. **部署阶段**: 合并到main → 自动部署到生产环境
4. **验证阶段**: 健康检查 → 监控指标

#### Scenario: Automated deployment on merge
- **WHEN** PR合并到main分支
- **THEN** GitHub Actions触发CI/CD
- **AND** 运行测试套件（pytest）
- **AND** 测试通过后，部署到Railway（后端）
- **AND** 部署到Vercel（前端）
- **AND** 等待健康检查通过（/health endpoint）
- **AND** 发送Slack通知："✅ Deployment successful (v1.2.3)"

#### Scenario: Deployment failure and rollback
- **WHEN** 部署到生产环境
- **AND** 健康检查失败（/health返回503）
- **THEN** 自动回滚到上一版本
- **AND** 发送Slack告警："🚨 Deployment failed, rolled back to v1.2.2"
- **AND** 保留失败版本日志供排查

#### Scenario: Manual deployment approval
- **WHEN** 进行重大版本发布（Breaking Changes）
- **THEN** 需要手动批准部署
- **AND** 在Slack #deployments频道发送通知
- **AND** 需要@mention Team Lead批准
- **AND** 批准后执行部署

## Implementation Notes

### Sentry配置

```python
# backend/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,  # dev/staging/prod
    release=f"web3search-backend@{settings.VERSION}",
    traces_sample_rate=0.1,  # 10%性能追踪采样
    profiles_sample_rate=0.1,  # 10%性能分析采样
    integrations=[
        FastApiIntegration(
            transaction_style="endpoint",  # 按端点分组事务
        ),
        SqlalchemyIntegration(),
    ],
    before_send=filter_sensitive_data,  # 过滤敏感信息
)

def filter_sensitive_data(event, hint):
    """过滤敏感信息（API keys、密码等）"""
    if "request" in event:
        headers = event["request"].get("headers", {})
        headers.pop("Authorization", None)
        headers.pop("X-API-Key", None)
    return event
```

### 自定义指标

```python
# backend/app/core/metrics.py
from sentry_sdk import metrics

class MetricsCollector:
    @staticmethod
    def record_quick_chat(symbol: str, response_time: float, cached: bool):
        """记录Quick Chat指标"""
        metrics.incr("quick_chat.request_count", tags={"symbol": symbol})
        metrics.distribution("quick_chat.response_time", value=response_time, unit="millisecond")

        if cached:
            metrics.incr("quick_chat.cache_hit")
        else:
            metrics.incr("quick_chat.cache_miss")

    @staticmethod
    def record_data_source(source: str, success: bool, response_time: float | None = None):
        """记录数据源指标"""
        metrics.incr("data_source.request", tags={"source": source})

        if success:
            metrics.incr("data_source.success", tags={"source": source})
            if response_time:
                metrics.distribution("data_source.response_time", value=response_time, tags={"source": source})
        else:
            metrics.incr("data_source.failure", tags={"source": source})

    @staticmethod
    def record_fallback(from_source: str, to_source: str):
        """记录fallback事件"""
        metrics.incr("data_source.fallback", tags={"from": from_source, "to": to_source})
```

### 健康检查端点

```python
# backend/app/api/v1/health.py
from fastapi import APIRouter, Response

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def basic_health():
    """基础健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@router.get("/database")
async def database_health(db: AsyncSession = Depends(get_db)):
    """数据库健康检查"""
    try:
        start = time.time()
        await db.execute("SELECT 1")
        latency = (time.time() - start) * 1000

        return {
            "status": "up",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return Response(
            content=json.dumps({"status": "down", "error": str(e)}),
            status_code=503
        )

@router.get("/redis")
async def redis_health(redis: Redis = Depends(get_redis)):
    """Redis健康检查"""
    try:
        start = time.time()
        await redis.ping()
        latency = (time.time() - start) * 1000

        return {
            "status": "up",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return Response(
            content=json.dumps({"status": "down", "error": str(e)}),
            status_code=503
        )

@router.get("/dependencies")
async def dependencies_health():
    """所有依赖项健康检查"""
    results = {}

    # 并行检查所有依赖
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_coingecko(),
        check_openrouter(),
        return_exceptions=True
    )

    results["database"], results["redis"], results["coingecko"], results["openrouter"] = checks

    # 判断整体状态
    all_up = all(r.get("status") == "up" for r in results.values() if isinstance(r, dict))
    status = "healthy" if all_up else "degraded"

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "dependencies": results
    }
```

### 告警Slack通知

```python
# backend/app/core/alerts.py
import aiohttp

async def send_slack_alert(level: str, title: str, message: str, details: dict = None):
    """发送Slack告警"""
    emoji = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
        "resolved": "✅"
    }

    payload = {
        "text": f"{emoji.get(level, '📊')} {level.upper()}: {title}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n{message}"
                }
            }
        ]
    }

    if details:
        payload["blocks"].append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*{k}*: {v}"}
                for k, v in details.items()
            ]
        })

    async with aiohttp.ClientSession() as session:
        await session.post(settings.SLACK_WEBHOOK_URL, json=payload)
```

## Testing Requirements

### 健康检查测试
- 测试各健康检查端点（成功/失败场景）
- 测试健康检查超时处理
- 测试并发健康检查

### 监控指标测试
- 验证指标正确记录（Sentry SDK）
- 测试告警规则触发条件
- Mock Slack通知，验证消息格式

### 文档测试
- 验证API文档示例可执行
- 测试故障排查手册步骤
- 验证部署指南完整性

### 端到端测试
- 模拟生产环境部署
- 触发告警并验证通知
- 测试日志查询功能
