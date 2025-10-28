# Web3 Search Backend API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Web3 Search Backend** 是一个基于FastAPI的加密货币研究和分析API服务，提供快速对话和深度研究功能，支持自动生成专业PDF报告。

## 🚀 核心功能

### 1. Quick Chat - 快速对话 (3秒响应)
- 实时回答加密货币相关问题
- 支持多轮对话和上下文理解
- 自动识别查询类型（价格、技术、对比等）
- 基于Claude 3.5 Sonnet模型

### 2. Deep Research - 深度研究 (15-30秒)
- **九大分析维度**完整覆盖：
  - TL;DR摘要 - 30秒快速了解
  - 时间窗分析 - 短中期走势预测
  - 情绪分析 - 社交媒体和新闻情绪
  - 技术分析 - 图表分析和技术指标
  - 链上数据 - 活跃度和资金流向
  - 竞品分析 - 同赛道竞品对比
  - 代币经济学 - 供应模型和解锁时间表
  - 风险评估 - 多维度风险矩阵
  - 结论与建议 - 投资评级和行动方案

### 3. 自动生成表格和图表 📊
- **6种表格类型**:
  - 竞品对比表（市值、TVL、估值倍数）
  - 估值倍数表（P/S、P/E、市值/TVL）
  - 技术分析关键价位表（支撑阻力位）
  - 代币解锁时间表（解锁计划）
  - 风险矩阵表（风险评估）
  - 催化剂日历表（关键事件）

- **4种图表类型**:
  - 价格走势图（历史趋势）
  - 情绪分布图（社交媒体数据）
  - 估值对比图（竞品估值）
  - 风险热力图（风险可视化）

### 4. 专业PDF导出 📄
- **完整中文字体支持**（Noto Sans CJK）
- **表格和图表高清渲染**
- **专业A4布局**（页边距、目录、页码）
- **30秒内生成**（优化性能）
- **自定义CSS样式**

### 5. 其他功能
- 搜索API - 加密货币自动补全
- 热点API - 市场热点识别
- 报告管理 - 列表、详情、分享
- Redis缓存 - 加速数据访问
- 速率限制 - 防止滥用

---

## 🛠️ 技术栈

### 核心框架
- **FastAPI** - 现代高性能Web框架
- **SQLAlchemy** - ORM和数据库操作
- **Pydantic** - 数据验证和序列化
- **Asyncio** - 异步I/O支持

### 数据和缓存
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和会话存储
- **Alembic** - 数据库迁移工具（可选）

### AI和LLM
- **OpenRouter** - 多模型LLM API网关
- **Claude 3.5 Sonnet** - Quick Chat主力模型
- **Qwen 3 235B** - Deep Research摘要模型
- **DeepSeek R1** - 深度分析模型

### PDF和可视化
- **WeasyPrint** - HTML到PDF转换
- **markdown2** - Markdown解析
- **matplotlib** - 图表生成（可选）
- **Pillow** - 图像处理

### 监控和日志
- **Sentry** - 错误追踪和性能监控
- **Prometheus** - 指标收集（可选）
- **结构化日志** - JSON格式日志输出

---

## 📦 快速开始

### 前置要求

- Python 3.10+（推荐3.11或3.13）
- PostgreSQL 14+
- Redis 6+
- OpenRouter API Key

### 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/marovole/Web3search.git
cd Web3search/backend
```

2. **创建虚拟环境**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

```bash
cp .env.example .env.dev
```

编辑 `.env.dev`：

```bash
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://postgres:password@localhost:5432/web3search
REDIS_URL=redis://localhost:6379/0
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

5. **启动数据库和Redis**

```bash
# 使用Docker Compose（推荐）
docker-compose up -d postgres redis

# 或手动启动
brew services start postgresql@14 redis  # macOS
sudo systemctl start postgresql redis    # Linux
```

6. **运行应用**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **访问API文档**

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

---

## 📖 API文档

完整的API文档请查看：

- **[API.md](./docs/API.md)** - 详细的API端点说明、请求/响应示例、速率限制
- **[DEPLOYMENT.md](./docs/DEPLOYMENT.md)** - 部署指南（本地、Docker、Render.com）
- **[CONFIG.md](./docs/CONFIG.md)** - 配置选项说明

### 快速示例

#### Quick Chat - 快速对话

```bash
curl -X POST "http://localhost:8000/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current price of Bitcoin?",
    "session_id": null
  }'
```

#### Deep Research - 深度研究

```bash
curl -X POST "http://localhost:8000/api/v1/chat/deep-research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze Bitcoin technical and sentiment",
    "symbol": "BTC"
  }'
```

#### 导出PDF报告

```bash
curl "http://localhost:8000/api/v1/reports/123/export/pdf" -o bitcoin_report.pdf
```

---

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/integration/test_report_pipeline.py

# 查看测试覆盖率
pytest --cov=app --cov-report=html
```

### 集成测试

集成测试需要完整的服务栈（PostgreSQL、Redis、外部API）:

```bash
# 启动所有服务
docker-compose up -d

# 运行集成测试
pytest tests/integration/ -v
```

---

## 🚀 部署

### Docker部署

```bash
docker-compose up -d
```

### Render.com部署

1. 连接GitHub仓库到Render
2. 使用 `render.yaml` 配置自动部署
3. 设置环境变量（API Keys等）
4. 等待部署完成

详细步骤请参考 [DEPLOYMENT.md](./docs/DEPLOYMENT.md)

---

## 📊 项目结构

```
backend/
├── app/
│   ├── api/                  # API路由
│   │   └── v1/              # API v1版本
│   ├── core/                # 核心配置
│   │   ├── config.py        # 环境变量配置
│   │   ├── database.py      # 数据库连接
│   │   ├── logging.py       # 日志配置
│   │   └── monitoring.py    # Sentry监控
│   ├── models/              # 数据库模型
│   ├── schemas/             # Pydantic模型
│   ├── services/            # 业务逻辑
│   │   ├── llm.py          # LLM客户端
│   │   ├── data_aggregator.py  # 数据聚合
│   │   ├── research_engine/    # 研究引擎
│   │   │   ├── deep_research.py     # Deep Research主入口
│   │   │   └── analyzers/           # 9个analyzer
│   │   │       ├── tldr_generator.py
│   │   │       ├── timeframe_analyzer.py
│   │   │       ├── sentiment_analyzer.py
│   │   │       ├── technical_analyzer.py
│   │   │       ├── onchain_analyzer.py
│   │   │       ├── competitor_analyzer.py
│   │   │       ├── tokenomics_analyzer.py
│   │   │       ├── risk_assessor.py
│   │   │       └── conclusion_synthesizer.py
│   │   └── report/              # 报告生成
│   │       ├── report_generator.py   # Markdown生成
│   │       ├── table_generator.py    # 表格生成
│   │       ├── chart_generator.py    # 图表生成
│   │       └── pdf_exporter.py       # PDF导出
│   └── main.py              # FastAPI应用入口
├── tests/                   # 测试文件
│   ├── integration/        # 集成测试
│   └── unit/               # 单元测试
├── docs/                    # 文档
│   ├── API.md              # API文档
│   ├── DEPLOYMENT.md       # 部署指南
│   └── CONFIG.md           # 配置说明
├── prompts/                # LLM Prompt模板
│   └── deep_research/      # Deep Research prompts
├── requirements.txt        # Python依赖
├── Dockerfile             # Docker镜像配置
├── docker-compose.yml     # Docker Compose配置
├── render.yaml            # Render部署配置
└── README.md              # 本文件
```

---

## 🔧 配置选项

关键环境变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ENVIRONMENT` | 运行环境（development/staging/production） | `development` |
| `DEBUG` | 调试模式 | `true` |
| `DATABASE_URL` | PostgreSQL连接字符串 | - |
| `REDIS_URL` | Redis连接字符串 | - |
| `OPENROUTER_API_KEY` | OpenRouter API密钥 | - |
| `SENTRY_DSN` | Sentry错误追踪DSN | - |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:3000` |

完整配置选项请查看 [CONFIG.md](./docs/CONFIG.md)

---

## 📈 性能指标

### 目标性能

| 指标 | 目标值 | 说明 |
|------|--------|------|
| Quick Chat响应时间 | <3秒 | 90%的请求 |
| Deep Research生成时间 | <60秒 | 完整报告 |
| PDF导出时间 | <30秒 | 标准报告（10-20页） |
| API可用性 | >99.5% | 月度统计 |
| 错误率 | <1% | 所有请求 |

### 监控和告警

- **Sentry**: 错误追踪和性能监控
- **健康检查**: `/health` 端点（每30秒）
- **关键指标**: 响应时间、错误率、吞吐量

---

## 🤝 贡献指南

欢迎贡献代码和提出建议！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8风格指南
- 使用`black`格式化代码
- 添加类型注解（Type Hints）
- 编写单元测试（覆盖率>80%）
- 更新相关文档

---

## 📝 更新日志

### v1.0.0 (2025-01-28)

**新增功能**:
- ✨ Deep Research九大分析维度
- 📊 自动生成6种表格和4种图表
- 📄 PDF导出功能（完整中文支持）
- 🚀 性能优化（智能缓存预热）
- 📈 监控和日志系统

**改进**:
- 🔧 统一Analyzer输出接口
- 🎨 优化PDF CSS样式
- ⚡ 超时控制和错误处理
- 📚 完善API和部署文档

---

## 📄 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](../LICENSE) 文件。

---

## 🔗 链接

- **GitHub**: https://github.com/marovole/Web3search
- **文档**: https://docs.web3search.com （规划中）
- **API**: https://api.web3search.com
- **问题反馈**: https://github.com/marovole/Web3search/issues

---

## 👥 联系方式

- **Email**: marovole@example.com
- **Twitter**: @Web3Search （规划中）
- **Discord**: Web3 Search Community （规划中）

---

**⭐ 如果这个项目对你有帮助，请给我们一个Star！**

---

**最后更新**: 2025-01-28
