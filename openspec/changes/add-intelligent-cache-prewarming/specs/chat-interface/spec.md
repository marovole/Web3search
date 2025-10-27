# chat-interface Spec Delta

## MODIFIED Requirements

### Requirement: 双模式对话交互
系统**SHALL**提供Quick Chat和Deep Research两种交互模式，满足不同用户需求。**集成L1内存缓存加速响应。**

#### Scenario: Quick Chat with L1 Cache
- **WHEN** 用户提问热门币种（如"BTC price"）
- **THEN** 首先检查L1内存缓存
- **AND** L1命中时响应延迟< 500ms（含AI生成）
- **AND** L1未命中但L2命中时响应延迟< 1秒
- **AND** 缓存完全未命中时响应延迟< 3秒
- **AND** 响应头包含缓存信息（X-Cache: HIT-L1/HIT-L2/MISS）

#### Scenario: Cache-aware Response Headers
- **WHEN** 系统返回Quick Chat或Deep Research响应
- **THEN** 响应头包含缓存状态信息：
  - `X-Cache`: HIT-L1 | HIT-L2 | MISS
  - `X-Cache-Age`: 缓存数据年龄（秒）
  - `X-Data-Source`: cached | live | fallback
- **AND** 用户可以在开发工具中查看缓存状态
- **AND** 监控系统记录缓存命中率统计
