# Project Context

## Purpose
Web3 Search 是一个专注于加密货币领域的AI驱动研究平台，对标 asksurf.ai。项目目标：
- 为投资者提供机构级的加密货币分析报告
- 支持快速问答（Quick Chat）和深度研究（Deep Research）双模式
- 使用OpenRouter免费模型实现零AI成本
- 开源、免费、透明的加密货币研究工具

## Tech Stack

### 后端
- **语言**: Python 3.11
- **框架**: FastAPI（高性能异步API）
- **数据库**: PostgreSQL 15（关系数据）、Redis 7（缓存）、ChromaDB（向量存储）
- **任务队列**: Celery + Redis
- **AI服务**: OpenRouter API（qwen3-235b, qwen3-30b, deepseek-r1, gpt-oss-20b）
- **数据采集**: aiohttp, web3.py, tweepy, praw

### 前端
- **语言**: TypeScript
- **框架**: React 18
- **构建工具**: Vite
- **样式**: TailwindCSS + shadcn/ui
- **图表**: Recharts
- **Markdown渲染**: react-markdown

### 部署
- **前端**: Vercel（全球CDN，免费）
- **后端**: Railway（Python运行环境，$5-10/月）
- **CI/CD**: GitHub Actions

## Project Conventions

### Code Style
- **Python**: 遵循PEP 8，使用black格式化，pylint静态检查
- **TypeScript**: 使用ESLint + Prettier，遵循Airbnb风格指南
- **命名规范**:
  - 文件名：kebab-case（如`data-collector.py`）
  - 类名：PascalCase（如`DataCollector`）
  - 函数名：snake_case（如`fetch_price_data`）
  - 常量名：UPPER_SNAKE_CASE（如`MAX_RETRIES`）
- **注释**: 关键逻辑必须添加docstring，复杂算法需要行内注释
- **类型提示**: Python使用type hints，TypeScript使用严格模式

### Architecture Patterns
- **前后端分离**: React SPA + FastAPI RESTful API
- **微服务思想**: 数据采集、AI分析、报告生成独立模块
- **异步优先**: 使用asyncio并行处理，提升性能
- **缓存策略**: Redis多级缓存（价格1分钟、报告24小时）
- **错误处理**: 全局异常处理器 + 降级策略
- **配置管理**: 环境变量 + YAML配置文件

### Testing Strategy
- **单元测试**: pytest（Python）、Jest（TypeScript），覆盖率目标 > 80%
- **集成测试**: 测试API端到端流程
- **端到端测试**: Playwright测试完整用户流程
- **负载测试**: Locust模拟100并发用户
- **测试数据**: 使用Mock数据，避免依赖外部API
- **CI集成**: 每次PR自动运行测试，必须通过才能合并

### Git Workflow
- **分支策略**:
  - `main`: 生产环境，受保护分支
  - `develop`: 开发主分支
  - `feature/*`: 功能开发分支
  - `bugfix/*`: Bug修复分支
  - `hotfix/*`: 紧急修复分支
- **提交规范**:
  ```
  <type>(<scope>): <subject>

  类型: feat/fix/docs/style/refactor/test/chore
  示例: feat(data-collector): add CoinGecko API integration
  ```
- **PR流程**:
  1. 创建PR并填写描述
  2. 自动运行测试和代码检查
  3. Code Review（至少1人审核）
  4. 合并到develop或main

## Domain Context

### 加密货币领域知识
- **项目类型**: DeFi、Layer 1、Layer 2、CEX、DEX、NFT、GameFi等
- **关键指标**:
  - TVL（Total Value Locked）：锁仓总价值
  - OI（Open Interest）：未平仓合约
  - P/S比率（Price-to-Sales）：市值/收入比率
  - FDV（Fully Diluted Valuation）：完全稀释估值
- **数据源理解**:
  - CoinGecko/CoinMarketCap：价格和市值数据
  - Etherscan/BSCScan：链上交易和地址数据
  - Twitter/Reddit：社区情绪和讨论热度
  - CryptoPanic：新闻聚合
- **分析维度**: 基本面、技术面、链上数据、社交情绪、竞品对比、代币经济学

### 报告标准
参考 Hyperliquid PDF 示例：
- TL;DR：核心判断（Bull/Neutral/Bear）+ 置信度 + 一句话总结
- 时间窗分析：24h/7d/30d 多维度对比
- 结构化表格：竞品对比、估值倍数、支撑阻力
- 数据可视化：价格走势图、情绪分布图、TVL趋势图

## Important Constraints

### 成本约束
- **AI成本**: 必须使用OpenRouter免费模型（月成本$0）
- **部署成本**: 总成本< $10/月（Vercel免费 + Railway $5-10）
- **API限流**: 免费API有调用次数限制，需缓存和降级策略

### 时间约束
- **MVP开发周期**: 22-25天
- **Quick Chat响应**: < 3秒
- **Deep Research生成**: < 30秒

### 质量约束
- **报告质量**: 必须达到 Hyperliquid PDF 示例标准
- **数据准确性**: 与原始数据源误差< 10%
- **系统可用性**: > 99%

### 技术约束
- **Railway限制**: 免费tier有睡眠机制，需付费计划
- **Vercel限制**: Serverless Functions 10秒超时，不适合Deep Research
- **OpenRouter限流**: 免费模型可能有每日调用次数限制

## External Dependencies

### 数据源API
- **CoinGecko API**: 价格、市值、交易量（免费50次/分钟）
- **CoinMarketCap API**: 备用价格数据源
- **Etherscan API**: 以太坊链上数据（免费5次/秒）
- **BSCScan API**: BSC链上数据
- **Twitter API v2**: 推文搜索和情绪分析（免费500K条/月）
- **Reddit API**: 社区讨论抓取（免费60次/分钟）
- **CryptoPanic API**: 新闻聚合（免费25次/日）

### AI服务
- **OpenRouter API**: 统一LLM接口
  - qwen/qwen3-235b-a22b:free（深度分析）
  - qwen/qwen3-30b-a3b:free（快速响应）
  - deepseek/deepseek-r1-0528:free（推理分析）
  - openai/gpt-oss-20b:free（备用）

### 云服务
- **Vercel**: 前端托管和CDN
- **Railway**: 后端运行环境和数据库
- **GitHub**: 代码仓库和CI/CD

### 监控与告警
- **Sentry**: 错误追踪和监控
- **Railway Dashboard**: 服务监控和日志
- **Vercel Analytics**: 前端性能监控
