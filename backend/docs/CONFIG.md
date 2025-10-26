# 配置管理文档

## 概述

Web3 Search API 使用基于 Pydantic Settings 的配置管理系统，提供：

- ✅ **强类型验证**：自动验证配置值的类型和格式
- ✅ **多环境支持**：.env.dev、.env.staging、.env.prod
- ✅ **敏感信息脱敏**：API keys 在日志中自动隐藏
- ✅ **配置热加载**：开发环境支持动态重载
- ✅ **详细文档**：每个配置项都有描述和验证规则

## 快速开始

### 1. 创建环境配置文件

```bash
# 复制示例配置
cp .env.example .env

# 或针对特定环境
cp .env.example .env.dev
cp .env.example .env.staging
cp .env.example .env.prod
```

### 2. 配置环境变量

编辑 `.env` 或 `.env.{environment}` 文件，设置必要的配置项：

```bash
# 基础配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/web3search

# OpenRouter API（生产环境必填）
OPENROUTER_API_KEY=sk_or_v1_xxxxxxxxxxxxx
```

### 3. 在代码中使用配置

```python
from app.core.config import settings

# 访问配置
print(f"环境: {settings.ENVIRONMENT}")
print(f"数据库URL: {settings.DATABASE_URL}")

# 检查环境
from app.core.config import is_production, is_development

if is_production():
    # 生产环境逻辑
    pass

if is_development():
    # 开发环境逻辑
    pass
```

## 配置验证规则

### 基础配置

| 配置项 | 类型 | 验证规则 | 默认值 |
|--------|------|----------|--------|
| ENVIRONMENT | str | 必须是: development, dev, staging, stage, production, prod | development |
| DEBUG | bool | - | true |
| LOG_LEVEL | str | 必须是: DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO |

### 数据库连接池

| 配置项 | 类型 | 验证规则 | 默认值 |
|--------|------|----------|--------|
| DATABASE_POOL_MIN_SIZE | int | 范围: 1-100 | 10 |
| DATABASE_POOL_MAX_SIZE | int | 范围: 1-200 | 50 |
| DATABASE_POOL_TIMEOUT | float | 范围: 1.0-60.0 秒 | 10.0 |
| DATABASE_COMMAND_TIMEOUT | float | 范围: 1.0-300.0 秒 | 60.0 |

**重要**：`DATABASE_POOL_MIN_SIZE` 必须小于或等于 `DATABASE_POOL_MAX_SIZE`

### API Base URLs

所有 API Base URL 配置项必须：
- 以 `http://` 或 `https://` 开头
- 尾部斜杠会被自动移除

### 缓存TTL

| 配置项 | 类型 | 验证规则 | 默认值 |
|--------|------|----------|--------|
| CACHE_TTL_PRICE | int | 范围: 10-3600 秒 | 60 |
| CACHE_TTL_PROJECT | int | 范围: 300-86400 秒 | 3600 |
| CACHE_TTL_REPORT | int | 范围: 3600-604800 秒 | 86400 |

## 多环境配置

### 环境选择优先级

系统根据 `ENVIRONMENT` 环境变量自动选择配置文件：

1. `.env.{ENVIRONMENT}` （特定环境）
2. `.env` （通用配置）

**示例**：

```bash
# 使用开发环境配置
export ENVIRONMENT=development
# 系统会加载 .env.dev 和 .env

# 使用生产环境配置
export ENVIRONMENT=production
# 系统会加载 .env.prod 和 .env
```

### 环境配置建议

#### 开发环境（.env.dev）

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_ECHO=true  # 输出SQL日志
DATABASE_POOL_MIN_SIZE=5
DATABASE_POOL_MAX_SIZE=20
```

#### 预发布环境（.env.staging）

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_ECHO=false
DATABASE_POOL_MIN_SIZE=10
DATABASE_POOL_MAX_SIZE=30
SENTRY_DSN=your_sentry_dsn  # 启用错误追踪
```

#### 生产环境（.env.prod）

```bash
ENVIRONMENT=production
DEBUG=false  # 强制关闭，即使设置为true
LOG_LEVEL=INFO
DATABASE_ECHO=false  # 强制关闭
DATABASE_POOL_MIN_SIZE=10
DATABASE_POOL_MAX_SIZE=50
OPENROUTER_API_KEY=sk_xxx  # 必填
SENTRY_DSN=your_sentry_dsn
```

## 敏感信息脱敏

### 自动脱敏

所有包含以下关键词的配置项在日志中会被自动脱敏：
- `KEY`
- `TOKEN`
- `SECRET`
- `PASSWORD`
- `DSN`

**示例**：

```python
from app.core.config import settings

# 原始值
settings.OPENROUTER_API_KEY = "sk_or_v1_1234567890abcdef"

# 日志中显示
print(settings.mask_sensitive(settings.OPENROUTER_API_KEY))
# 输出: sk_o...cdef

# 获取安全配置字典（用于日志）
safe_config = settings.get_safe_config()
print(safe_config["OPENROUTER_API_KEY"])
# 输出: sk_o...cdef
```

### 手动脱敏

```python
from app.core.config import settings

# 脱敏任意字符串
masked = settings.mask_sensitive("sensitive_value_123456")
print(masked)  # 输出: sens...456
```

## 配置热加载

在开发环境下，可以动态重新加载配置而无需重启应用：

```python
from app.core.config import reload_settings

# 修改 .env 或 .env.dev 文件后
new_settings = reload_settings()

# 注意：生产环境下此函数不执行任何操作
```

**注意**：
- 仅在开发环境（`ENVIRONMENT=development` 或 `dev`）下有效
- 生产环境会记录警告日志并返回当前配置

## 生产环境特殊处理

生产环境下，系统会自动：

1. **强制关闭 DEBUG**：即使配置为 `true`，也会被强制设为 `false`
2. **强制关闭 DATABASE_ECHO**：禁止输出SQL日志
3. **必填检查**：`OPENROUTER_API_KEY` 必须配置

```python
# 生产环境配置验证
if settings.ENVIRONMENT in ('production', 'prod'):
    assert settings.DEBUG is False
    assert settings.DATABASE_ECHO is False
    assert settings.OPENROUTER_API_KEY  # 不能为空
```

## 辅助函数

### 环境检测

```python
from app.core.config import (
    is_production,
    is_development,
    is_staging
)

if is_production():
    print("当前是生产环境")

if is_development():
    print("当前是开发环境")

if is_staging():
    print("当前是预发布环境")
```

### 获取连接字符串

```python
from app.core.config import (
    get_database_url,
    get_redis_url
)

db_url = get_database_url()
redis_url = get_redis_url()
```

## 配置测试

运行配置验证测试：

```bash
# 运行所有配置测试
pytest tests/test_config.py -v

# 运行特定测试类
pytest tests/test_config.py::TestSettingsValidation -v

# 运行特定测试
pytest tests/test_config.py::TestSettingsValidation::test_environment_validation -v
```

## 故障排查

### 配置验证失败

**问题**：启动时报错 "ValidationError"

**解决**：
1. 检查配置值是否符合验证规则
2. 查看错误消息中的具体字段和要求
3. 参考本文档的"配置验证规则"部分

**示例错误**：
```
ValidationError: 1 validation error for Settings
DATABASE_POOL_MIN_SIZE
  Input should be greater than or equal to 1 [type=greater_than_equal, input_value=0]
```

### 生产环境启动失败

**问题**：生产环境启动报错 "生产环境必须配置OPENROUTER_API_KEY"

**解决**：
1. 确保 `.env.prod` 或环境变量中设置了 `OPENROUTER_API_KEY`
2. 检查值不为空字符串
3. 验证API key格式正确

### 配置未生效

**问题**：修改配置后未生效

**解决**：
1. 确认修改了正确的配置文件（`.env.{ENVIRONMENT}`）
2. 确认 `ENVIRONMENT` 环境变量设置正确
3. 重启应用（生产环境不支持热加载）
4. 开发环境可调用 `reload_settings()`

## 最佳实践

### 1. 环境变量优先级

```bash
# 环境变量 > .env.{environment} > .env > 默认值
export DATABASE_URL="postgresql://..."  # 最高优先级
```

### 2. 敏感信息管理

- ❌ **不要**将包含真实API keys的`.env`文件提交到Git
- ✅ **使用** `.env.example` 作为模板
- ✅ **配置** `.gitignore` 忽略 `.env*` 文件（除了 `.env.example`）

### 3. 配置文档化

每次添加新配置项时：
1. 在 `Settings` 类中添加 `Field` 描述
2. 添加适当的验证规则
3. 更新 `.env.example`
4. 在本文档中记录

### 4. 配置验证

添加新配置时，编写对应的测试：

```python
# tests/test_config.py
def test_new_config_validation(self, monkeypatch):
    """测试新配置项验证"""
    monkeypatch.setenv("NEW_CONFIG", "invalid_value")
    with pytest.raises(ValidationError):
        Settings()
```

## 参考资料

- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI 配置管理](https://fastapi.tiangolo.com/advanced/settings/)
- [环境变量最佳实践](https://12factor.net/config)
