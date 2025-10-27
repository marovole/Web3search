# API错误码说明

Web3 Search API 错误码完整参考文档。

## 目录

1. [错误响应格式](#错误响应格式)
2. [HTTP状态码](#http状态码)
3. [业务错误码](#业务错误码)
4. [常见错误处理](#常见错误处理)

---

## 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误描述",
    "status": 400,
    "details": {
      "field": "额外的错误详情（仅DEBUG模式）"
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 业务错误码（大写，下划线分隔） |
| `message` | string | 用户友好的错误描述（中文） |
| `status` | integer | HTTP状态码 |
| `details` | object | 额外详情（仅DEBUG模式，生产环境不返回） |
| `request_id` | string | 请求追踪ID（用于日志查询） |

---

## HTTP状态码

### 2xx - 成功

| 状态码 | 说明 | 示例 |
|--------|------|------|
| **200** | OK | 请求成功 |
| **201** | Created | 资源创建成功 |

### 4xx - 客户端错误

#### 400 Bad Request
请求参数错误或格式不正确。

**常见场景**：
- JSON格式错误
- 必填参数缺失
- 参数类型错误

**示例**：
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "status": 400,
    "details": {
      "errors": [
        {
          "field": "query",
          "message": "field required",
          "type": "value_error.missing"
        }
      ]
    }
  }
}
```

#### 401 Unauthorized
认证失败或未提供认证信息。

**常见场景**：
- API密钥缺失
- API密钥无效
- Token过期

**示例**：
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "认证失败，请提供有效的API密钥",
    "status": 401
  }
}
```

**注**：当前版本未实现认证，此错误码保留用于未来版本。

#### 403 Forbidden
请求被拒绝，权限不足。

**常见场景**：
- 访问受限资源
- 权限不足

**示例**：
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "权限不足，无法访问该资源",
    "status": 403
  }
}
```

#### 404 Not Found
请求的资源不存在。

**常见场景**：
- 项目ID不存在
- 报告ID不存在
- 端点路径错误

**示例**：
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "请求的资源不存在",
    "status": 404
  }
}
```

#### 422 Unprocessable Entity
请求格式正确，但语义错误。

**常见场景**：
- Pydantic验证失败
- 业务规则验证失败

**示例**：
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "status": 422,
    "details": {
      "errors": [
        {
          "field": "symbol",
          "message": "symbol must be uppercase",
          "type": "value_error"
        }
      ]
    }
  }
}
```

#### 429 Too Many Requests
速率限制超限。

**限流规则**：
- Quick Chat: 10次/分钟（基于IP）
- Deep Research: 3次/小时（基于IP）

**响应头**：
- `X-RateLimit-Limit`: 限流阈值
- `X-RateLimit-Remaining`: 剩余请求数
- `X-RateLimit-Reset`: 重置时间（Unix timestamp）
- `Retry-After`: 建议重试的秒数

**示例**：
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超限，请稍后重试",
    "status": 429,
    "details": {
      "limit": 10,
      "remaining": 0,
      "reset_at": 1706345678
    }
  }
}
```

### 5xx - 服务器错误

#### 500 Internal Server Error
服务器内部错误。

**常见场景**：
- 未捕获的异常
- 数据库连接失败
- 第三方API调用失败

**示例**：
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "服务暂时不可用，请稍后重试",
    "status": 500,
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**排查步骤**：
1. 记录`request_id`
2. 联系技术支持
3. 查看Sentry错误详情

#### 503 Service Unavailable
服务暂时不可用。

**常见场景**：
- 数据库连接失败
- Redis连接失败
- 系统维护中

**示例**：
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "服务暂时不可用，请稍后重试",
    "status": 503
  }
}
```

#### 504 Gateway Timeout
网关超时。

**常见场景**：
- LLM调用超时（>30s）
- 数据采集超时
- 报告生成超时

**示例**：
```json
{
  "error": {
    "code": "TIMEOUT",
    "message": "请求处理超时，请稍后重试",
    "status": 504
  }
}
```

---

## 业务错误码

### 数据相关

#### DATA_NOT_FOUND
请求的数据不存在或未找到。

**HTTP状态码**: 404

**常见场景**：
- 查询的加密货币符号不存在
- 历史数据不可用

**示例**：
```json
{
  "error": {
    "code": "DATA_NOT_FOUND",
    "message": "未找到符号为 'INVALID' 的加密货币",
    "status": 404
  }
}
```

#### DATA_SOURCE_ERROR
数据源访问失败。

**HTTP状态码**: 503

**常见场景**：
- CoinGecko API不可用
- Etherscan API限流
- Twitter API失败

**示例**：
```json
{
  "error": {
    "code": "DATA_SOURCE_ERROR",
    "message": "数据源暂时不可用：CoinGecko API",
    "status": 503,
    "details": {
      "source": "coingecko",
      "reason": "429 Too Many Requests"
    }
  }
}
```

**处理建议**：
- 等待1-5分钟后重试
- 系统会自动切换到fallback数据源
- 持续失败请联系支持

### AI相关

#### LLM_ERROR
LLM调用失败。

**HTTP状态码**: 500

**常见场景**：
- OpenRouter API不可用
- Token超限
- 模型超时

**示例**：
```json
{
  "error": {
    "code": "LLM_ERROR",
    "message": "AI分析失败，请稍后重试",
    "status": 500,
    "details": {
      "model": "anthropic/claude-3.5-sonnet",
      "reason": "API timeout"
    }
  }
}
```

#### PROMPT_TOO_LONG
Prompt长度超过限制。

**HTTP状态码**: 400

**限制**：
- Quick Chat: 500 tokens
- Deep Research: 2000 tokens

**示例**：
```json
{
  "error": {
    "code": "PROMPT_TOO_LONG",
    "message": "查询内容过长，请简化后重试",
    "status": 400,
    "details": {
      "max_tokens": 500,
      "actual_tokens": 650
    }
  }
}
```

### 报告相关

#### REPORT_GENERATION_FAILED
报告生成失败。

**HTTP状态码**: 500

**常见场景**：
- 数据不足
- LLM生成失败
- 格式化错误

**示例**：
```json
{
  "error": {
    "code": "REPORT_GENERATION_FAILED",
    "message": "报告生成失败，请稍后重试",
    "status": 500
  }
}
```

#### REPORT_NOT_READY
报告尚未生成完成。

**HTTP状态码**: 202

**说明**：这不是错误，而是表示报告正在生成中。

**示例**：
```json
{
  "status": "processing",
  "message": "报告正在生成中，请稍后查询",
  "report_id": "rpt_abc123",
  "estimated_time": 30
}
```

### 数据库相关

#### DATABASE_ERROR
数据库操作失败。

**HTTP状态码**: 500

**常见场景**：
- 连接池耗尽
- 查询超时
- 约束冲突

**示例**：
```json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "数据库操作失败，请稍后重试",
    "status": 500
  }
}
```

### 缓存相关

#### CACHE_ERROR
缓存操作失败（不影响主功能）。

**HTTP状态码**: 200（警告，不中断请求）

**说明**：缓存失败时，系统会自动降级到直接数据查询。

---

## 常见错误处理

### 场景1：符号不存在

**请求**：
```bash
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is INVALID coin?"}'
```

**响应**：
```json
{
  "error": {
    "code": "DATA_NOT_FOUND",
    "message": "未找到符号为 'INVALID' 的加密货币",
    "status": 404
  }
}
```

**处理**：
- 检查符号拼写
- 使用`/api/v1/search/autocomplete?q=symbol`搜索正确符号
- 访问CoinGecko确认符号存在

### 场景2：速率限制

**请求**：
```bash
# 第11次请求（超过10次/分钟限制）
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "BTC price"}'
```

**响应**：
```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706345678
Retry-After: 45

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超限，请45秒后重试",
    "status": 429
  }
}
```

**处理**：
- 等待`Retry-After`秒后重试
- 实现客户端请求队列
- 考虑批量查询优化

### 场景3：服务器超时

**请求**：
```bash
curl -X POST "https://api.web3search.com/api/v1/reports/deep-research" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC"}'
```

**响应**：
```json
{
  "error": {
    "code": "TIMEOUT",
    "message": "报告生成超时，请稍后重试",
    "status": 504
  }
}
```

**处理**：
- 使用异步报告生成（推荐）
- 增加客户端超时时间（>60s）
- 联系支持获取报告状态

### 场景4：参数验证失败

**请求**：
```bash
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{}'  # 缺少query字段
```

**响应**：
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "status": 422,
    "details": {
      "errors": [
        {
          "field": "query",
          "message": "field required",
          "type": "value_error.missing"
        }
      ]
    }
  }
}
```

**处理**：
- 检查请求参数完整性
- 参考API文档确认必填字段
- 验证参数类型和格式

---

## 错误处理最佳实践

### 客户端实现

```python
import requests
import time

def call_api_with_retry(url, data, max_retries=3):
    """带重试的API调用"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data, timeout=30)

            # 成功
            if response.status_code == 200:
                return response.json()

            # 速率限制
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited, waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            # 服务器错误（可重试）
            if response.status_code >= 500:
                wait_time = 2 ** attempt  # 指数退避
                print(f"Server error, retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            # 客户端错误（不重试）
            if response.status_code >= 400:
                error = response.json().get('error', {})
                raise Exception(f"API Error: {error.get('message')}")

        except requests.Timeout:
            print(f"Timeout, retrying ({attempt + 1}/{max_retries})...")
            time.sleep(2 ** attempt)
            continue

    raise Exception("Max retries exceeded")
```

### JavaScript实现

```javascript
async function callApiWithRetry(url, data, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      // 成功
      if (response.ok) {
        return await response.json();
      }

      // 速率限制
      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        console.log(`Rate limited, waiting ${retryAfter}s...`);
        await sleep(retryAfter * 1000);
        continue;
      }

      // 服务器错误（可重试）
      if (response.status >= 500) {
        const waitTime = Math.pow(2, attempt) * 1000;
        console.log(`Server error, retrying in ${waitTime}ms...`);
        await sleep(waitTime);
        continue;
      }

      // 客户端错误（不重试）
      const error = await response.json();
      throw new Error(`API Error: ${error.error.message}`);

    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      await sleep(Math.pow(2, attempt) * 1000);
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## 调试技巧

### 1. 使用request_id追踪

所有500错误都包含`request_id`，用于在Sentry中查询详细日志：

```bash
# 复制request_id
request_id="550e8400-e29b-41d4-a716-446655440000"

# 在Sentry中搜索
# 筛选条件: tags.request_id:$request_id
```

### 2. 查看详细堆栈（DEBUG模式）

开发环境设置`DEBUG=true`可以看到详细错误信息：

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Database connection failed",
    "status": 500,
    "details": {
      "traceback": "Traceback (most recent call last):\n  ..."
    }
  }
}
```

### 3. 使用健康检查

在调用API前，先检查服务状态：

```bash
curl https://api.web3search.com/health
```

---

## 参考资源

- [API文档](https://api.web3search.com/docs)
- [监控指南](./MONITORING_GUIDE.md)
- [故障排查](./TROUBLESHOOTING.md)
- [HTTP状态码RFC](https://tools.ietf.org/html/rfc7231)

---

**版本**：v1.0.0
**最后更新**：2025-01-27
**维护者**：Web3Search API Team
