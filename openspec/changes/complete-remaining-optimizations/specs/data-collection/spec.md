# Data Collection Specification - Phase 14 Deltas

## MODIFIED Requirements

### Requirement: Cryptocurrency Market Data Collection
The system SHALL collect cryptocurrency market data (price, market cap, volume, 24h change) from reliable data sources and SHALL implement multi-layer fallback mechanism to ensure 98% data collection availability.

系统必须从可靠的数据源收集加密货币市场数据（价格、市值、交易量、24小时变化），并实现多层fallback机制确保数据采集的高可用性（98%成功率）。主数据源失败时，系统应自动切换到备用数据源，对用户透明无感知。所有数据源调用应实现智能重试机制（指数退避）和断路器模式防止级联故障。

**数据源优先级**：
1. **主数据源**: CoinGecko API（免费，限流50 req/min）
2. **备用数据源1**: CoinMarketCap API（免费333 credits/天，约100次调用）
3. **备用数据源2**: Redis缓存数据（最多1小时前的数据）

#### Scenario: 主数据源成功
- **WHEN** 调用CoinGecko API获取BTC市场数据
- **AND** CoinGecko响应成功（HTTP 200）
- **THEN** 返回市场数据（价格、市值、交易量、24h变化）
- **AND** 记录日志："data_fetch_success", source="coingecko"
- **AND** 更新数据源成功率指标

#### Scenario: 主数据源失败，fallback成功
- **WHEN** 调用CoinGecko API获取BTC市场数据
- **AND** CoinGecko失败（HTTP 429 Too Many Requests）
- **THEN** 系统自动切换到CoinMarketCap API
- **AND** CoinMarketCap响应成功
- **THEN** 返回市场数据
- **AND** 记录日志："data_fetch_failed", source="coingecko", error="rate_limit"
- **AND** 记录日志："data_fetch_success", source="coinmarketcap"

#### Scenario: 所有数据源失败，使用缓存
- **WHEN** 调用CoinGecko API获取BTC市场数据
- **AND** CoinGecko失败（超时）
- **THEN** 系统切换到CoinMarketCap API
- **AND** CoinMarketCap也失败（超时）
- **THEN** 系统从Redis获取缓存数据
- **AND** 缓存数据存在且未过期（<1小时）
- **THEN** 返回缓存数据，并标记data_age字段
- **AND** 记录警告日志："using_cached_data", age_minutes=30

#### Scenario: 所有来源都失败
- **WHEN** 调用所有数据源（CoinGecko、CoinMarketCap、Cache）
- **AND** 所有来源都失败或无可用数据
- **THEN** 抛出DataSourceError异常
- **AND** 记录错误日志："all_data_sources_failed", symbol="BTC"
- **AND** 返回HTTP 503 Service Unavailable给用户

### Requirement: On-chain Data Collection
The system SHALL collect on-chain data (holder addresses, active addresses, transaction count, gas fees) from blockchain data providers and SHALL implement fallback mechanism.

系统必须从区块链数据提供商收集链上数据（持有地址数、活跃地址、交易笔数、Gas费用），并实现fallback机制。

**数据源优先级**：
1. **主数据源**: Etherscan API（免费5 req/sec）
2. **备用数据源**: Blockchair API（免费每天1万次调用）

#### Scenario: 链上数据采集成功
- **WHEN** 调用Etherscan API获取ETH链上数据
- **AND** Etherscan响应成功
- **THEN** 返回链上数据（持有地址、活跃地址、交易笔数）
- **AND** 记录成功日志

#### Scenario: 主数据源失败，fallback到Blockchair
- **WHEN** 调用Etherscan API获取ETH链上数据
- **AND** Etherscan失败（API key无效或限流）
- **THEN** 系统切换到Blockchair API
- **AND** Blockchair响应成功
- **THEN** 返回链上数据
- **AND** 记录日志："onchain_fallback", from="etherscan", to="blockchair"

### Requirement: Social Media Data Collection
The system SHALL collect sentiment data (Twitter/Reddit discussion volume, sentiment tendency) from social media platforms and SHALL implement fallback mechanism.

系统必须从社交媒体平台收集情绪数据（Twitter/Reddit讨论量、情绪倾向），并实现fallback机制。

**数据源优先级**：
1. **主数据源**: Twitter API v2（付费）
2. **备用数据源**: Nitter镜像（免费）
3. **降级策略**: 跳过社交数据（不影响核心功能）

#### Scenario: Twitter数据采集成功
- **WHEN** 调用Twitter API搜索"#Bitcoin"相关推文
- **AND** Twitter API响应成功
- **THEN** 返回社交数据（讨论量、情绪分数）

#### Scenario: Twitter失败，使用Nitter镜像
- **WHEN** 调用Twitter API失败（限流或API key无效）
- **THEN** 系统切换到Nitter镜像抓取
- **AND** 成功抓取推文数据
- **THEN** 返回社交数据

#### Scenario: 社交数据全部失败，优雅降级
- **WHEN** 所有社交数据源都失败
- **THEN** 系统跳过社交数据，继续处理
- **AND** 在响应中标记social_data=null
- **AND** 记录警告日志："social_data_unavailable"

## ADDED Requirements

### Requirement: Smart Retry Mechanism
The system SHALL implement smart retry mechanism for all external API calls with exponential backoff, error classification, and timeout control.

系统必须为所有外部API调用实现智能重试机制，支持指数退避、错误分类和超时控制。

**重试策略**：
- **临时错误**（429 Too Many Requests, 503 Service Unavailable, Timeout）：重试最多3次
- **永久错误**（401 Unauthorized, 404 Not Found）：不重试，立即失败
- **重试间隔**：1秒、2秒、4秒（指数退避）
- **总超时**：单次请求10秒，总计30秒

#### Scenario: 临时错误重试成功
- **WHEN** 调用CoinGecko API
- **AND** 第1次请求返回503 Service Unavailable
- **THEN** 系统等待1秒后重试
- **AND** 第2次请求成功
- **THEN** 返回数据
- **AND** 记录日志："retry_success", attempt=2

#### Scenario: 达到最大重试次数
- **WHEN** 调用CoinGecko API
- **AND** 3次请求都返回503错误
- **THEN** 停止重试，抛出APIError异常
- **AND** 记录错误日志："max_retries_exceeded", attempts=3

#### Scenario: 永久错误不重试
- **WHEN** 调用CoinGecko API
- **AND** 请求返回401 Unauthorized
- **THEN** 系统不重试，立即抛出异常
- **AND** 记录错误日志："permanent_error", status=401

### Requirement: Circuit Breaker Pattern
The system SHALL implement circuit breaker pattern for each external data source to prevent cascading failures.

系统必须为每个外部数据源实现断路器模式，防止级联故障。

**断路器配置**：
- **失败阈值**: 连续失败5次
- **熔断时间**: 10分钟（600秒）
- **半开状态**: 10分钟后尝试1次请求，成功则恢复，失败则继续熔断

**状态转换**：
- CLOSED（正常）→ 连续失败5次 → OPEN（熔断）
- OPEN（熔断）→ 10分钟后 → HALF_OPEN（半开）
- HALF_OPEN（半开）→ 请求成功 → CLOSED（正常）
- HALF_OPEN（半开）→ 请求失败 → OPEN（熔断）

#### Scenario: 断路器熔断
- **WHEN** CoinGecko API连续失败5次
- **THEN** 断路器状态变为OPEN
- **AND** 记录错误日志："circuit_breaker_opened", source="coingecko"
- **AND** 后续请求直接返回CircuitBreakerOpenError，不调用API

#### Scenario: 断路器半开尝试恢复
- **WHEN** 断路器处于OPEN状态
- **AND** 距离最后一次失败已过去10分钟
- **THEN** 断路器状态变为HALF_OPEN
- **AND** 允许下一次请求通过
- **WHEN** 请求成功
- **THEN** 断路器状态恢复为CLOSED
- **AND** 重置失败计数器

#### Scenario: 断路器恢复失败
- **WHEN** 断路器处于HALF_OPEN状态
- **AND** 尝试请求失败
- **THEN** 断路器重新回到OPEN状态
- **AND** 重新计时10分钟

### Requirement: Data Quality Validation
The system SHALL validate quality of collected data, detect anomalies, and record alerts.

系统必须对采集的数据进行质量验证，检测异常数据并记录告警。

**验证规则**：
- **价格数据**: 与上一次价格相比波动不超过±50%
- **市值数据**: 计算一致性检查（market_cap ≈ price * circulating_supply）
- **社交数据**: 时效性验证（数据不超过24小时）
- **链上数据**: 必填字段完整性检查

#### Scenario: 价格数据异常检测
- **WHEN** 获取BTC价格数据为$10,000
- **AND** 上一次记录的价格为$50,000
- **THEN** 系统检测到异常波动（-80%）
- **AND** 记录告警日志："price_anomaly_detected", symbol="BTC", change=-80%
- **AND** 触发Sentry告警
- **AND** 使用缓存数据替代异常数据

#### Scenario: 市值数据一致性检查
- **WHEN** 获取BTC市场数据
- **AND** price=$50,000, circulating_supply=19M, market_cap=$800B
- **THEN** 计算预期市值 = 50000 * 19000000 = $950B
- **AND** 实际市值与预期相差19%
- **THEN** 记录警告日志："market_cap_mismatch", expected="950B", actual="800B", diff=19%

#### Scenario: 社交数据时效性验证失败
- **WHEN** 获取Twitter情绪数据
- **AND** 数据时间戳为48小时前
- **THEN** 系统拒绝使用该数据
- **AND** 记录警告日志："stale_social_data", age_hours=48
- **AND** 标记social_data=null

### Requirement: Data Source Metrics
The system SHALL record performance metrics for all data sources for monitoring and optimization purposes.

系统必须记录所有数据源的性能指标，用于监控和优化。

**记录指标**：
- **成功率**: 成功请求数 / 总请求数（按数据源统计）
- **响应时间**: P50、P95、P99延迟（按数据源统计）
- **失败原因**: 超时、限流、认证失败等（分类统计）
- **Fallback频率**: 主数据源失败，使用备用数据源的次数

#### Scenario: 记录成功请求指标
- **WHEN** CoinGecko API调用成功
- **AND** 响应时间为250ms
- **THEN** 增加指标："data_source.request", source="coingecko"
- **AND** 增加指标："data_source.success", source="coingecko"
- **AND** 记录分布指标："data_source.response_time", value=250, source="coingecko"

#### Scenario: 记录失败请求指标
- **WHEN** CoinGecko API调用失败（429错误）
- **THEN** 增加指标："data_source.request", source="coingecko"
- **AND** 增加指标："data_source.failure", source="coingecko", reason="rate_limit"
- **AND** 增加指标："data_source.fallback", from="coingecko", to="coinmarketcap"

## Implementation Notes

### Python装饰器实现

```python
# backend/app/core/retry.py
from functools import wraps
import asyncio
from typing import Callable

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
    retriable_exceptions: tuple = (aiohttp.ClientError, asyncio.TimeoutError)
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retriable_exceptions as e:
                    if attempt == max_attempts - 1:
                        raise

                    delay = base_delay * (exponential_base ** attempt)
                    logger.warning(
                        "retry_attempt",
                        func=func.__name__,
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
            return wrapper
        return decorator

# 使用示例
@retry_with_backoff(max_attempts=3, base_delay=1.0)
async def fetch_coingecko_price(symbol: str) -> dict:
    async with aiohttp.ClientSession() as session:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        async with session.get(url, params={"ids": symbol}, timeout=10) as resp:
            return await resp.json()
```

### 断路器实现

```python
# backend/app/core/circuit_breaker.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    timeout_seconds: int = 600

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: datetime | None = None

    async def call(self, func: Callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                self.state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker_half_open", name=self.name)
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("circuit_breaker_closed", name=self.name)

            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error("circuit_breaker_opened", name=self.name, failures=self.failure_count)

            raise
```

### Fallback机制实现

```python
# backend/app/services/data_collector.py
async def fetch_market_data_with_fallback(symbol: str) -> dict:
    """按优先级尝试多个数据源"""
    sources = [
        ("coingecko", coingecko_breaker, fetch_from_coingecko),
        ("coinmarketcap", cmc_breaker, fetch_from_coinmarketcap),
        ("cache", None, fetch_from_cache)
    ]

    for source_name, breaker, fetch_func in sources:
        try:
            if breaker:
                data = await breaker.call(fetch_func, symbol)
            else:
                data = await fetch_func(symbol)

            logger.info("data_fetch_success", symbol=symbol, source=source_name)
            metrics.incr("data_source.success", tags={"source": source_name})
            return data
        except CircuitBreakerOpenError:
            logger.warning("circuit_breaker_open", source=source_name)
            continue
        except Exception as e:
            logger.warning("data_fetch_failed", symbol=symbol, source=source_name, error=str(e))
            metrics.incr("data_source.failure", tags={"source": source_name, "reason": type(e).__name__})
            continue

    raise DataSourceError(f"All data sources failed for {symbol}")
```

## Testing Requirements

### 单元测试
- 测试重试机制（成功、最大重试、永久错误）
- 测试断路器状态转换（CLOSED→OPEN→HALF_OPEN→CLOSED）
- 测试Fallback逻辑（主源失败→备用源成功）
- 测试数据验证（异常检测、一致性检查）

### 集成测试
- Mock外部API，模拟各种失败场景
- 验证指标记录是否正确
- 测试并发场景下的断路器行为

### 性能测试
- 验证重试机制不影响正常请求延迟
- 测试断路器熔断后的响应时间（<50ms）
- 验证Fallback切换延迟（<100ms）
