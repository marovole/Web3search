# Project Context

## Purpose
Web3 Search 是一个专注于加密货币领域的AI驱动研究平台，对标 asksurf.ai。项目目标：
- 为投资者提供机构级的加密货币分析报告
- 支持快速问答（Quick Chat）和深度研究（Deep Research）双模式
- 使用OpenRouter免费模型实现零AI成本
- 开源、免费、透明的加密货币研究工具

## Tech Stack

### 后端
- **平台**: Cloudflare Workers（边缘计算，全球分布）
- **语言**: TypeScript
- **数据库**: Supabase PostgreSQL（关系数据）
- **AI服务**: OpenRouter API（Claude Sonnet, GPT models）
- **价格数据**: CoinGecko API（免费版）

### 前端
- **语言**: TypeScript
- **框架**: React 18
- **构建工具**: Vite
- **样式**: TailwindCSS + shadcn/ui
- **图表**: Recharts
- **Markdown渲染**: react-markdown

### 部署
- **前端**: Cloudflare Pages（全球CDN，免费）
- **后端**: Cloudflare Workers（边缘计算，免费）
- **数据库**: Supabase（PostgreSQL，免费）
- **CI/CD**: GitHub Actions + Cloudflare自动部署

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
- **前后端分离**: React SPA + Cloudflare Workers RESTful API
- **边缘优先**: 利用Cloudflare全球边缘网络，降低延迟
- **Serverless架构**: 无需服务器管理，按需扩展
- **实时数据**: CoinGecko API实时价格 + OpenRouter流式响应
- **错误处理**: 全局异常处理器 + 降级策略
- **配置管理**: 环境变量 + Wrangler配置文件

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

## Current Status

### 项目阶段
**当前状态**: Phase 1 - 前端开发完成 ✅ | 后端部署成功 ✅ | OpenSpec规范完成 ✅

**最后更新**: 2025-11-01 19:30 (UTC+8)

### OpenSpec进度
- **活动Change**: `add-crypto-ai-search-platform`
- **Validation状态**: ✅ 通过（openspec validate --strict）
- **完成时间**: 2025-10-25
- **Capability Specs**: 5个已完成并验证
  - ✅ data-collection: 多源数据采集系统
  - ✅ ai-analysis: OpenRouter AI分析引擎
  - ✅ chat-interface: 双模式对话系统
  - ✅ report-generation: 报告生成与导出
  - ✅ deployment: 云原生部署配置
- **Phase 0任务**: 8/8完成（100%）

### 后端开发状态
**进度**: 约65%完成

**已完成模块**:
- ✅ FastAPI基础框架（app/main.py）
- ✅ 数据模型层（models/project.py, conversation.py, report.py）
- ✅ 数据采集器（collectors/coingecko.py, twitter.py, cryptopanic.py）
- ✅ Celery定时任务（tasks/data_collection.py）
- ✅ API端点（api/v1/chat.py, reports.py）- 10个端点已就绪
- ✅ 配置管理（core/config.py, database.py, redis_client.py）
- ✅ 测试框架（tests/）
- ✅ 生产环境部署和验证

**待完成模块**:
- ⏳ Deep Research引擎完整实现
- ⏳ Prompt模板库（prompts/目录）
- ⏳ 报告生成器（Markdown/PDF导出）
- ⏳ 完整的单元测试覆盖

### 前端开发状态
**进度**: 85%（接近完成）

**技术栈**: React 18 + TypeScript + Vite + TailwindCSS + shadcn/ui ✅

**已完成功能**:
- ✅ 完整页面架构（12个页面：Chat, Search, History, Settings等）
- ✅ UI组件库（shadcn/ui + 30+自定义组件）
- ✅ 双模式AI对话系统（Quick Chat + Deep Research）
- ✅ 响应式设计和主题切换
- ✅ 性能优化（代码分割、懒加载、PWA）
- ✅ 部署配置（Vercel + CI/CD）

### 部署状态
**平台**: Cloudflare（边缘计算平台）

**服务配置**:
- 后端服务: Cloudflare Workers (TypeScript)
- 前端服务: Cloudflare Pages (React + Vite)
- 数据库: Supabase PostgreSQL (Free Plan)
- AI服务: OpenRouter API
- 价格数据: CoinGecko API
- 全球分布: 300+ 边缘节点

**当前状态**: ✅ **LIVE**
- 后端 API: https://web3search-api.marovole.workers.dev
- 前端应用: https://web3search.pages.dev
- API 健康检查: https://web3search-api.marovole.workers.dev/api/v1/health
- 部署方式: GitHub push 自动部署
- 最后更新: 2025-11-10

**架构优势**（2025-11-10迁移）:
1. ✅ 全球边缘分布，低延迟访问
2. ✅ Serverless 架构，自动扩展
3. ✅ 零成本运营（Cloudflare 免费计划）
4. ✅ 实时价格数据集成（CoinGecko）
5. ✅ 流式 AI 响应（OpenRouter SSE）
4. ✅ 修复SQLAlchemy metadata保留名称冲突

**可用功能**:
- ✅ 健康检查端点 (/health)
- ✅ Quick Chat API (快速对话)
- ✅ Deep Research API (深度研究)
- ✅ Reports API (报告管理)
- ✅ 完整的OpenAPI文档

### 下一步优先级

**当前阶段**: Phase 2 - 前后端集成和功能完善

**紧急任务** (本周):
1. ✅ ~~修复Render部署问题~~ **已完成** (2025-10-25)
2. ✅ ~~完成前端开发~~ **已完成** (2025-11-01)
3. 🟡 前后端API集成测试
4. 🟡 完成Deep Research核心功能实现
5. 🟡 创建Prompt模板库（prompts/目录）

**中期任务** (2-3周):
6. 🟡 实现报告生成器（Markdown/PDF格式）
7. 🟢 前端部署到Vercel生产环境
8. 🟢 完善测试覆盖率（目标>80%）

**长期任务** (3-4周):
9. 🔵 性能优化和负载测试（100并发）
10. 🔵 配置生产环境监控（Sentry）
11. 🔵 项目文档完善和公开发布

### 技术债务
- ✅ ~~tasks.md与实际代码进度不同步~~ **已解决** (2025-10-25)
- ✅ ~~前端开发进度文档不准确~~ **已解决** (2025-11-01)
- ⚠️ 缺少完整的错误处理和降级策略
- ⚠️ 前后端API集成需要测试验证
- ⚠️ 缺少完整的监控和告警系统
- ⚠️ Deep Research引擎需要完整实现
