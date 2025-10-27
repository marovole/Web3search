# 开发环境设置指南

Web3 Search 本地开发环境完整设置指南。

## 系统要求

- **Python**: 3.11+
- **PostgreSQL**: 14+
- **Redis**: 6+
- **Node.js**: 18+ （前端）
- **OS**: macOS/Linux/Windows（WSL）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/Web3search.git
cd Web3search
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env
# 编辑.env，填入必需的API密钥

# 启动PostgreSQL（Docker）
docker run -d --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:14

# 启动Redis（Docker）
docker run -d --name redis -p 6379:6379 redis:6

# 初始化数据库
python3 -m alembic upgrade head
# 或使用管理端点：
# uvicorn app.main:app --reload
# curl -X POST http://localhost:8000/admin/init-db

# 启动API服务器
uvicorn app.main:app --reload --port 8000
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 启动开发服务器
npm run dev
```

访问：
- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 环境变量配置

### 必需变量

```bash
# .env

# 数据库
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/web3search
REDIS_URL=redis://localhost:6379/0

# LLM API（必需）
OPENROUTER_API_KEY=sk-or-v1-xxx  # 从https://openrouter.ai获取

# 数据源API（可选，但推荐）
COINGECKO_API_KEY=CG-xxx
ETHERSCAN_API_KEY=xxx
TWITTER_BEARER_TOKEN=xxx
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# 应用配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### 获取API密钥

1. **OpenRouter** (必需):
   ```bash
   # 1. 访问https://openrouter.ai
   # 2. 注册账号
   # 3. Keys → Create Key
   # 4. 复制密钥：sk-or-v1-xxx
   ```

2. **CoinGecko** (推荐):
   ```bash
   # 1. 访问https://www.coingecko.com/en/api
   # 2. 注册Developer账号
   # 3. 获取免费API Key
   ```

## 开发工具

### IDE配置（VSCode）

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### 代码格式化

```bash
# 安装工具
pip install black flake8 isort

# 格式化代码
black backend/app
isort backend/app

# 检查代码质量
flake8 backend/app
```

## 测试

### 运行测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api.py

# 查看覆盖率
pytest --cov=app --cov-report=html
# 打开htmlcov/index.html查看报告
```

### 编写测试

```python
# tests/test_quick_chat.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_quick_chat():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/chat/quick-chat",
            json={"query": "What is Bitcoin?"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert len(data["content"]) > 0
```

## 调试

### 断点调试（VSCode）

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### 日志调试

```python
# 临时启用详细日志
import logging
logging.getLogger("app").setLevel(logging.DEBUG)

# 查看SQL查询
# app/core/database.py
engine = create_async_engine(DATABASE_URL, echo=True)
```

## 常见问题

### 1. 端口被占用

```bash
# 查找占用进程
lsof -ti:8000
# 杀死进程
kill -9 $(lsof -ti:8000)
```

### 2. 数据库连接失败

```bash
# 检查PostgreSQL状态
docker ps | grep postgres
# 重启PostgreSQL
docker restart postgres
# 测试连接
psql postgresql://postgres:postgres@localhost:5432/web3search
```

### 3. 模块导入错误

```bash
# 确认PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
# 或使用相对导入
python3 -m app.main
```

---

**版本**: v1.0.0
**最后更新**: 2025-01-27
