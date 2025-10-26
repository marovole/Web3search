# 提案：构建Web3加密货币AI搜索引擎

## Why（为什么）

加密货币市场快速发展，但缺乏高质量、AI驱动的研究工具。现状问题：

1. **信息分散**：价格数据、链上数据、社交媒体、新闻资讯散落在不同平台
2. **分析门槛高**：普通投资者难以进行专业级的多维度分析
3. **工具昂贵**：现有AI研究平台（如asksurf.ai）收费高昂（$20-200/月）
4. **不透明**：商业平台的分析逻辑和数据源不公开

我们需要构建一个**开源、免费、专业级**的加密货币AI搜索引擎，为投资者提供机构级分析报告，降低研究门槛，提高市场透明度。

## What Changes（改什么）

创建一个完整的Web3 AI搜索平台，包含以下核心组件：

### 1. 数据采集系统
- 集成CoinGecko、CoinMarketCap（市场数据）
- 集成Etherscan、BSCScan（链上数据）
- 集成Twitter API v2、Reddit API（社交媒体）
- 集成CryptoPanic、RSS聚合（新闻资讯）
- Celery定时任务（自动更新数据）

### 2. AI分析引擎
- OpenRouter多模型路由（qwen3-235b、qwen3-30b、deepseek-r1、gpt-oss-20b）
- 六维分析能力：
  - TL;DR生成（核心判断+置信度）
  - 时间窗分析（24h/7d/30d价格+协议指标）
  - 社媒情绪分析（Twitter/Reddit情绪+热点话题）
  - 技术面分析（支撑阻力+RSI/MACD+清算风险）
  - 基本面分析（用户增长+收入+鲸鱼持仓）
  - 竞品对比（估值倍数+市场份额）

### 3. 双模式交互
- **Quick Chat模式**：快速问答，3-5秒响应，适合简单查询
- **Deep Research模式**：深度研究报告，15-30秒生成，机构级质量

### 4. 报告生成系统
- Markdown格式输出（3000-5000字）
- 动态表格生成（竞品对比/估值倍数）
- 图表嵌入（价格走势/情绪分布）
- PDF导出功能（WeasyPrint）
- 分享链接生成（7天有效期）

### 5. 现代化前端
- React + TypeScript + Vite
- 对话式界面（类似ChatGPT）
- 模式切换器（Quick/Deep）
- SSE流式输出（实时显示）
- Markdown渲染 + 交互式图表（Recharts）
- 响应式设计（支持移动端）

### 6. 云原生部署
- **前端**：Vercel（全球CDN，免费）
- **后端**：Railway（Python + PostgreSQL + Redis，$5-10/月）
- **架构**：前后端分离，支持水平扩展

## Impact（影响）

### 新增能力（5个核心模块）
1. ✅ **data-collection**：多源数据采集与定时更新
2. ✅ **ai-analysis**：OpenRouter多模型AI分析引擎
3. ✅ **chat-interface**：双模式对话交互系统
4. ✅ **report-generation**：机构级Markdown/PDF报告生成
5. ✅ **deployment**：Vercel + Railway云原生部署

### 技术栈
- **后端**：Python 3.11、FastAPI、SQLAlchemy、Celery
- **数据库**：PostgreSQL 15、Redis 7、ChromaDB
- **前端**：React 18、TypeScript、Vite、TailwindCSS、Recharts
- **AI**：OpenRouter API（免费模型）
- **部署**：Vercel（前端）+ Railway（后端）

### 性能指标
- Quick Chat响应时间：< 3秒
- Deep Research生成时间：< 30秒
- 支持加密货币数量：Top 100
- 并发支持：100+用户
- 月部署成本：< $10（初期）

### 开发周期
- **总工期**：22-25天
- **里程碑**：
  - Week 1：数据采集+AI引擎基础
  - Week 2：Deep Research核心功能
  - Week 3：前端界面+报告生成
  - Week 4：部署+测试优化

### 质量标准
- 报告质量对标机构研报（参考Hyperliquid PDF示例）
- 代码覆盖率：> 80%
- API响应时间p95：< 5秒
- 前端加载速度：< 2秒（Vercel CDN）

### 受影响的文件
- **新增代码**：约10,000行（后端5000 + 前端3000 + 配置2000）
- **目录结构**：
  ```
  /backend         # FastAPI后端
  /frontend        # React前端
  /prompts         # AI Prompt模板库
  /docs            # 项目文档
  docker-compose.yml
  railway.yaml
  vercel.json
  ```

### 风险与挑战
1. **API限流风险**：免费API可能有调用限制 → 缓存策略+降级方案
2. **AI质量不稳定**：免费模型输出可能不一致 → 多次采样+质量检查
3. **数据源变更**：第三方API可能改变 → 适配器模式+监控告警
4. **成本控制**：Railway成本可能超预算 → 监控用量+优化查询

### 成功指标
- [ ] Deep Research报告质量通过人工评估（对比PDF标准）
- [ ] 支持Top 100加密货币完整分析
- [ ] 每日生成50+份研究报告（不超OpenRouter免费额度）
- [ ] 系统可用性 > 99%
- [ ] 用户满意度 > 4.5/5（基于反馈）
