# 技术设计文档：Web3加密货币AI搜索引擎

## Context（背景）

### 问题陈述
构建一个对标asksurf.ai的加密货币AI研究平台，需要解决以下技术挑战：
1. 多源数据实时采集与聚合（5+数据源）
2. AI模型成本控制（使用免费OpenRouter模型）
3. 15-30秒内生成3000+字的深度研究报告
4. 支持流式响应和长时间任务
5. 低成本云部署（月成本 < $10）

### 约束条件
- **预算约束**：必须使用免费/低成本服务
- **时间约束**：22-25天完成MVP
- **技术栈约束**：后端Python（FastAPI），前端React
- **质量约束**：报告质量对标机构研报（参考Hyperliquid PDF）

### 利益相关方
- **开发者**：项目负责人
- **用户**：加密货币投资者、研究员
- **数据源**：CoinGecko、Twitter、Etherscan等第三方API

---

## Goals / Non-Goals（目标与非目标）

### Goals（目标）
1. ✅ 实现双模式交互（Quick Chat + Deep Research）
2. ✅ Deep Research报告质量达到PDF示例标准
3. ✅ 支持Top 100加密货币分析
4. ✅ Quick Chat响应 < 3秒，Deep Research < 30秒
5. ✅ 月部署成本 < $10
6. ✅ 使用OpenRouter免费模型（零AI成本）

### Non-Goals（非目标）
1. ❌ 不支持实时价格推送（WebSocket）- 使用轮询即可
2. ❌ 不支持用户登录系统（MVP阶段）- 后续迭代
3. ❌ 不支持自定义报告模板 - 使用固定格式
4. ❌ 不支持多语言（仅中文/英文）- 后续扩展
5. ❌ 不做移动端原生应用 - 响应式Web即可

---

## Decisions（关键技术决策）

### 决策1：部署架构 - Vercel + Railway混合部署

#### 决策内容
采用**前后端分离 + 混合云部署**架构：
- **前端**：Vercel（全球CDN，免费Hobby计划）
- **后端**：Railway（Python + PostgreSQL + Redis，$5-10/月）

#### 架构图
```
用户浏览器
    ↓
Vercel CDN (React SPA)
    ↓ API请求
Railway 后端服务集群
    ├── FastAPI应用 (8000端口)
    ├── Celery Worker (后台任务)
    ├── PostgreSQL 15 (持久化数据)
    └── Redis 7 (缓存+消息队列)
```

#### 理由
1. **成本优势**：
   - Vercel免费100GB带宽/月
   - Railway $5包含500小时计算+数据库
   - 总成本 < $10/月（对比AWS EC2 $50+/月）

2. **技术匹配**：
   - Vercel/Netlify的Serverless Functions有10秒超时限制，不支持Deep Research（15-30秒）
   - Cloudflare Workers不原生支持Python，需要Pyodide（性能损失50%）
   - Railway原生支持Python长时间运行，无需改造架构

3. **开发体验**：
   - Vercel自动化部署（Git集成）
   - Railway一键部署PostgreSQL/Redis
   - 无需复杂的容器编排

#### 替代方案考虑
| 方案 | 优势 | 劣势 | 不选原因 |
|------|------|------|---------|
| Vercel Only (Serverless) | 完全免费 | 10秒超时，需重构为任务队列 | 用户体验差，开发成本高 |
| AWS EC2 | 完全可控 | 成本高（$50+/月），运维复杂 | 超预算 |
| Cloudflare Workers | 全球边缘计算 | 不支持Python，需Pyodide | 性能损失大，生态不成熟 |
| Render.com免费层 | 零成本 | 15分钟无请求会睡眠 | 生产环境不可用 |

#### 迁移计划
如后续需要从Railway迁移到AWS/GCP：
1. 修改`railway.yaml` → `docker-compose.yml`
2. 配置环境变量（DATABASE_URL等）
3. 使用Terraform进行基础设施即代码管理

---

### 决策2：AI模型策略 - OpenRouter多模型智能路由

#### 决策内容
使用OpenRouter API统一接口，根据任务类型路由到4个免费模型：

```python
MODEL_ROUTING = {
    # Quick Chat模式
    "quick_qa": "qwen/qwen3-30b-a3b:free",           # 响应快，3-5秒
    "price_query": "openai/gpt-oss-20b:free",        # 结构化输出稳定

    # Deep Research模式
    "tldr_generation": "qwen/qwen3-235b-a22b:free",  # 235B参数，高质量总结
    "sentiment_analysis": "qwen/qwen3-30b-a3b:free", # 中文理解强
    "technical_analysis": "deepseek/deepseek-r1-0528:free",  # 推理能力突出
    "fundamental_analysis": "qwen/qwen3-235b-a22b:free",  # 综合分析能力
    "competitor_analysis": "qwen/qwen3-235b-a22b:free",   # 数据对比准确
    "conclusion_synthesis": "qwen/qwen3-235b-a22b:free",  # 逻辑综合
}
```

#### 理由
1. **成本控制**：
   - 所有模型免费，零AI成本
   - 每日免费额度可支持50-100份Deep Research报告

2. **质量保证**：
   - qwen3-235b的235B参数量接近GPT-3.5/4质量
   - deepseek-r1专注推理，技术分析更准确
   - 多模型结合，各取所长

3. **响应速度**：
   - Quick Chat用30B模型（qwen3-30b），响应快（3秒）
   - Deep Research并行调用，总时长可控（< 30秒）

#### 降级策略
```python
class ModelFallback:
    PRIMARY = "qwen/qwen3-235b-a22b:free"
    FALLBACK_1 = "qwen/qwen3-30b-a3b:free"
    FALLBACK_2 = "openai/gpt-oss-20b:free"
    FALLBACK_3 = "deepseek/deepseek-r1-0528:free"
```

当主模型不可用时（超时/限流/错误）：
1. 自动重试1次（间隔2秒）
2. 降级到FALLBACK_1
3. 如仍失败，降级到FALLBACK_2
4. 最后尝试FALLBACK_3
5. 全部失败则返回错误并记录日志

#### Token使用优化
- **输入Token限制**：每次最多4K tokens（裁剪过长数据）
- **输出Token限制**：每个分析维度最多1K tokens
- **缓存策略**：相同项目24小时内复用报告骨架

---

### 决策3：Deep Research工作流 - 三阶段流水线

#### 决策内容
Deep Research采用**分阶段并行处理**架构：

```
用户请求 "生成Hyperliquid深度研究报告"
    ↓
[阶段1] 数据采集 (5-8秒，并行6个源)
    ├── CoinGecko: 价格/市值/交易量 (1-2秒)
    ├── Etherscan: 链上数据/持币分布 (2-3秒)
    ├── Twitter: 提及量/情绪/话题 (2-3秒)
    ├── Reddit: 讨论热度/帖子 (2-3秒)
    ├── CryptoPanic: 新闻资讯 (1-2秒)
    └── 内部DB: 历史数据/竞品信息 (0.5秒)
    ↓
[阶段2] AI分析 (15-20秒，并行5个分析器)
    ├── TL;DR生成器 (qwen3-235b, 3-4秒)
    ├── 时间窗分析器 (qwen3-30b, 2-3秒)
    ├── 情绪分析器 (qwen3-30b, 2-3秒)
    ├── 技术面分析器 (deepseek-r1, 4-5秒)
    ├── 基本面分析器 (qwen3-235b, 3-4秒)
    ├── 竞品对比分析器 (qwen3-235b, 3-4秒)
    └── 风险评估器 (qwen3-235b, 2-3秒)
    ↓
[阶段3] 报告组装 (2-3秒，串行处理)
    ├── Markdown格式化
    ├── 表格生成（竞品对比/估值倍数）
    ├── 图表嵌入（价格走势/情绪分布）
    └── 结论综合（置信度计算）
    ↓
输出: 完整Markdown报告（3000-5000字）
```

#### 并行化实现
使用Python `asyncio` + `aiohttp`：

```python
async def generate_deep_research(project: str):
    # 阶段1：并行采集数据
    data = await asyncio.gather(
        fetch_coingecko(project),
        fetch_etherscan(project),
        fetch_twitter(project),
        fetch_reddit(project),
        fetch_news(project),
        fetch_db(project)
    )

    # 阶段2：并行AI分析
    analyses = await asyncio.gather(
        generate_tldr(data),
        analyze_timeframe(data),
        analyze_sentiment(data),
        analyze_technical(data),
        analyze_fundamental(data),
        analyze_competitors(data),
        assess_risks(data)
    )

    # 阶段3：串行组装报告
    report = await assemble_report(analyses)
    return report
```

#### 理由
1. **性能优化**：并行处理减少70%总时间（串行50秒 → 并行15-30秒）
2. **用户体验**：实时进度反馈（"正在采集市场数据..." → "正在分析技术面..."）
3. **容错性**：单个数据源失败不影响整体流程

---

### 决策4：数据库设计 - PostgreSQL主库 + Redis缓存

#### Schema设计

```sql
-- 项目基础信息
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,  -- BTC, ETH, HYPE
    name VARCHAR(100) NOT NULL,          -- Bitcoin, Ethereum
    coingecko_id VARCHAR(100),
    metadata JSONB,                      -- 灵活存储额外信息
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 历史快照（时间序列数据）
CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    price DECIMAL(20, 8),
    market_cap BIGINT,
    volume_24h BIGINT,
    tvl BIGINT,
    active_addresses INTEGER,
    twitter_mentions INTEGER,
    reddit_posts INTEGER,
    news_count INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_project_time (project_id, timestamp DESC)
);

-- 分析报告
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER REFERENCES projects(id),
    report_type VARCHAR(20),  -- 'quick_chat' or 'deep_research'
    content_markdown TEXT,
    content_json JSONB,        -- 结构化数据（用于前端渲染）
    metadata JSONB,            -- 模型信息、Token使用等
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,      -- 分享链接过期时间
    share_token VARCHAR(32) UNIQUE,  -- 分享链接ID
    INDEX idx_share (share_token)
);

-- 对话历史
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_session_id VARCHAR(64),  -- 前端生成的sessionId
    messages JSONB,               -- [{role, content, timestamp}]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_session (user_session_id)
);
```

#### Redis缓存策略

```python
CACHE_KEYS = {
    # 价格数据缓存（1分钟）
    "price:{symbol}": 60,

    # 项目元数据缓存（1小时）
    "project:{symbol}": 3600,

    # 完整报告缓存（24小时）
    "report:deep:{symbol}:{date}": 86400,

    # 对话上下文缓存（30分钟）
    "conversation:{session_id}": 1800,

    # API限流（每用户每分钟10次请求）
    "ratelimit:{ip}": 60
}
```

#### 理由
1. **性能**：Redis缓存减少90%数据库查询
2. **成本**：减少外部API调用次数（CoinGecko限流50次/分钟）
3. **扩展性**：时间序列数据支持历史趋势分析

---

### 决策5：Prompt工程策略 - YAML模板 + Few-shot学习

#### Prompt模板结构

```yaml
# prompts/deep_research/tldr.yaml
name: "TL;DR生成器"
model: "qwen/qwen3-235b-a22b:free"
temperature: 0.7
max_tokens: 500

system: |
  你是一位专业的加密货币研究分析师，擅长生成简洁有力的投资判断。

  任务：基于提供的多源数据，生成TL;DR总结。

  输出格式（严格遵循）：
  核心判断: [Bull/Neutral/Bear] (看涨/中性/看跌，置信度 XX%)
  一句话总结: [项目名] 凭借 [核心优势/数据]，展现了 [领域] 的 [地位]。尽管面临 [短期压力]，但其 [核心机制] 和 [增长点] 提供了 [支撑类型]。

  要求：
  1. 置信度基于数据可靠性和市场确定性
  2. 必须包含具体数字（市场份额、收入、增长率）
  3. 平衡机会与风险
  4. 控制在100字以内

few_shot_examples:
  - input: |
      项目：Hyperliquid
      价格：$39.58，24h涨跌：-1.07%
      市值：$107.7亿，排名：第34位
      TVL：$47.3亿，30d变化：-23%
      日活用户：59,600
      30d收入：$1.014亿（年化$12.2亿）
      Twitter情绪：7/10（正面）
      市场份额：DeFi衍生品80%
      催化剂：Robinhood上市、$10亿融资
      风险：11月代币解锁、竞争加剧
    output: |
      核心判断: Bull (看涨，置信度 75%)
      一句话总结: Hyperliquid 凭借 80% 的衍生品市场份额、年化 12 亿美元收入和强劲的机构采用信号（10 亿美元 S-1 申请、Robinhood 上市），展现了 DeFi 基础设施的领先地位。尽管面临 11 月代币解锁和竞争加剧的短期压力，但其 97% 费用回购机制和生态扩张（HyperEVM 达 20 亿美元 TVL）提供了强有力的基本面支撑。

user_template: |
  项目：{project_name}

  市场数据：
  - 价格：${price}，24h涨跌：{change_24h}%
  - 市值：${market_cap}，排名：{rank}
  - 24h成交量：${volume_24h}

  协议数据：
  - TVL：${tvl}，30d变化：{tvl_change_30d}%
  - 日活用户：{daily_active_users}
  - 30d收入：${revenue_30d}

  社交情绪：
  - Twitter提及量：{twitter_mentions}（7d），情绪：{sentiment_score}/10
  - Reddit讨论热度：{reddit_activity}

  竞争地位：
  - 市场份额：{market_share}%
  - 主要竞品：{competitors}

  近期催化剂：
  {catalysts}

  主要风险：
  {risks}
```

#### 理由
1. **可维护性**：YAML集中管理，易于调优
2. **质量保证**：Few-shot示例（基于Hyperliquid PDF）确保输出格式
3. **版本控制**：Git追踪Prompt变更历史

---

## Risks / Trade-offs（风险与权衡）

### 风险1：OpenRouter免费模型可能被滥用导致限流
- **概率**：中等（30%）
- **影响**：无法生成报告，用户体验差
- **缓解措施**：
  1. 实施用户级限流（每IP每小时3次Deep Research）
  2. 准备付费模型降级方案（OpenAI GPT-3.5-turbo $0.002/1K tokens）
  3. 缓存常见项目报告（24小时复用）

### 风险2：Railway成本超预算
- **概率**：低（10%）
- **影响**：月成本超过$10
- **缓解措施**：
  1. 监控Railway使用量（设置$15告警阈值）
  2. 优化数据库查询（减少计算时间）
  3. 准备迁移到Render.com方案（付费$7/月，无睡眠）

### 风险3：数据源API限流或失效
- **概率**：中等（40%）
- **影响**：部分数据缺失，报告质量下降
- **缓解措施**：
  1. 多数据源冗余（CoinGecko + CoinMarketCap）
  2. 降级策略（数据缺失时标注并继续生成）
  3. 监控告警（检测API异常）

### 风险4：AI生成内容质量不稳定
- **概率**：中等（35%）
- **影响**：报告质量波动，用户信任度下降
- **缓解措施**：
  1. 多次采样取最佳（temperature=0.7，生成3次选最好）
  2. 结构化输出验证（JSON Schema检查）
  3. 人工抽检（每日随机抽查5份报告）

---

## Migration Plan（迁移计划）

### MVP → 生产环境
1. **数据迁移**：
   - 导出Railway PostgreSQL数据（`pg_dump`）
   - 迁移到生产数据库（AWS RDS / DigitalOcean）

2. **服务迁移**：
   - 容器化（Docker）
   - 使用Terraform管理基础设施
   - 配置CI/CD（GitHub Actions）

3. **域名配置**：
   - 前端：`web3search.ai` → Vercel
   - 后端：`api.web3search.ai` → Railway/AWS

### 回滚计划
如生产环境出现重大问题：
1. Vercel回滚到上一个稳定版本（1分钟）
2. Railway回滚到上一个Docker镜像（2分钟）
3. 数据库恢复到最近备份（5分钟）

---

## Open Questions（待解决问题）

1. **Q**: 是否需要支持用户登录系统？
   **A**: MVP阶段不需要，使用sessionId追踪用户即可。后续迭代可添加OAuth。

2. **Q**: 报告是否需要支持多语言？
   **A**: MVP仅支持中文/英文。后续可用i18n扩展。

3. **Q**: 是否需要实时价格推送（WebSocket）？
   **A**: MVP使用轮询（每分钟刷新）。实时推送可后续添加。

4. **Q**: PDF导出是否必须在MVP阶段？
   **A**: 是的，这是核心功能（对标asksurf.ai）。使用WeasyPrint实现。

5. **Q**: 是否需要移动端原生应用？
   **A**: 不需要。响应式Web应用即可满足移动端需求。
