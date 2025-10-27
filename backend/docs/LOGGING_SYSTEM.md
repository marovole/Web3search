# 日志系统文档

## 概述

Web3search采用structlog实现结构化日志系统，提供：

- **结构化日志**：JSON格式，便于解析和查询
- **请求追踪**：自动生成request_id追踪完整请求链路
- **上下文传播**：contextvars实现跨异步调用的上下文传递
- **敏感信息保护**：自动脱敏API keys、密码等敏感数据
- **日志过滤**：排除健康检查等噪音日志
- **日志轮转**：按大小自动轮转（100MB），保留10个备份
- **多环境支持**：开发环境彩色输出，生产环境JSON格式

## 快速开始

### 1. 基础日志记录

```python
from app.core.structlog_config import get_logger

logger = get_logger(__name__)

# 简单日志
logger.info("user_login", user_id=123)

# 带多个字段
logger.info(
    "api_request",
    method="GET",
    url="/api/data",
    status_code=200,
    duration_ms=45.2
)

# 错误日志
try:
    risky_operation()
except Exception as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
```

### 2. 使用请求上下文

```python
from app.core.log_context import LogContext, log_context

# 方式1：手动设置
LogContext.set_request_id("req-123")
LogContext.set_user_id(456)
logger.info("processing")  # 自动包含request_id和user_id

# 方式2：使用context manager
with log_context(request_id="req-123", user_id=456, symbol="BTC"):
    logger.info("analyzing")  # 自动包含所有上下文
    perform_analysis()
```

### 3. 查询日志

```bash
# 按request_id查询
python scripts/query_logs.py --request-id abc-123

# 查询错误日志
python scripts/query_logs.py --level ERROR --limit 20

# 查询特定时间范围
python scripts/query_logs.py --since "2024-01-01 10:00:00"

# 获取请求追踪
python scripts/query_logs.py --request-id abc-123 --trace
```

## 日志级别

按严重程度从低到高：

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 调试信息 | 变量值、函数调用 |
| INFO | 一般信息 | 操作开始/完成、状态变更 |
| WARNING | 警告信息 | 性能下降、即将达到限制 |
| ERROR | 错误信息 | 操作失败、异常 |
| CRITICAL | 严重错误 | 系统崩溃、数据损坏 |

### 环境配置

- **开发环境**：DEBUG级别，彩色控制台输出
- **预发布环境**：INFO级别，JSON格式
- **生产环境**：INFO级别，JSON格式

```bash
# .env
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# .env.prod
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 核心功能

### 1. Request ID追踪

每个HTTP请求自动获得唯一的request_id（UUID），用于追踪完整的请求处理链路。

#### 中间件自动注入

```python
# main.py
from app.middleware.request_context import RequestContextMiddleware

app.add_middleware(RequestContextMiddleware)
```

#### 日志示例

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "log_level": "info",
  "event": "request_started",
  "request_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "method": "GET",
  "url": "/api/v1/chat/quick",
  "client_ip": "192.168.1.100"
}
```

#### 在代码中使用

```python
from fastapi import Request
from app.middleware.request_context import get_request_id

@app.get("/api/example")
async def example(request: Request):
    request_id = get_request_id(request)
    logger.info("processing_request", request_id=request_id)
```

### 2. 上下文传播

使用Python的contextvars实现上下文信息在异步调用链中传播。

#### 支持的上下文字段

- `request_id`：请求ID
- `user_id`：用户ID
- `symbol`：加密货币符号
- `conversation_id`：会话ID
- 自定义字段：任意键值对

#### 使用方法

```python
from app.core.log_context import LogContext, log_context, get_logger_with_context

# 方式1：手动设置/获取
LogContext.set_request_id("req-123")
LogContext.set_user_id(456)
LogContext.set_symbol("BTC")
LogContext.set_custom("analysis_type", "technical")

# 获取
request_id = LogContext.get_request_id()
context = LogContext.get_all()  # 获取所有上下文

# 方式2：Context Manager（推荐）
with log_context(request_id="req-123", user_id=456):
    logger.info("step1")  # 自动包含request_id和user_id
    await async_operation()
    logger.info("step2")  # 仍然包含上下文

# 方式3：获取带上下文的logger
logger = get_logger_with_context(__name__)
logger.info("processing")  # 自动包含当前上下文
```

#### 嵌套上下文

```python
with log_context(request_id="outer-req"):
    logger.info("outer")  # request_id=outer-req

    with log_context(user_id=123):
        logger.info("inner")  # request_id=outer-req, user_id=123

    logger.info("back_to_outer")  # request_id=outer-req, user_id=None
```

### 3. 敏感信息脱敏

自动检测并脱敏敏感信息，防止泄露。

#### 自动脱敏的字段

- `password`
- `token`
- `secret`
- `api_key`, `apikey`
- `authorization`, `auth`
- `key`
- `dsn`
- `DATABASE_URL`

#### 脱敏规则

- 长度≤8：替换为 `***`
- 长度>8：显示前4位和后4位，中间为`...`

#### 示例

```python
logger.info(
    "api_call",
    api_key="sk-1234567890abcdefghij"  # 记录为: sk-1...ghij
)

logger.info(
    "config_loaded",
    database_url="postgres://user:pass@host:5432/db"  # 记录为: post...l/db
)

# 嵌套字典也会脱敏
logger.info(
    "settings",
    config={
        "api_key": "secret-key-123456",  # 脱敏
        "timeout": 30  # 不脱敏
    }
)
```

### 4. 日志过滤

过滤掉不需要的日志，减少噪音。

#### 默认过滤规则

- 健康检查端点：`/health`, `/healthz`, `/metrics`
- 静态资源：`favicon.ico`
- 系统事件：`health_check`, `metrics_request`

#### 自定义过滤

```python
from app.core.log_filters import setup_log_filters
import logging

logger = logging.getLogger("my_logger")

# 配置过滤器
setup_log_filters(
    logger,
    exclude_health_checks=True,
    min_level=logging.INFO,
    excluded_patterns=[r"test.*", r"debug.*"]
)
```

#### Structlog事件过滤

```python
from app.core.log_filters import StructlogEventFilter
import structlog

# 创建过滤器
event_filter = StructlogEventFilter(
    excluded_events=["heartbeat", "ping"],
    excluded_urls=["/internal/status"]
)

# 添加到processors
structlog.configure(
    processors=[
        event_filter,
        # ... 其他processors
    ]
)
```

### 5. 日志轮转

自动轮转日志文件，防止单个文件过大。

#### 配置

- **最大文件大小**：100MB
- **备份数量**：10个
- **文件格式**：`web3search_{environment}.log`
- **目录**：`logs/`

#### 文件结构

```
logs/
├── web3search_production.log          # 当前日志
├── web3search_production.log.1        # 第1个备份
├── web3search_production.log.2        # 第2个备份
└── ...
```

#### 轮转策略

1. 当前日志文件达到100MB时
2. 重命名为 `.log.1`
3. 旧的 `.log.1` 变为 `.log.2`，以此类推
4. 保留最新的10个备份，删除更旧的

## 日志格式

### 开发环境（彩色文本）

```
2024-01-15 10:30:45 | app.api.chat     | INFO     | quick_chat_started request_id=abc-123 user_id=456
```

### 生产环境（JSON）

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "log_level": "info",
  "logger_name": "app.api.chat",
  "event": "quick_chat_started",
  "request_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "user_id": 456,
  "symbol": "BTC",
  "filename": "chat.py",
  "lineno": 42,
  "func_name": "quick_chat"
}
```

### 错误日志格式

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "log_level": "error",
  "event": "api_call_failed",
  "request_id": "abc-123",
  "error": "Connection timeout",
  "error_type": "TimeoutError",
  "exception": "Traceback (most recent call last):\n  File ...",
  "filename": "client.py",
  "lineno": 89,
  "func_name": "fetch_data"
}
```

## 日志查询工具

### 基本用法

```bash
# 按request_id查询
python scripts/query_logs.py --request-id abc-123

# 查询特定级别
python scripts/query_logs.py --level ERROR

# 查询特定用户
python scripts/query_logs.py --user-id 456

# 查询特定加密货币
python scripts/query_logs.py --symbol BTC

# 时间范围查询
python scripts/query_logs.py \
    --since "2024-01-01 10:00:00" \
    --until "2024-01-01 12:00:00"

# 限制结果数量
python scripts/query_logs.py --level ERROR --limit 10
```

### 高级查询

```bash
# 请求追踪（完整链路）
python scripts/query_logs.py --request-id abc-123 --trace

# 错误摘要
python scripts/query_logs.py --error-summary

# 模式匹配
python scripts/query_logs.py --pattern "timeout|connection"

# 详细输出（包含完整JSON）
python scripts/query_logs.py --request-id abc-123 --verbose

# 导出到文件
python scripts/query_logs.py --level ERROR --output errors.json
```

### 查询结果示例

```bash
$ python scripts/query_logs.py --request-id abc-123 --trace

🔍 请求追踪 (request_id=abc-123):
  共 8 条日志

[2024-01-15 10:30:45] [INFO] [abc-123] request_started (method=GET, url=/api/v1/chat/quick)
[2024-01-15 10:30:45] [INFO] [abc-123] fetching_market_data (symbol=BTC)
[2024-01-15 10:30:46] [INFO] [abc-123] analyzing_sentiment (sources=3)
[2024-01-15 10:30:47] [INFO] [abc-123] generating_response (model=gpt-4)
[2024-01-15 10:30:49] [INFO] [abc-123] request_completed (status_code=200, duration=4200ms)
```

## 最佳实践

### 1. 选择合适的日志级别

```python
# ✅ 正确
logger.debug("variable_value", x=42)  # 调试信息
logger.info("user_registered", user_id=123)  # 重要操作
logger.warning("rate_limit_approaching", usage=0.9)  # 警告
logger.error("api_call_failed", error=str(e))  # 错误

# ❌ 错误
logger.info("x=42")  # 过度使用INFO记录调试信息
logger.error("User clicked button")  # ERROR用于正常操作
```

### 2. 使用结构化字段

```python
# ✅ 正确：结构化字段
logger.info(
    "order_created",
    order_id=12345,
    user_id=456,
    amount=100.50,
    currency="USD"
)

# ❌ 错误：字符串拼接
logger.info(f"Order 12345 created by user 456 for $100.50 USD")
```

### 3. 记录错误时包含上下文

```python
# ✅ 正确
try:
    result = api_call(symbol="BTC")
except Exception as e:
    logger.error(
        "api_call_failed",
        symbol="BTC",
        endpoint=endpoint,
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True  # 包含堆栈追踪
    )

# ❌ 错误：缺少上下文
try:
    result = api_call(symbol="BTC")
except Exception as e:
    logger.error(str(e))
```

### 4. 使用上下文管理器

```python
# ✅ 正确：自动管理上下文
async def process_request(request_id: str, user_id: int):
    with log_context(request_id=request_id, user_id=user_id):
        logger.info("processing_started")
        await step1()
        await step2()
        logger.info("processing_completed")

# ❌ 错误：手动传递参数
async def process_request(request_id: str, user_id: int):
    logger.info("processing_started", request_id=request_id, user_id=user_id)
    await step1()  # 忘记传递上下文
    logger.info("processing_completed", request_id=request_id)  # 忘记user_id
```

### 5. 避免记录敏感信息

```python
# ✅ 正确：脱敏后记录
logger.info("auth_success", api_key=api_key)  # 自动脱敏

# ✅ 正确：不记录敏感信息
logger.info("payment_processed", order_id=order_id)

# ❌ 错误：明文记录敏感信息
print(f"API Key: {api_key}")  # 绕过日志系统
```

### 6. 记录关键业务指标

```python
# ✅ 正确：记录业务指标
logger.info(
    "ai_analysis_completed",
    symbol="BTC",
    analysis_type="technical",
    confidence_score=0.85,
    duration_ms=1234,
    model="gpt-4"
)

# 这些日志可用于：
# - 性能分析
# - 业务报表
# - 问题追踪
```

## 故障排查

### 问题1：日志未输出

**症状**：代码中有logger.info()但看不到日志

**原因**：日志级别过滤

**解决**：
```python
# 检查LOG_LEVEL配置
import os
print(os.getenv("LOG_LEVEL"))  # 应该是DEBUG或INFO

# 或在代码中设置
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### 问题2：上下文信息丢失

**症状**：日志中没有request_id等上下文

**原因**：未使用上下文管理器或未绑定logger

**解决**：
```python
# 方式1：使用context manager
with log_context(request_id=request_id):
    logger.info("event")

# 方式2：使用带上下文的logger
logger = get_logger_with_context(__name__)
logger.info("event")
```

### 问题3：敏感信息泄露

**症状**：日志中出现完整的API key

**原因**：使用print()或其他输出方式

**解决**：
```python
# ❌ 绕过日志系统
print(f"Key: {api_key}")

# ✅ 使用logger（自动脱敏）
logger.info("key_loaded", api_key=api_key)
```

### 问题4：日志文件过大

**症状**：日志文件占用过多磁盘空间

**原因**：日志轮转未生效或备份数量过多

**解决**：
```python
# 检查日志目录
ls -lh logs/

# 减少备份数量（修改structlog_config.py）
handler = RotatingFileHandler(
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=5  # 从10减少到5
)

# 手动清理旧日志
rm logs/web3search_*.log.9
```

### 问题5：无法查询日志

**症状**：query_logs.py报错

**原因**：日志文件格式错误或路径问题

**解决**：
```bash
# 检查日志文件
ls -la logs/

# 验证JSON格式
head -1 logs/web3search_production.log | python -m json.tool

# 指定日志文件
python scripts/query_logs.py --log-file logs/web3search_production.log
```

## 性能考虑

### 1. 日志级别配置

- **开发环境**：DEBUG - 详细信息
- **生产环境**：INFO - 关键信息
- **高负载场景**：WARNING - 仅警告和错误

### 2. 异步日志

Structlog和Python logging都是同步的，但性能影响很小：

- 单条日志耗时：< 1ms
- 每秒可处理：10000+ 条日志
- 对API延迟影响：可忽略

### 3. 日志采样

高频事件可以采样记录：

```python
import random

# 只记录10%的请求
if random.random() < 0.1:
    logger.debug("request_detail", ...)
```

### 4. 批量日志

避免在循环中记录日志：

```python
# ❌ 避免
for item in items:
    logger.info("processing_item", item_id=item.id)

# ✅ 推荐
logger.info("batch_processing", total_items=len(items))
```

## 监控集成

### Sentry集成

日志系统已与Sentry集成，ERROR和CRITICAL级别日志自动上报：

```python
# 自动上报到Sentry
logger.error("critical_error", error=str(e), exc_info=True)

# Sentry中可以看到：
# - 完整堆栈追踪
# - request_id等上下文
# - 环境信息
# - 用户信息（如果有）
```

### 日志分析

使用query_logs.py进行日志分析：

```bash
# 性能分析
python scripts/query_logs.py --pattern "duration_ms" --since "today"

# 错误分析
python scripts/query_logs.py --error-summary --since "today"

# 用户行为分析
python scripts/query_logs.py --user-id 456 --since "today"
```

## 相关文档

- [配置管理文档](CONFIG.md)
- [数据库优化文档](STAGE1_DATABASE_OPTIMIZATION_SUMMARY.md)
- [项目总览](../README.md)

## 更新历史

- **2024-01-15**：初始版本，完成structlog集成和基础功能
