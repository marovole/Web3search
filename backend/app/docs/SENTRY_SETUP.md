# Sentry配置指南

Web3 Search API 使用 Sentry 进行错误追踪和性能监控。本文档提供完整的配置指南。

## 目录

1. [快速开始](#快速开始)
2. [环境变量配置](#环境变量配置)
3. [Sentry项目设置](#sentry项目设置)
4. [集成验证](#集成验证)
5. [高级配置](#高级配置)
6. [故障排查](#故障排查)

---

## 快速开始

### 1. 创建Sentry项目

1. 访问 [Sentry.io](https://sentry.io/)
2. 注册/登录账号
3. 创建新组织（如果是首次使用）
4. 点击"Create Project"
5. 选择平台：**Python - FastAPI**
6. 输入项目名称：`web3search-api`
7. 复制生成的DSN（形如：`https://xxxxx@o12345.ingest.sentry.io/67890`）

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# Sentry配置
SENTRY_DSN=https://xxxxx@o12345.ingest.sentry.io/67890
ENVIRONMENT=production  # 或 development, staging
```

### 3. 安装依赖

```bash
pip install sentry-sdk[fastapi]
```

### 4. 验证集成

启动应用后，查看日志：

```
✅ Sentry initialized: environment=production
```

---

## 环境变量配置

### 必填变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SENTRY_DSN` | Sentry项目DSN | `https://xxxxx@o12345.ingest.sentry.io/67890` |
| `ENVIRONMENT` | 运行环境 | `development`, `staging`, `production` |

### 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `API_VERSION` | 应用版本号（用于Release标签） | `1.0.0` |
| `DEBUG` | 是否为调试模式 | `false` |

### 环境差异

**Development（开发环境）**：
- `traces_sample_rate=1.0`（100%性能追踪）
- `sample_rate=1.0`（100%错误采样）
- 所有日志级别（DEBUG+）

**Staging（预发布环境）**：
- `traces_sample_rate=0.5`（50%性能追踪）
- `sample_rate=0.8`（80%错误采样）
- INFO级别及以上

**Production（生产环境）**：
- `traces_sample_rate=0.1`（10%性能追踪，节省配额）
- `sample_rate=0.5`（50%错误采样）
- WARNING级别及以上

---

## Sentry项目设置

### 1. 基础设置

在Sentry项目的 Settings → General：

| 设置项 | 推荐值 |
|--------|--------|
| **Platform** | Python - FastAPI |
| **Default Environment** | production |
| **Resolve in Next Release** | ✅ 启用 |
| **Auto-assign to Issue Owner** | ✅ 启用 |

### 2. 集成配置

我们的集成包含：

- ✅ **FastAPI**：自动追踪HTTP请求
- ✅ **SQLAlchemy**：数据库查询性能监控
- ✅ **Redis**：缓存操作监控
- ✅ **Celery**：异步任务错误追踪
- ✅ **Logging**：结构化日志集成

配置代码位于 `app/core/monitoring.py:43-57`

### 3. Release追踪

Release标签使用应用版本号（`API_VERSION`环境变量）。

**配置Git集成**（可选）：
1. Settings → Integrations → GitHub
2. 连接GitHub仓库
3. 启用 "Create Releases Automatically"
4. Release将自动关联Git Commit

### 4. 过滤规则

**已配置的过滤**（`app/core/monitoring.py:78-103`）：

- ❌ 过滤健康检查端点错误（`/health`）
- ❌ 过滤用户主动中断（`KeyboardInterrupt`）
- ✅ 保留所有业务错误和系统错误

**自定义过滤**：

修改 `before_send_filter()` 函数添加更多过滤规则。

---

## 集成验证

### 1. 测试错误追踪

```python
# 在任意端点中抛出测试异常
from app.core.monitoring import capture_exception

try:
    raise ValueError("Sentry测试错误")
except Exception as e:
    capture_exception(e, extra={"test": True})
```

访问该端点后，在Sentry中应该看到新的Issue。

### 2. 测试性能监控

```python
from app.core.monitoring import trace_operation

with trace_operation("test_operation", {"user_id": "123"}):
    # 执行耗时操作
    await some_slow_function()
```

在 Sentry → Performance 中查看事务追踪。

### 3. 测试自定义指标

```python
from app.core.monitoring import metrics

metrics.record_api_call(
    endpoint="/api/v1/test",
    method="GET",
    status_code=200,
    duration=0.123
)
```

在 Sentry → Insights → Custom Metrics 中查看。

### 4. 验证清单

- [ ] 应用启动时看到 "✅ Sentry initialized" 日志
- [ ] 手动触发错误后，Sentry中创建了新Issue
- [ ] Issue包含完整的堆栈追踪和上下文信息
- [ ] Performance页面显示API事务数据
- [ ] 自定义指标正常记录

---

## 高级配置

### 1. 采样率调优

**性能追踪采样率**（`traces_sample_rate`）：

- 高流量应用：0.01-0.1（1%-10%）
- 中等流量：0.1-0.5（10%-50%）
- 低流量/开发：1.0（100%）

**错误采样率**（`sample_rate`）：

- 建议生产环境：0.5-1.0（50%-100%）
- 根据配额调整

### 2. 自定义标签

在 `trace_operation()` 中添加标签：

```python
with trace_operation("llm_call", {
    "model": "llama-3.3-70b",
    "user_id": user_id,
    "symbol": symbol
}):
    response = await llm_generate(...)
```

标签会自动添加到Sentry事件中，便于过滤和分组。

### 3. 面包屑（Breadcrumbs）

Sentry自动记录：
- HTTP请求
- 数据库查询
- Redis操作
- 日志消息（INFO+）

最大保留50条面包屑（`max_breadcrumbs=50`）。

### 4. 上下文信息

**用户上下文**（未来实现认证后）：

```python
import sentry_sdk

sentry_sdk.set_user({"id": user_id, "email": user_email})
```

**额外上下文**：

```python
sentry_sdk.set_context("crypto_query", {
    "symbol": "BTC",
    "timeframe": "24h",
    "mode": "quick_chat"
})
```

### 5. 敏感信息脱敏

**当前配置**：`send_default_pii=False`（不发送个人身份信息）

**自动脱敏**：
- 环境变量中的密钥（`*_KEY`, `*_SECRET`, `*_PASSWORD`）
- HTTP请求中的Authorization头
- 数据库连接字符串

**手动脱敏**：

```python
def before_send_filter(event, hint):
    # 移除敏感字段
    if "request" in event:
        if "headers" in event["request"]:
            event["request"]["headers"].pop("Authorization", None)
    return event
```

---

## 故障排查

### 问题1：看不到错误上报

**可能原因**：
1. `SENTRY_DSN` 未配置或配置错误
2. `sentry-sdk` 未安装
3. 错误被 `before_send_filter()` 过滤

**解决方法**：
1. 检查环境变量：`echo $SENTRY_DSN`
2. 验证安装：`pip list | grep sentry`
3. 查看应用启动日志
4. 临时禁用过滤器测试

### 问题2：性能数据缺失

**可能原因**：
1. `traces_sample_rate=0`（未启用）
2. 采样率太低，数据未被采样
3. 端点未添加性能追踪

**解决方法**：
1. 检查配置：`traces_sample_rate >= 0.1`
2. 临时提高采样率测试
3. 使用 `trace_operation()` 包装关键操作

### 问题3：配额耗尽

**现象**：Sentry返回429错误

**解决方法**：
1. 降低采样率（`sample_rate`, `traces_sample_rate`）
2. 添加更多过滤规则
3. 升级Sentry计划
4. 使用 `before_send_filter()` 过滤噪音

### 问题4：大量重复Issue

**解决方法**：
1. 在Sentry中合并相似Issue
2. 设置 Fingerprint 规则
3. 使用 `before_send()` 聚合错误

### 问题5：性能影响

**Sentry开销**：
- 错误追踪：< 1ms
- 性能追踪：2-5ms（取决于采样率）

**优化建议**：
- 生产环境使用低采样率（10%）
- 仅在关键路径添加自定义追踪
- 使用异步发送（SDK默认行为）

---

## 参考资源

### 官方文档

- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [FastAPI集成](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [性能监控](https://docs.sentry.io/product/performance/)
- [告警配置](https://docs.sentry.io/product/alerts/)

### 内部资源

- **代码实现**：`app/core/monitoring.py`
- **监控指南**：`app/docs/MONITORING_GUIDE.md`
- **告警规则**：`app/config/sentry_alerts.json`
- **Dashboard配置**：`app/tools/sentry_dashboard.py`

### 社区资源

- [Sentry社区论坛](https://forum.sentry.io/)
- [GitHub Issues](https://github.com/getsentry/sentry-python/issues)

---

## 维护清单

### 每月检查
- [ ] 配额使用情况（避免超限）
- [ ] Issue解决率（目标 > 80%）
- [ ] 新增错误类型（及时修复）
- [ ] 性能回归（P95延迟变化）

### 每季度检查
- [ ] 告警规则有效性
- [ ] 采样率调优
- [ ] 过滤规则更新
- [ ] Release追踪准确性

### 版本升级
- [ ] 查看SDK更新日志
- [ ] 测试环境验证
- [ ] 生产环境逐步升级
- [ ] 监控错误率变化

---

**版本**：v1.0.0
**最后更新**：2025-01-27
**维护者**：Web3Search Team
**反馈渠道**：GitHub Issues
