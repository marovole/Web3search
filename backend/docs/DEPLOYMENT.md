# Web3 Search Backend 部署指南

本文档提供完整的部署指南，包括本地开发、Staging环境和生产环境的部署步骤。

## 📚 目录

- [前置要求](#前置要求)
- [本地开发部署](#本地开发部署)
- [Docker部署](#docker部署)
- [Render.com部署](#rendercom部署)
- [中文字体配置](#中文字体配置)
- [WeasyPrint依赖](#weasyprint依赖)
- [环境变量配置](#环境变量配置)
- [数据库迁移](#数据库迁移)
- [监控和日志](#监控和日志)
- [常见问题排查](#常见问题排查)

---

## 前置要求

### 系统要求

- **Python**: 3.10+ (推荐3.11或3.13)
- **PostgreSQL**: 14+
- **Redis**: 6+
- **操作系统**: Linux (Ubuntu 20.04+推荐) / macOS / Windows (WSL2)

### 外部服务

- **OpenRouter API Key**: 用于LLM调用
- **CoinGecko API Key**: 用于加密货币数据（可选，免费版有限制）
- **Sentry DSN**: 用于错误追踪（可选）

---

## 本地开发部署

### 1. 克隆仓库

```bash
git clone https://github.com/marovole/Web3search.git
cd Web3search/backend
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env.dev
```

编辑 `.env.dev`：

```bash
# 基础配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/web3search

# Redis配置
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here  # 可选

# Sentry（可选）
SENTRY_DSN=https://your_sentry_dsn_here
```

### 5. 启动数据库和Redis

使用Docker Compose（推荐）：

```bash
docker-compose up -d postgres redis
```

或者手动启动：

```bash
# PostgreSQL
brew services start postgresql@14  # macOS
sudo systemctl start postgresql    # Linux

# Redis
brew services start redis          # macOS
sudo systemctl start redis         # Linux
```

### 6. 运行数据库迁移

```bash
# 创建数据库（如果不存在）
python -m app.core.database

# 运行迁移（使用Alembic，如果有）
alembic upgrade head
```

### 7. 启动应用

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

---

## Docker部署

### 1. 构建镜像

```bash
docker build -t web3search-backend:latest .
```

### 2. 使用Docker Compose

```bash
docker-compose up -d
```

这将启动：
- FastAPI应用（端口8000）
- PostgreSQL数据库（端口5432）
- Redis缓存（端口6379）

### 3. 查看日志

```bash
docker-compose logs -f app
```

---

## Render.com部署

### 1. 准备Render配置

创建 `render.yaml`：

```yaml
services:
  - type: web
    name: web3search-backend
    env: python
    region: oregon
    plan: standard
    branch: main
    buildCommand: |
      pip install -r requirements.txt
      pip install weasyprint
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: web3search-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: web3search-redis
          type: redis
          property: connectionString
      - key: OPENROUTER_API_KEY
        sync: false  # 手动在Dashboard设置
      - key: SENTRY_DSN
        sync: false  # 手动在Dashboard设置

databases:
  - name: web3search-db
    databaseName: web3search
    plan: starter
    postgresMajorVersion: 15

redis:
  - name: web3search-redis
    plan: starter
    maxmemoryPolicy: noeviction
```

### 2. 部署到Render

**方式1: 通过GitHub连接**

1. 登录 [Render Dashboard](https://dashboard.render.com/)
2. 点击 "New" → "Blueprint"
3. 连接GitHub仓库
4. 选择 `render.yaml` 配置
5. 设置环境变量（OPENROUTER_API_KEY, SENTRY_DSN等）
6. 点击 "Apply" 开始部署

**方式2: 使用Render CLI**

```bash
# 安装Render CLI
npm install -g render-cli

# 登录
render login

# 部署
render blueprint apply
```

### 3. 配置域名（可选）

在Render Dashboard中：
1. 进入Web Service设置
2. 点击 "Custom Domains"
3. 添加自定义域名
4. 配置DNS记录（CNAME或A记录）

### 4. 启用自动部署

在Render Dashboard中：
1. 进入Web Service设置
2. 确保 "Auto-Deploy" 已启用
3. 每次push到main分支会自动触发部署

---

## 中文字体配置

PDF导出功能需要中文字体支持，否则中文字符会显示为方框或乱码。

### Render.com环境

Render.com的Ubuntu环境需要手动安装中文字体。在 `render.yaml` 的 `buildCommand` 中添加：

```yaml
buildCommand: |
  # 安装系统依赖
  apt-get update
  apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-wqy-microhei \
    fonts-wqy-zenhei

  # 安装Python依赖
  pip install -r requirements.txt
  pip install weasyprint markdown2

  # 刷新字体缓存
  fc-cache -f -v
```

### Docker环境

在 `Dockerfile` 中添加：

```dockerfile
FROM python:3.11-slim

# 安装系统依赖和中文字体
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    libpango-1.0-0 \
    libcairo2 \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 验证中文字体

运行以下命令检查中文字体是否可用：

```bash
fc-list :lang=zh
```

应该看到类似输出：

```
/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc: Noto Sans CJK SC:style=Regular
/usr/share/fonts/truetype/wqy/wqy-microhei.ttc: WenQuanYi Micro Hei:style=Regular
```

### CSS字体回退链

应用使用以下字体回退链（`pdf_exporter.py`）：

```css
font-family: 'Noto Sans CJK SC', 'Noto Sans CJK TC', 'Microsoft YaHei',
             'PingFang SC', 'Hiragino Sans GB', 'SimSun', 'SimHei',
             'Arial Unicode MS', 'Helvetica Neue', 'Arial', sans-serif;
```

这确保在不同环境中都能正确显示中文。

---

## WeasyPrint依赖

WeasyPrint用于将HTML/Markdown转换为PDF，需要以下系统依赖。

### 系统依赖

**Ubuntu/Debian:**

```bash
apt-get update
apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info
```

**macOS:**

```bash
brew install cairo pango gdk-pixbuf libffi
```

**Alpine Linux (Docker):**

```bash
apk add --no-cache \
    cairo \
    pango \
    gdk-pixbuf \
    libffi-dev \
    ttf-freefont
```

### Python依赖

在 `requirements.txt` 中已包含：

```txt
weasyprint==66.0
markdown2==2.5.4
Pillow==12.0.0
```

### Render.com配置

在 `render.yaml` 中添加系统依赖：

```yaml
buildCommand: |
  # WeasyPrint系统依赖
  apt-get update
  apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

  # Python依赖
  pip install -r requirements.txt
```

### 验证WeasyPrint

运行以下Python代码测试：

```python
from weasyprint import HTML

html_content = "<html><body><h1>测试中文</h1><p>Hello World</p></body></html>"
HTML(string=html_content).write_pdf("test.pdf")
print("✅ WeasyPrint工作正常")
```

如果成功生成 `test.pdf`，说明WeasyPrint配置正确。

---

## 环境变量配置

### 开发环境 (`.env.dev`)

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:password@localhost:5432/web3search
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
OPENROUTER_API_KEY=sk-or-v1-xxx
```

### Staging环境 (`.env.staging`)

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db:5432/web3search
REDIS_URL=redis://staging-redis:6379/0
CORS_ORIGINS=https://staging.web3search.com
OPENROUTER_API_KEY=sk-or-v1-xxx
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 生产环境 (`.env.production`)

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@prod-db:5432/web3search
REDIS_URL=redis://prod-redis:6379/0
CORS_ORIGINS=https://web3search.com,https://app.web3search.com
OPENROUTER_API_KEY=sk-or-v1-xxx
SENTRY_DSN=https://xxx@sentry.io/xxx
DATABASE_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=50
```

### 关键配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ENVIRONMENT` | 运行环境 | `development` |
| `DEBUG` | 调试模式 | `true` (开发), `false` (生产) |
| `LOG_LEVEL` | 日志级别 | `DEBUG` (开发), `INFO` (生产) |
| `DATABASE_URL` | PostgreSQL连接字符串 | - |
| `REDIS_URL` | Redis连接字符串 | - |
| `OPENROUTER_API_KEY` | OpenRouter API密钥 | - |
| `SENTRY_DSN` | Sentry错误追踪DSN | - (可选) |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:3000` |
| `DATABASE_POOL_SIZE` | 数据库连接池大小 | `10` |
| `REDIS_MAX_CONNECTIONS` | Redis最大连接数 | `10` |

---

## 数据库迁移

### 使用Alembic

如果项目使用Alembic进行数据库迁移：

```bash
# 生成新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 手动迁移

如果没有使用Alembic，在 `app/core/database.py` 中运行：

```python
# 创建所有表
from app.core.database import init_db

async def migrate():
    await init_db()
```

---

## 监控和日志

### Sentry集成

在 `.env` 中配置：

```bash
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10%的请求追踪
```

### 日志配置

查看 `app/core/logging.py` 配置日志输出格式和级别。

生产环境建议：
- `LOG_LEVEL=INFO` 或 `WARNING`
- 使用结构化日志（JSON格式）
- 集成日志聚合服务（如Datadog、CloudWatch）

### 健康检查

- **端点**: `GET /health`
- **监控内容**: 数据库连接、Redis连接、磁盘空间
- **建议频率**: 每30秒

```bash
# 简单健康检查
curl https://api.web3search.com/health
```

### 性能监控

关键指标：
- **Deep Research生成时间**: 目标<60秒
- **PDF导出时间**: 目标<30秒
- **API响应时间（P95）**: 目标<500ms
- **错误率**: 目标<1%

---

## 常见问题排查

### 1. PDF生成失败

**错误**: `ModuleNotFoundError: No module named 'weasyprint'`

**解决**:
```bash
pip install weasyprint markdown2
```

**错误**: `OSError: cannot load library 'libcairo.so.2'`

**解决** (Ubuntu):
```bash
apt-get install libcairo2 libpango-1.0-0
```

### 2. 中文显示为方框

**原因**: 缺少中文字体

**解决**:
```bash
apt-get install fonts-noto-cjk fonts-wqy-microhei
fc-cache -f -v
```

**验证**:
```bash
fc-list :lang=zh  # 应该看到中文字体列表
```

### 3. Redis连接失败

**错误**: `ConnectionError: Error connecting to Redis`

**检查**:
```bash
# 确认Redis运行
redis-cli ping  # 应返回PONG

# 检查连接字符串
echo $REDIS_URL
```

### 4. 数据库连接池耗尽

**错误**: `TimeoutError: QueuePool limit of size X overflow Y reached`

**解决**:
增加连接池大小（`.env`）:
```bash
DATABASE_POOL_SIZE=20
DATABASE_POOL_MAX_OVERFLOW=10
```

### 5. OpenRouter API限流

**错误**: `Rate limit exceeded`

**解决**:
- 使用缓存减少API调用
- 实现请求重试和降级策略
- 升级OpenRouter套餐

### 6. 部署后PDF导出超时

**原因**: Render.com的CPU/内存资源不足

**解决**:
- 升级Render plan（从starter到standard）
- 优化PDF生成代码
- 增加超时时间（在 `pdf_exporter.py` 中调整）

---

## 生产环境检查清单

部署到生产前确认：

- [ ] 环境变量正确配置（`DATABASE_URL`, `REDIS_URL`, `OPENROUTER_API_KEY`）
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=INFO` 或 `WARNING`
- [ ] 数据库迁移已应用
- [ ] 中文字体已安装并验证
- [ ] WeasyPrint系统依赖已安装
- [ ] Sentry错误追踪已配置
- [ ] 健康检查端点可访问
- [ ] CORS配置正确（只允许生产域名）
- [ ] SSL证书已配置
- [ ] 数据库备份策略已设置
- [ ] 监控和告警已配置

---

## 回滚策略

如果部署失败，快速回滚：

**Render.com:**
1. 进入Dashboard → Web Service
2. 点击 "Rollback" 按钮
3. 选择上一个成功的部署

**Docker:**
```bash
# 回滚到上一个镜像
docker-compose down
docker-compose up -d --build
```

**Git:**
```bash
# 回滚代码
git revert HEAD
git push origin main
```

---

## 支持和反馈

遇到问题？
- **文档**: 查看 [API.md](./API.md) 和 [CONFIG.md](./CONFIG.md)
- **GitHub Issues**: https://github.com/marovole/Web3search/issues
- **Email**: marovole@example.com

---

**文档最后更新**: 2025-01-28
