# API使用教程

Web3 Search API 实用教程 - 5个常见场景的完整示例。

## 目录

1. [快速开始](#快速开始)
2. [场景1：快速价格查询](#场景1快速价格查询)
3. [场景2：生成深度研究报告](#场景2生成深度研究报告)
4. [场景3：搜索和自动补全](#场景3搜索和自动补全)
5. [场景4：追踪市场热点](#场景4追踪市场热点)
6. [场景5：批量查询优化](#场景5批量查询优化)

---

## 快速开始

### 前置要求

- 基本HTTP请求知识
- curl、Python或JavaScript环境

### 基础URL

```
生产环境: https://api.web3search.com
开发环境: http://localhost:8000
```

### 测试连接

```bash
curl https://api.web3search.com/health
```

**响应**：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T12:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

---

## 场景1：快速价格查询

### 用例
用户想快速了解某个加密货币的当前价格和市场情况。

### API端点
`POST /api/v1/chat/quick-chat`

### cURL示例

```bash
curl -X POST "https://api.web3search.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current price of Bitcoin?"
  }'
```

### Python示例

```python
import requests

def get_crypto_price(symbol):
    """查询加密货币价格"""
    url = "https://api.web3search.com/api/v1/chat/quick-chat"

    payload = {
        "query": f"What is the current price of {symbol}?"
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    print(f"Response: {data['content']}")
    print(f"Query Type: {data['query_type']}")
    print(f"Response Time: {data['response_time']}s")

    return data

# 使用
get_crypto_price("Bitcoin")
```

### JavaScript示例

```javascript
async function getCryptoPrice(symbol) {
  const url = 'https://api.web3search.com/api/v1/chat/quick-chat';

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: `What is the current price of ${symbol}?`
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  console.log('Response:', data.content);
  console.log('Response Time:', data.response_time, 's');

  return data;
}

// 使用
getCryptoPrice('Bitcoin')
  .then(data => console.log(data))
  .catch(err => console.error(err));
```

### 预期响应

```json
{
  "content": "Bitcoin (BTC) is currently trading at $45,000 with a 24-hour change of +2.5%. The market cap is $900B with a trading volume of $25B in the last 24 hours...",
  "symbol": "BTC",
  "query_type": "price",
  "response_time": 2.3,
  "model": "anthropic/claude-3.5-sonnet",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 场景2：生成深度研究报告

### 用例
投资者需要一份详细的加密货币分析报告，包含技术面、基本面、风险评估等。

### API端点
`POST /api/v1/reports/deep-research`

### cURL示例

```bash
curl -X POST "https://api.web3search.com/api/v1/reports/deep-research" \
  -H "Content-Type: "application/json" \
  -d '{
    "symbol": "ETH",
    "format": "markdown"
  }'
```

### Python示例（流式）

```python
import requests

def generate_deep_research_report(symbol, stream=True):
    """生成深度研究报告（流式输出）"""
    url = "https://api.web3search.com/api/v1/reports/deep-research/stream"

    payload = {
        "symbol": symbol,
        "format": "markdown"
    }

    with requests.post(url, json=payload, stream=stream, timeout=60) as response:
        response.raise_for_status()

        if stream:
            # 流式处理
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data = line[6:]  # 移除 "data: " 前缀
                    if data == "[DONE]":
                        print("\n报告生成完成!")
                        break
                    print(data, end="", flush=True)
        else:
            # 非流式
            data = response.json()
            print(data['content'])

# 使用
generate_deep_research_report("ETH", stream=True)
```

### JavaScript示例（流式）

```javascript
async function generateDeepResearchReport(symbol) {
  const url = 'https://api.web3search.com/api/v1/reports/deep-research/stream';

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      symbol: symbol,
      format: 'markdown'
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // 处理流式响应
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      console.log('\n报告生成完成!');
      break;
    }

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          return;
        }
        process.stdout.write(data);
      }
    }
  }
}

// 使用
generateDeepResearchReport('ETH')
  .catch(err => console.error(err));
```

### 预期响应（流式）

```
data: # Ethereum (ETH) 深度研究报告
data:
data: ## TL;DR
data: 🎯 **投资观点**: 中性偏多
data:
data: **牛市论点**:
data: - 以太坊是最大的智能合约平台...
...
data: [DONE]
```

### 异步报告生成（推荐用于大批量）

```python
def generate_report_async(symbol):
    """异步生成报告"""
    # 1. 提交报告生成任务
    url = "https://api.web3search.com/api/v1/reports/deep-research/async"

    response = requests.post(url, json={"symbol": symbol})
    task_id = response.json()["task_id"]

    print(f"任务提交成功: {task_id}")

    # 2. 轮询任务状态
    import time
    status_url = f"https://api.web3search.com/api/v1/reports/status/{task_id}"

    while True:
        status_response = requests.get(status_url)
        status_data = status_response.json()

        if status_data["status"] == "completed":
            print("报告生成完成!")
            print(status_data["result"]["content"])
            break
        elif status_data["status"] == "failed":
            print(f"报告生成失败: {status_data['error']}")
            break
        else:
            print(f"当前状态: {status_data['status']} ({status_data['progress']}%)")
            time.sleep(5)

# 使用
generate_report_async("BTC")
```

---

## 场景3：搜索和自动补全

### 用例
用户在输入框中输入"bit"，需要自动补全建议。

### API端点
`GET /api/v1/search/autocomplete?q={query}`

### cURL示例

```bash
curl "https://api.web3search.com/api/v1/search/autocomplete?q=bit&limit=10"
```

### Python示例

```python
def autocomplete_crypto(query, limit=10):
    """加密货币自动补全"""
    url = "https://api.web3search.com/api/v1/search/autocomplete"

    params = {
        "q": query,
        "limit": limit
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    suggestions = data["suggestions"]

    print(f"找到 {len(suggestions)} 个建议:")
    for item in suggestions:
        print(f"  {item['symbol']}: {item['name']} (${item['price']})")

    return suggestions

# 使用
autocomplete_crypto("bit")
```

### JavaScript示例（防抖）

```javascript
// 实现防抖以优化性能
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

async function autocompleteCrypto(query, limit = 10) {
  const url = `https://api.web3search.com/api/v1/search/autocomplete?q=${encodeURIComponent(query)}&limit=${limit}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.suggestions;
}

// 使用（带防抖）
const debouncedAutocomplete = debounce(async (query) => {
  if (query.length < 2) return;

  try {
    const suggestions = await autocompleteCrypto(query);
    console.log('Suggestions:', suggestions);
    // 更新UI
  } catch (error) {
    console.error('Autocomplete error:', error);
  }
}, 300);  // 300ms防抖

// 绑定到输入框
document.getElementById('search-input').addEventListener('input', (e) => {
  debouncedAutocomplete(e.target.value);
});
```

### 预期响应

```json
{
  "query": "bit",
  "suggestions": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "price": 45000,
      "market_cap": 900000000000,
      "image": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    },
    {
      "symbol": "BCH",
      "name": "Bitcoin Cash",
      "price": 250,
      "market_cap": 5000000000,
      "image": "https://assets.coingecko.com/coins/images/780/small/bitcoin-cash.png"
    }
  ],
  "total": 2
}
```

---

## 场景4：追踪市场热点

### 用例
用户想了解当前市场上最热门的加密货币。

### API端点
`GET /api/v1/trending/hottest`

### cURL示例

```bash
curl "https://api.web3search.com/api/v1/trending/hottest?limit=10"
```

### Python示例

```python
def get_trending_cryptos(limit=10):
    """获取热门加密货币"""
    url = "https://api.web3search.com/api/v1/trending/hottest"

    params = {"limit": limit}

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    trending = data["trending"]

    print(f"🔥 Top {len(trending)} 热门加密货币:")
    for i, item in enumerate(trending, 1):
        print(f"{i}. {item['symbol']}: {item['name']}")
        print(f"   热度评分: {item['hotness_score']}/100")
        print(f"   24h变化: {item['price_change_24h']:+.2f}%")
        print()

    return trending

# 使用
get_trending_cryptos()
```

### React示例（实时更新）

```jsx
import React, { useState, useEffect } from 'react';

function TrendingCryptos() {
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const response = await fetch('https://api.web3search.com/api/v1/trending/hottest?limit=10');
        const data = await response.json();
        setTrending(data.trending);
      } catch (error) {
        console.error('Error fetching trending:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrending();

    // 每5分钟更新一次
    const interval = setInterval(fetchTrending, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>加载中...</div>;

  return (
    <div className="trending-list">
      <h2>🔥 热门加密货币</h2>
      {trending.map((item, index) => (
        <div key={item.symbol} className="trending-item">
          <span className="rank">#{index + 1}</span>
          <img src={item.image} alt={item.name} />
          <span className="name">{item.name} ({item.symbol})</span>
          <span className="score">热度: {item.hotness_score}/100</span>
          <span className={`change ${item.price_change_24h > 0 ? 'positive' : 'negative'}`}>
            {item.price_change_24h > 0 ? '↑' : '↓'} {Math.abs(item.price_change_24h).toFixed(2)}%
          </span>
        </div>
      ))}
    </div>
  );
}

export default TrendingCryptos;
```

### 预期响应

```json
{
  "trending": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "hotness_score": 95,
      "price": 45000,
      "price_change_24h": 5.2,
      "market_cap": 900000000000,
      "volume_24h": 25000000000,
      "image": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png",
      "reasons": ["价格突破", "社交热度高", "新闻频繁"]
    }
  ],
  "updated_at": "2025-01-27T12:00:00Z"
}
```

---

## 场景5：批量查询优化

### 用例
需要同时查询多个加密货币的价格，如何优化性能？

### 策略1：并发请求

```python
import asyncio
import aiohttp

async def fetch_price(session, symbol):
    """异步获取单个价格"""
    url = "https://api.web3search.com/api/v1/chat/quick-chat"
    payload = {"query": f"What is the current price of {symbol}?"}

    async with session.post(url, json=payload) as response:
        data = await response.json()
        return {"symbol": symbol, "content": data["content"]}

async def fetch_multiple_prices(symbols):
    """批量异步获取价格"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_price(session, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                print(f"错误: {result}")
            else:
                print(f"{result['symbol']}: {result['content'][:100]}...")

# 使用
symbols = ["BTC", "ETH", "SOL", "ADA", "DOT"]
asyncio.run(fetch_multiple_prices(symbols))
```

### 策略2：使用缓存

```python
from functools import lru_cache
import hashlib
import time

# 简单的缓存装饰器
def cache_with_ttl(ttl_seconds=300):
    """带TTL的缓存"""
    cache = {}

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()

            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    print(f"缓存命中: {key}")
                    return result

            # 调用函数
            result = func(*args, **kwargs)

            # 存储缓存
            cache[key] = (result, time.time())

            return result

        return wrapper
    return decorator

@cache_with_ttl(ttl_seconds=60)  # 缓存1分钟
def get_crypto_price_cached(symbol):
    """带缓存的价格查询"""
    url = "https://api.web3search.com/api/v1/chat/quick-chat"
    payload = {"query": f"What is the current price of {symbol}?"}

    response = requests.post(url, json=payload)
    return response.json()

# 使用（第二次调用会命中缓存）
for _ in range(2):
    result = get_crypto_price_cached("BTC")
    print(result["content"][:100])
    time.sleep(1)
```

### 策略3：批量搜索端点（推荐）

```python
def batch_search_cryptos(symbols):
    """批量搜索多个加密货币"""
    url = "https://api.web3search.com/api/v1/search/batch"

    payload = {"symbols": symbols}

    response = requests.post(url, json=payload)
    data = response.json()

    for item in data["results"]:
        print(f"{item['symbol']}: ${item['price']} ({item['price_change_24h']:+.2f}%)")

# 使用
batch_search_cryptos(["BTC", "ETH", "SOL", "ADA", "DOT"])
```

---

## 最佳实践总结

### 1. 错误处理

```python
def call_api_with_error_handling(url, payload):
    """带完整错误处理的API调用"""
    try:
        response = requests.post(url, json=payload, timeout=30)

        # 检查HTTP状态码
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # 速率限制
            retry_after = response.headers.get('Retry-After', 60)
            raise Exception(f"速率限制，请{retry_after}秒后重试")
        elif response.status_code >= 500:
            # 服务器错误
            raise Exception(f"服务器错误: {response.status_code}")
        else:
            # 其他错误
            error_data = response.json().get('error', {})
            raise Exception(f"API错误: {error_data.get('message', 'Unknown error')}")

    except requests.Timeout:
        raise Exception("请求超时，请稍后重试")
    except requests.ConnectionError:
        raise Exception("网络连接失败")
```

### 2. 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def logged_api_call(url, payload):
    """带日志的API调用"""
    logger.info(f"调用API: {url}")
    logger.debug(f"Payload: {payload}")

    try:
        response = requests.post(url, json=payload, timeout=30)
        logger.info(f"响应状态: {response.status_code}")

        if response.ok:
            logger.debug(f"响应数据: {response.json()}")
            return response.json()
        else:
            logger.error(f"API错误: {response.text}")
            raise Exception(f"API调用失败: {response.status_code}")

    except Exception as e:
        logger.error(f"异常: {str(e)}", exc_info=True)
        raise
```

### 3. 性能优化

- ✅ 使用连接池（requests.Session）
- ✅ 实现本地缓存（5-10分钟）
- ✅ 并发请求（asyncio/aiohttp）
- ✅ 实现请求防抖（前端）
- ✅ 监控API使用情况

---

## 参考资源

- [API错误码](./API_ERRORS.md)
- [认证说明](./API_AUTH.md)
- [完整API文档](https://api.web3search.com/docs)
- [示例代码库](https://github.com/web3search/examples)

---

**版本**：v1.0.0
**最后更新**：2025-01-27
**维护者**：Web3Search API Team
