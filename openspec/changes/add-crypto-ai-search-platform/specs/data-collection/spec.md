# Data Collection Capability Specification

## ADDED Requirements

### Requirement: 多源加密货币数据采集
系统**SHALL**能够从多个公开数据源采集加密货币相关信息，包括市场数据、链上数据、社交媒体和新闻资讯。

#### Scenario: 成功采集CoinGecko价格数据
- **WHEN** 系统请求某个加密货币（如Bitcoin）的价格数据
- **THEN** 返回包含当前价格、24h涨跌幅、市值、交易量的结构化JSON数据
- **AND** 数据时效性在1分钟内（缓存TTL为60秒）
- **AND** 响应时间< 2秒

#### Scenario: 采集链上数据（Etherscan）
- **WHEN** 系统请求以太坊项目的链上数据（如Uniswap合约地址）
- **THEN** 返回包含日活地址数、24h交易量、持币地址分布的数据
- **AND** 支持多条链（Ethereum、BSC、Polygon、Arbitrum）
- **AND** 数据来源标注为Etherscan/BSCScan API

#### Scenario: 社交媒体情绪采集（Twitter）
- **WHEN** 系统采集某项目的Twitter数据（如搜索"Hyperliquid"）
- **THEN** 返回7天内的提及量、关键讨论话题、情绪得分（-1到1）
- **AND** 支持时间窗口过滤（24h/7d/30d）
- **AND** 识别Top 5高频关键词

#### Scenario: Reddit讨论热度采集
- **WHEN** 系统采集某项目的Reddit数据（在r/CryptoCurrency搜索）
- **THEN** 返回帖子数量、评论数量、平均upvote比例
- **AND** 提取最热门的3个讨论帖子标题
- **AND** 计算讨论热度得分（0-100）

#### Scenario: 新闻资讯采集（CryptoPanic）
- **WHEN** 系统采集某项目的新闻数据
- **THEN** 返回7天内的新闻标题、来源、发布时间
- **AND** 新闻按时间倒序排列
- **AND** 标注新闻情绪（正面/中性/负面）

#### Scenario: API限流处理
- **WHEN** 遇到数据源API限流（如CoinGecko返回429状态码）
- **THEN** 自动使用Redis缓存数据（如果存在）
- **AND** 如缓存不存在，降级到备用数据源（如CoinMarketCap）
- **AND** 记录限流事件到日志系统
- **AND** 返回响应时标注数据来源为"cached"或"fallback"

#### Scenario: 数据源不可用降级
- **WHEN** 主数据源完全不可用（连接超时或服务宕机）
- **THEN** 自动切换到备用数据源
- **AND** 在响应中添加警告信息"Using fallback data source"
- **AND** 触发监控告警通知运维人员

### Requirement: 定时数据更新
系统**SHALL**使用Celery定时任务自动更新数据，确保信息时效性。

#### Scenario: 定时任务正常执行
- **WHEN** 到达预定更新时间（如每15分钟的第0秒）
- **THEN** Celery Worker执行数据采集任务`update_market_data`
- **AND** 更新Top 100加密货币的价格到PostgreSQL数据库
- **AND** 刷新Redis缓存对应的key
- **AND** 任务执行时间< 60秒
- **AND** 记录任务执行日志（开始时间、结束时间、更新数量）

#### Scenario: 定时任务失败重试
- **WHEN** 定时任务执行失败（如网络错误导致API调用失败）
- **THEN** 自动重试最多3次
- **AND** 重试间隔递增（第1次1分钟、第2次5分钟、第3次15分钟）
- **AND** 3次重试后仍失败则标记任务为FAILED
- **AND** 发送告警邮件或Slack通知
- **AND** 保留失败任务的错误堆栈信息用于调试

#### Scenario: 不同数据类型的更新频率
- **WHEN** Celery Beat调度器启动
- **THEN** 配置以下定时任务：
  - `update_prices`：每1分钟执行（价格数据）
  - `update_onchain_data`：每5分钟执行（链上数据）
  - `update_social_data`：每15分钟执行（Twitter/Reddit）
  - `update_news`：每30分钟执行（新闻资讯）
- **AND** 所有任务独立执行，互不阻塞
- **AND** 任务执行状态可通过`GET /api/v1/tasks/status`查询

### Requirement: 数据持久化与缓存
系统**SHALL**将采集的数据持久化到PostgreSQL数据库，并使用Redis进行缓存优化。

#### Scenario: 新项目数据首次存储
- **WHEN** 首次采集某个项目（如新上线的代币）的数据
- **THEN** 在`projects`表中创建新记录（symbol, name, metadata）
- **AND** 在`snapshots`表中插入第一条快照记录
- **AND** 在Redis中缓存项目基础信息（TTL=1小时）
- **AND** 在Redis中缓存最新快照（TTL=1分钟）

#### Scenario: 历史数据查询
- **WHEN** 系统需要查询某项目过去30天的价格数据
- **THEN** 从`snapshots`表中查询按时间倒序的记录
- **AND** 使用索引`idx_project_time (project_id, timestamp DESC)`加速查询
- **AND** 查询时间< 500ms（对于30天数据）
- **AND** 返回数组格式`[{timestamp, price, volume}, ...]`

#### Scenario: 缓存命中减少数据库查询
- **WHEN** 用户请求某项目的当前价格（如"BTC price"）
- **THEN** 首先检查Redis key `price:BTC`
- **AND** 如果缓存存在且未过期，直接返回缓存数据
- **AND** 如果缓存不存在或已过期，查询数据库并更新缓存
- **AND** 缓存命中率应> 90%（通过监控统计）

### Requirement: 错误处理与监控
系统**SHALL**实施健壮的错误处理机制和实时监控。

#### Scenario: API调用超时处理
- **WHEN** 外部API调用超过10秒未响应
- **THEN** 取消请求并抛出`TimeoutError`异常
- **AND** 错误被全局异常处理器捕获
- **AND** 返回用户友好的错误消息"数据源暂时不可用，请稍后重试"
- **AND** 记录错误日志（包含API URL、超时时长）

#### Scenario: 数据验证失败处理
- **WHEN** 采集的数据不符合预期格式（如价格为负数）
- **THEN** 触发数据验证异常`DataValidationError`
- **AND** 丢弃该条异常数据
- **AND** 记录警告日志（包含原始数据和验证规则）
- **AND** 继续处理其他正常数据（不中断整个批次）

#### Scenario: 实时监控关键指标
- **WHEN** 数据采集服务运行时
- **THEN** 实时上报以下监控指标：
  - API调用成功率（按数据源分组）
  - 平均响应时间（p50/p95/p99）
  - 缓存命中率
  - 定时任务执行成功率
  - 数据更新延迟时间
- **AND** 当成功率< 95%时触发告警
- **AND** 当响应时间p95 > 5秒时触发告警
