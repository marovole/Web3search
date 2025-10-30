# data-collection Specification

## Purpose
定义多源加密货币数据采集系统的功能规范，包括从CoinGecko、Etherscan、Twitter、Reddit、CryptoPanic等数据源采集市场数据、链上数据、社交媒体情绪和新闻资讯，实现智能缓存预热、分层缓存策略（L1内存缓存+L2 Redis缓存）、定时数据更新、错误处理与降级机制，确保数据时效性和系统可靠性。
## Requirements
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
系统**SHALL**使用Celery定时任务自动更新数据，确保信息时效性。**集成智能预热调度。**

#### Scenario: 智能预热任务调度
- **WHEN** Celery Beat调度器启动
- **THEN** 配置以下预热任务：
  - `prewarm_top10_coins`：每1分钟执行（Top 10币种）
  - `prewarm_top100_coins`：每5分钟执行（Top 11-100币种）
  - `adjust_prewarming_list`：每小时执行（动态调整预热列表）
- **AND** 预热任务与数据更新任务独立执行
- **AND** 预热任务优先级高于常规更新任务
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

### Requirement: 智能缓存预热系统
系统**SHALL**实现智能缓存预热机制，在用户请求前主动加载热门币种数据到缓存。

#### Scenario: Top 100币种自动预热
- **WHEN** 系统启动或每5分钟执行预热任务
- **THEN** 从CoinGecko获取Top 100市值币种列表
- **AND** 批量预热这些币种的价格数据到Redis缓存
- **AND** 预热任务执行时间< 30秒
- **AND** 预热成功率> 98%
- **AND** 记录预热任务日志（预热数量、成功数、失败数、耗时）

#### Scenario: 分层预热策略
- **WHEN** 预热任务执行时
- **THEN** 按优先级分层预热：
  - **高优先级**（Top 10）：每1分钟更新一次
  - **中优先级**（Top 11-100）：每5分钟更新一次
  - **低优先级**（长尾币种）：按需更新或15分钟更新
- **AND** 高优先级任务优先执行，不被阻塞
- **AND** 每层任务独立监控和统计

#### Scenario: 启动时快速预加载
- **WHEN** 服务启动（uvicorn启动完成）
- **THEN** 立即触发Top 10币种的预加载
- **AND** 预加载完成时间< 5秒
- **AND** 预加载失败不阻塞服务启动
- **AND** 预加载进度通过日志输出（"Preloading 1/10..."）
- **AND** 预加载状态纳入/health健康检查

#### Scenario: 预热任务失败重试
- **WHEN** 预热任务中某个币种数据获取失败
- **THEN** 自动重试该币种（最多3次）
- **AND** 重试间隔为1秒、2秒、4秒（指数退避）
- **AND** 3次重试后仍失败则跳过该币种
- **AND** 记录失败详情到错误日志
- **AND** 不影响其他币种的预热进程

#### Scenario: 智能预热列表动态调整
- **WHEN** 每小时分析用户查询历史
- **THEN** 计算每个币种的查询热度得分
- **AND** 根据热度动态调整预热列表（替换低热度币种）
- **AND** 保持预热列表最大100个币种
- **AND** 记录预热列表变更日志
- **AND** 预热列表变更不影响当前正在执行的预热任务

### Requirement: L1内存缓存层
系统**SHALL**实现L1内存缓存层，进一步降低Redis访问延迟。

#### Scenario: L1缓存命中
- **WHEN** 用户请求热门币种价格（如BTC）
- **THEN** 首先检查L1内存缓存
- **AND** 如果L1命中，直接返回（延迟< 1ms）
- **AND** 如果L1未命中，检查L2 Redis缓存
- **AND** 如果L2命中，将数据写入L1并返回
- **AND** 如果L2也未命中，查询数据源并写入L1和L2

#### Scenario: L1缓存淘汰策略
- **WHEN** L1缓存达到容量上限（100条）
- **THEN** 使用LRU + 访问频率权重淘汰最低价值条目
- **AND** 访问频率高的条目权重增加50%
- **AND** 淘汰的数据仍保留在L2 Redis中
- **AND** 记录淘汰事件到监控指标

#### Scenario: L1/L2缓存一致性
- **WHEN** L2缓存数据更新（预热任务或数据采集）
- **THEN** 同时失效L1对应的缓存条目
- **AND** 下次访问时重新从L2加载到L1
- **AND** 确保L1和L2数据一致性
- **AND** 一致性检查每分钟执行一次

