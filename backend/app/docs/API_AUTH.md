# API认证说明

Web3 Search API 认证和授权完整指南。

## 目录

1. [当前状态](#当前状态)
2. [未来认证方案](#未来认证方案)
3. [速率限制](#速率限制)
4. [安全最佳实践](#安全最佳实践)

---

## 当前状态

### v1.0.0 - 无认证（公开API）

**当前版本的Web3 Search API是完全公开的，无需认证即可访问。**

这意味着：
- ✅ 无需注册账号
- ✅ 无需API密钥
- ✅ 立即开始使用
- ⚠️ 受速率限制保护（基于IP）

**示例请求**：
```bash
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'
```

### 为什么暂不需要认证？

1. **MVP阶段**：产品处于早期验证阶段
2. **降低门槛**：鼓励用户试用和反馈
3. **速率限制足够**：IP级限流可防止滥用
4. **资源成本可控**：使用免费LLM模型（OpenRouter）

---

## 未来认证方案

### v2.0.0 计划 - API密钥认证

预计实施时间：2025年Q2

#### 认证流程

```
┌──────────┐          ┌──────────┐          ┌──────────┐
│  Client  │          │   API    │          │ Database │
└─────┬────┘          └─────┬────┘          └─────┬────┘
      │                     │                     │
      │ 1. Request with     │                     │
      │    API Key          │                     │
      ├────────────────────>│                     │
      │                     │ 2. Validate Key     │
      │                     ├────────────────────>│
      │                     │ 3. Key Valid?       │
      │                     │<────────────────────┤
      │ 4. Response         │                     │
      │<────────────────────┤                     │
```

#### 使用方式

**HTTP Header认证**（推荐）：
```bash
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'
```

**Query Parameter认证**（不推荐，仅用于快速测试）：
```bash
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat?api_key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'
```

#### API密钥获取

1. 访问 https://web3search.com/dashboard
2. 注册账号并登录
3. 导航到"API Keys"
4. 点击"Generate New Key"
5. 复制并保存密钥（仅显示一次）

#### 密钥管理

**密钥格式**：
```
ws_live_1a2b3c4d5e6f7g8h9i0j
```
- 前缀：`ws_` (Web3 Search)
- 环境：`live_` (生产) 或 `test_` (测试)
- 密钥：32字符随机字符串

**密钥类型**：
- **只读密钥**：仅可调用查询类API
- **读写密钥**：可调用所有API
- **临时密钥**：有效期24小时，用于前端应用

**密钥权限**：
```json
{
  "permissions": [
    "chat:read",
    "reports:read",
    "reports:write",
    "search:read",
    "trending:read"
  ],
  "rate_limits": {
    "quick_chat": 100,
    "deep_research": 20
  },
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### v3.0.0 计划 - OAuth 2.0

预计实施时间：2025年Q4

支持第三方应用接入：
- GitHub OAuth
- Google OAuth
- Wallet Connect（Web3钱包登录）

---

## 速率限制

### 当前限制（基于IP）

| 端点 | 限制 | 时间窗口 | 超限后重试 |
|------|------|----------|-----------|
| `/api/v1/chat/quick-chat` | 10次 | 每分钟 | 60秒 |
| `/api/v1/reports/deep-research` | 3次 | 每小时 | 3600秒 |
| `/api/v1/search/*` | 30次 | 每分钟 | 60秒 |
| `/api/v1/trending/*` | 20次 | 每分钟 | 60秒 |
| `/health` | 无限制 | - | - |

### 响应头

所有请求都包含速率限制信息：

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1706345678
```

### 超限处理

**响应示例**：
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超限，请45秒后重试",
    "status": 429,
    "details": {
      "limit": 10,
      "remaining": 0,
      "reset_at": 1706345678
    }
  }
}
```

### 未来限制（基于API密钥）

**免费计划**：
- Quick Chat: 100次/天
- Deep Research: 20次/天
- 最大并发: 1

**基础计划（$9/月）**：
- Quick Chat: 1000次/天
- Deep Research: 100次/天
- 最大并发: 5

**专业计划（$49/月）**：
- Quick Chat: 10000次/天
- Deep Research: 500次/天
- 最大并发: 20

**企业计划（自定义）**：
- 无限请求
- 专用实例
- 自定义并发

---

## 安全最佳实践

### 1. 保护API密钥（未来）

**❌ 不要**：
```javascript
// 不要在前端代码中硬编码API密钥
const API_KEY = "ws_live_1a2b3c4d5e6f7g8h9i0j";
```

**✅ 应该**：
```javascript
// 使用环境变量
const API_KEY = process.env.WEB3SEARCH_API_KEY;

// 或使用后端代理
fetch("/api/proxy/web3search", {
  method: "POST",
  body: JSON.stringify({ query: "..." })
});
```

### 2. 使用HTTPS

**始终使用HTTPS连接**：
```bash
# ✅ 正确
https://api.web3search.com/api/v1/...

# ❌ 错误
http://api.web3search.com/api/v1/...
```

### 3. 实现请求重试

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

session = create_session()
response = session.post(
    "https://api.web3search.com/api/v1/chat/quick-chat",
    json={"query": "What is Bitcoin?"}
)
```

### 4. 处理敏感数据

**不要在查询中包含敏感信息**：
```bash
# ❌ 错误：包含私钥
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -d '{"query": "My wallet private key is 0x123..."}'

# ✅ 正确：使用通用查询
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -d '{"query": "How to secure my crypto wallet?"}'
```

### 5. 监控API使用

**跟踪请求**：
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_api(query):
    logger.info(f"Calling API with query: {query[:50]}...")
    response = requests.post(API_URL, json={"query": query})

    if response.status_code == 429:
        logger.warning("Rate limit exceeded, backing off...")
    elif response.status_code >= 500:
        logger.error(f"Server error: {response.status_code}")

    return response
```

### 6. 缓存响应

**避免重复请求**：
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_api_call(query_hash):
    # 实际API调用
    response = requests.post(API_URL, json={"query": query_hash})
    return response.json()

def query_api(query):
    # 生成查询哈希
    query_hash = hashlib.md5(query.encode()).hexdigest()
    return cached_api_call(query_hash)
```

---

## CORS配置

### 允许的来源

当前允许的CORS来源：
- `http://localhost:3000` （开发环境）
- `http://localhost:5173` （Vite开发环境）
- `https://*.vercel.app` （所有Vercel部署）
- `https://web3search.com` （生产环境）

### 示例请求

**浏览器JavaScript**：
```javascript
fetch("https://api.web3search.com/api/v1/chat/quick-chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    query: "What is Bitcoin?"
  })
})
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
```

**React示例**：
```jsx
import { useState } from 'react';

function ChatComponent() {
  const [response, setResponse] = useState('');

  const handleQuery = async () => {
    const res = await fetch('https://api.web3search.com/api/v1/chat/quick-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'What is Bitcoin?' })
    });

    const data = await res.json();
    setResponse(data.content);
  };

  return (
    <div>
      <button onClick={handleQuery}>Query</button>
      <p>{response}</p>
    </div>
  );
}
```

---

## 迁移指南

### 当前版本 → v2.0.0（API密钥）

**代码变更**：

**之前**（v1.0.0）：
```python
response = requests.post(
    "https://api.web3search.com/api/v1/chat/quick-chat",
    json={"query": "What is Bitcoin?"}
)
```

**之后**（v2.0.0）：
```python
response = requests.post(
    "https://api.web3search.com/api/v1/chat/quick-chat",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={"query": "What is Bitcoin?"}
)
```

**宽限期**：v2.0.0发布后，v1.0.0（无认证）将继续支持3个月。

---

## 常见问题

### Q1：当前版本需要认证吗？

**A**：不需要。v1.0.0是完全公开的API，无需注册或API密钥。

### Q2：速率限制如何计算？

**A**：基于IP地址，使用滑动窗口算法。每个IP独立计算。

### Q3：如何突破速率限制？

**A**：当前版本无法突破（基于IP）。v2.0.0将支持付费计划提升限额。

### Q4：可以在浏览器中直接调用吗？

**A**：可以，但受CORS限制。确保请求来源在允许列表中。

### Q5：如何获取更高的配额？

**A**：
- **当前**：暂无方法，请合理使用
- **未来**：注册账号并订阅付费计划

---

## 参考资源

- [API错误码](./API_ERRORS.md)
- [API使用教程](./API_TUTORIAL.md)
- [速率限制详情](./RATE_LIMITS.md)
- [安全最佳实践](./SECURITY.md)

---

**版本**：v1.0.0
**最后更新**：2025-01-27
**未来路线图**：[GitHub Roadmap](https://github.com/web3search/roadmap)
