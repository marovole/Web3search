# API集成测试指南

## 概述

本文档提供了Web3 Search项目的API集成测试指南，包括测试策略、最佳实践和常见场景。

## 测试架构

### 测试层级

1. **后端集成测试** (`backend/tests/integration/`)
   - 测试API端点功能
   - 验证环境配置
   - 测试数据库交互

2. **前端集成测试** (`frontend/tests/integration/`)
   - 测试API客户端
   - 验证环境配置
   - 测试错误处理

3. **端到端测试** (`frontend/tests/e2e/`)
   - 完整的用户流程
   - 前后端交互
   - 真实API调用

## 运行测试

### 后端集成测试

```bash
cd backend

# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/integration/test_api_endpoints.py -v

# 生成覆盖率报告
pytest tests/integration/ --cov=app --cov-report=html
```

### 前端集成测试

```bash
cd frontend

# 运行集成测试
npm run test:integration

# 监听模式
npm run test:integration -- --watch

# 生成覆盖率
npm run test:integration -- --coverage
```

### E2E测试

```bash
cd frontend

# 安装Playwright浏览器
npx playwright install

# 运行E2E测试
npm run test:e2e

# 调试模式
npm run test:e2e -- --debug

# UI模式
npm run test:e2e -- --ui
```

## 测试环境配置

### 必需的环境变量

**后端测试:**
```bash
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/test_db
REDIS_URL=redis://localhost:6379/1
ENVIRONMENT=test
API_BASE_URL=http://localhost:8000
```

**前端测试:**
```bash
VITE_API_BASE_URL=https://web3search-api.onrender.com
VITE_ENVIRONMENT=test
```

### 本地测试设置

1. 启动测试数据库和Redis:
```bash
docker-compose -f docker-compose.test.yml up -d
```

2. 设置环境变量:
```bash
cp .env.test.example .env.test
```

3. 运行测试:
```bash
# 后端
cd backend && pytest tests/integration/

# 前端
cd frontend && npm run test:integration
```

## 编写集成测试

### 后端API测试示例

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_quick_chat_endpoint(integration_client: AsyncClient):
    """测试Quick Chat API"""
    response = await integration_client.post(
        "/api/v1/chat/quick",
        json={"query": "What is Bitcoin?", "stream": False}
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
```

### 前端API测试示例

```typescript
import { describe, it, expect } from 'vitest';
import { getEnvConfig } from '../../src/config/env';

describe('API Configuration', () => {
  it('should load valid API URL', () => {
    const config = getEnvConfig();
    expect(config.apiBaseUrl).toMatch(/^https?:\/\//);
  });
});
```

### E2E测试示例

```typescript
import { test, expect } from '@playwright/test';

test('Health check should work', async ({ request }) => {
  const response = await request.get(`${API_BASE_URL}/health`);
  expect(response.ok()).toBeTruthy();
});
```

## 常见测试场景

### 1. API端点存在性测试

验证API端点存在且可访问：

```python
async def test_endpoint_exists(integration_client):
    response = await integration_client.get("/api/v1/endpoint")
    assert response.status_code != 404
```

### 2. 参数验证测试

测试API参数验证：

```python
async def test_invalid_parameters(integration_client):
    response = await integration_client.post(
        "/api/v1/chat/quick",
        json={"invalid": "data"}
    )
    assert response.status_code == 422
```

### 3. 环境配置测试

验证环境配置正确：

```python
def test_production_config():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        assert settings.API_BASE_URL.startswith("https://")
```

### 4. URL路径测试

防止路径重复：

```python
def test_no_path_duplication():
    full_url = f"{settings.API_BASE_URL}/api/v1/test"
    assert "/api/api" not in full_url
```

## 持续集成

### GitHub Actions工作流

集成测试在以下情况自动运行：
- Pull Request创建或更新
- 代码推送到`main`或`develop`分支

工作流包括：
1. 后端集成测试（PostgreSQL + Redis）
2. 前端集成测试
3. E2E测试
4. 测试报告上传

### 测试失败处理

如果集成测试失败：

1. **查看测试日志**
   - 在GitHub Actions的"Actions"标签中查看详细日志
   - 下载测试工件（artifacts）查看详细报告

2. **本地复现**
   ```bash
   # 拉取失败的分支
   git checkout <branch-name>

   # 运行相同的测试
   pytest tests/integration/test_failing_test.py -v
   ```

3. **常见失败原因**
   - 环境配置错误
   - API端点变更
   - 数据库迁移未同步
   - 外部服务不可用

## 最佳实践

### 1. 测试隔离

- 每个测试应该独立运行
- 使用fixtures准备和清理数据
- 不依赖测试执行顺序

### 2. Mock外部依赖

```python
@pytest.fixture
def mock_llm_client():
    mock = Mock()
    mock.generate = Mock(return_value={"content": "test"})
    return mock
```

### 3. 有意义的测试名称

```python
# 好的命名
def test_quick_chat_returns_200_for_valid_query():
    pass

# 不好的命名
def test_chat():
    pass
```

### 4. 断言明确

```python
# 好的断言
assert response.status_code == 200, f"Expected 200, got {response.status_code}"

# 不好的断言
assert response.ok()
```

### 5. 测试覆盖关键路径

优先测试：
- 用户最常用的功能
- 最近变更的代码
- 历史上出现过bug的部分

## 测试覆盖率目标

- **总体目标**: 80%+
- **核心API端点**: 90%+
- **关键业务逻辑**: 95%+

### 查看覆盖率报告

```bash
# 后端
cd backend
pytest tests/integration/ --cov=app --cov-report=html
open htmlcov/index.html

# 前端
cd frontend
npm run test:integration -- --coverage
open coverage/index.html
```

## 故障排查

### 测试超时

如果测试超时：
```bash
# 增加超时时间
pytest tests/integration/ --timeout=60
```

### 数据库连接失败

```bash
# 检查数据库是否运行
docker ps | grep postgres

# 重启数据库
docker-compose restart postgres
```

### Redis连接失败

```bash
# 检查Redis
docker ps | grep redis

# 测试连接
redis-cli ping
```

## 参考资源

- [Pytest文档](https://docs.pytest.org/)
- [Vitest文档](https://vitest.dev/)
- [Playwright文档](https://playwright.dev/)
- [项目README](../README.md)

## 常见问题 (FAQ)

**Q: 为什么要写集成测试？**
A: 集成测试确保各个组件正确协作，能提前发现生产环境才会出现的问题。

**Q: 集成测试和单元测试的区别？**
A: 单元测试测试单个函数/类，集成测试测试多个组件的交互。

**Q: 测试应该多详细？**
A: 专注于关键路径和边界情况，不需要测试每个可能的组合。

**Q: 如何决定是否需要Mock？**
A: 如果外部服务慢、不稳定或需要付费，应该Mock。内部服务尽量使用真实实现。

## 更新日志

- 2025-01-15: 初始版本创建
- 添加后端和前端集成测试框架
- 配置CI/CD自动化测试流程
