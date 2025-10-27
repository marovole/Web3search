# API 版本变更日志

Web3 Search API 版本历史和变更记录。

## 版本规范

本API遵循[语义化版本](https://semver.org/lang/zh-CN/)规范：

- **主版本号（Major）**：不兼容的API变更
- **次版本号（Minor）**：向后兼容的功能新增
- **修订号（Patch）**：向后兼容的问题修复

---

## [1.0.0] - 2025-01-27

### 🎉 首次发布

Web3 Search API正式发布v1.0.0版本。

### ✨ 新增功能

#### Chat接口
- **POST /api/v1/chat/quick-chat** - 快速对话接口
  - 3秒内快速响应
  - 支持多轮对话（session_id）
  - 自动识别查询类型
  - Claude 3.5 Sonnet模型

- **POST /api/v1/chat/quick-chat/stream** - 流式快速对话
  - Server-Sent Events格式
  - 逐字返回响应
  - 改善用户体验

#### Research接口
- **POST /api/v1/chat/deep-research** - 深度研究报告生成
  - 15-30秒生成完整报告
  - 六维度分析（市场、技术、情绪、链上、代币经济、风险）
  - 多模型协同（Claude + Llama）
  - 质量评分系统（0-100分）
  - 自动保存到数据库

- **GET /api/v1/chat/deep-research/status/{report_id}** - 查询报告生成状态
  - 轮询检查报告完成情况
  - 返回当前进度和质量评分

#### Reports接口
- **GET /api/v1/reports** - 获取报告列表
  - 分页查询（默认10条/页）
  - 多维度筛选（symbol, report_type, status）
  - 灵活排序（created_at, quality_score, generation_time）

- **GET /api/v1/reports/{report_id}** - 获取报告详情
  - 完整Markdown内容
  - 所有分析维度数据
  - 质量评分和元数据

- **DELETE /api/v1/reports/{report_id}** - 删除报告
  - 软删除（标记为已删除）
  - 可恢复设计

- **GET /api/v1/reports/stats/summary** - 报告统计
  - 总报告数
  - 按类型/状态分组统计
  - 平均质量评分

- **POST /api/v1/reports/{report_id}/share** - 创建分享链接
  - 生成唯一分享token
  - 可设置过期时间（默认7天）
  - 无需认证访问

- **GET /api/v1/reports/shared/{share_token}** - 访问分享报告
  - 通过token访问报告
  - 检查过期时间
  - 匿名访问

- **DELETE /api/v1/reports/shared/{share_token}** - 撤销分享链接
  - 立即失效分享链接
  - 防止继续访问

#### Search接口
- **GET /api/v1/search/autocomplete** - 搜索自动补全
  - 实时搜索加密货币
  - 模糊匹配（支持部分匹配）
  - 按市值排名排序
  - 包含币种图标

#### Trending接口
- **GET /api/v1/trending/hotspots** - 获取市场热点
  - 多维度热点识别
  - 5个维度评分（Twitter, Reddit, 价格, 交易量, 新闻）
  - 每15分钟更新
  - Redis缓存加速

#### Health接口
- **GET /health** - 健康检查
  - 数据库连接状态
  - Redis连接状态
  - Celery worker状态
  - 返回503状态码（不健康时）

### 🔧 技术特性

#### 数据采集
- **5个数据源集成**
  - CoinGecko - 价格和市值数据
  - Etherscan - 链上数据
  - Twitter API - 社交媒体情绪
  - Reddit API - 社区讨论
  - CryptoPanic - 新闻聚合

- **Fallback机制**
  - CoinGecko ↔ CoinMarketCap
  - Etherscan ↔ Blockchair
  - 自动切换备用数据源
  - 提高系统可靠性

#### 性能优化
- **Redis缓存**
  - 查询结果缓存（10分钟TTL）
  - 价格数据缓存（5分钟TTL）
  - 缓存命中率追踪

- **响应压缩**
  - GZip压缩（>1KB自动压缩）
  - 压缩级别6（平衡速度和压缩率）

- **并行请求**
  - asyncio.gather并发API调用
  - 显著降低响应时间

- **连接池**
  - AsyncPG数据库连接池（10-50连接）
  - Redis连接池管理

#### 监控系统
- **Sentry集成**
  - 自动错误追踪
  - 性能监控（P95延迟）
  - 自定义业务指标
  - Slack告警通知

- **Structured Logging**
  - JSON格式日志
  - request_id追踪
  - 上下文信息记录

#### 安全和限流
- **速率限制**
  - 基于IP的请求限流
  - Quick Chat: 10次/分钟
  - Deep Research: 3次/小时
  - 其他端点: 30次/分钟

- **CORS配置**
  - 允许localhost开发环境
  - 支持Vercel部署域名
  - 通配符支持预览部署

- **数据验证**
  - Pydantic schema验证
  - 自动参数类型转换
  - 详细错误提示

### 📚 文档

- **API文档**
  - Swagger UI交互式文档（/docs）
  - ReDoc文档（/redoc）
  - OpenAPI 3.0规范

- **使用指南**
  - API使用教程（API_TUTORIAL.md）
  - 错误码参考（API_ERRORS.md）
  - 认证说明（API_AUTH.md）
  - 监控运维指南（MONITORING_GUIDE.md）

### 🎯 速率限制

| 端点 | 限制 | 时间窗口 |
|------|------|----------|
| `/api/v1/chat/quick-chat` | 10次 | 每分钟 |
| `/api/v1/chat/deep-research` | 3次 | 每小时 |
| `/api/v1/search/*` | 30次 | 每分钟 |
| `/api/v1/trending/*` | 20次 | 每分钟 |
| `/health` | 无限制 | - |

### 🌐 支持的环境

- **生产环境**: https://web3search-api.onrender.com
- **开发环境**: http://localhost:8000
- **文档**: https://web3search-api.onrender.com/docs

---

## [Unreleased] - 未来计划

### 🚀 v2.0.0 计划功能（2025 Q2）

#### API认证系统
- **API Key认证**
  - Bearer token认证方式
  - 生成和管理API密钥
  - 细粒度权限控制
  - 密钥过期机制

#### 订阅计划
- **免费计划**: 100次Quick Chat/天，20次Deep Research/天
- **基础计划（$9/月）**: 1000次/天，100次Deep Research/天
- **专业计划（$49/月）**: 10000次/天，500次Deep Research/天
- **企业计划**: 无限请求，专用实例

#### 新增功能
- **WebSocket实时推送**
  - 实时价格更新
  - 热点事件通知
  - 报告生成进度推送

- **批量查询API**
  - 单次请求查询多个币种
  - 提高效率和性能

- **自定义报告模板**
  - 用户自定义分析维度
  - 报告样式个性化

#### 数据增强
- **更多链支持**
  - BSC, Polygon, Arbitrum
  - 跨链数据聚合

- **DeFi数据**
  - TVL追踪
  - APY/APR监控
  - 流动性池分析

- **NFT数据**
  - 地板价追踪
  - 交易量分析
  - 稀有度评分

### 🔮 v3.0.0 计划功能（2025 Q4）

#### OAuth 2.0支持
- GitHub OAuth
- Google OAuth
- Wallet Connect（Web3钱包登录）

#### AI能力增强
- GPT-4集成
- 图像生成（币种Logo、K线图）
- 语音对话支持

#### 高级分析
- 持币地址分析
- 巨鲸追踪
- 关联性分析
- 预测模型

---

## 迁移指南

### 从未来v2.0.0迁移到v1.0.0（回退）

v2.0.0发布后，v1.0.0将继续支持3个月（宽限期）。

**代码变更示例：**

```python
# v1.0.0（当前）
response = requests.post(
    "https://api.web3search.com/api/v1/chat/quick-chat",
    json={"query": "What is Bitcoin?"}
)

# v2.0.0（未来）
response = requests.post(
    "https://api.web3search.com/api/v1/chat/quick-chat",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={"query": "What is Bitcoin?"}
)
```

---

## 支持

- **文档**: [https://docs.web3search.com](https://docs.web3search.com)
- **GitHub**: [https://github.com/web3search/api](https://github.com/web3search/api)
- **Discord**: [https://discord.gg/web3search](https://discord.gg/web3search)
- **Email**: support@web3search.com

---

## 约定

### Breaking Changes标记
不兼容变更使用 **⚠️ BREAKING** 标记

### 变更类型
- ✨ **新增**（Added）- 新功能
- 🔧 **变更**（Changed）- 现有功能变更
- 🐛 **修复**（Fixed）- Bug修复
- 🗑️ **废弃**（Deprecated）- 即将移除的功能
- ❌ **移除**（Removed）- 已移除的功能
- 🔒 **安全**（Security）- 安全相关更新

---

**版本**: v1.0.0
**发布日期**: 2025-01-27
**维护者**: Web3 Search Team
