# Web3 Search API 文档

## 📚 目录

- [API概览](#api概览)
- [认证与授权](#认证与授权)
- [速率限制](#速率限制)
- [错误处理](#错误处理)
- [聊天API](#聊天api)
- [报告API](#报告api)
- [搜索API](#搜索api)
- [热点API](#热点api)

---

## API概览

### 基础信息

- **Base URL (本地)**: `http://localhost:8000`
- **Base URL (生产)**: `https://web3search-api.onrender.com`
- **API版本**: v1
- **数据格式**: JSON
- **编码**: UTF-8

### 快速链接

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## 认证与授权

### 当前状态

目前API暂不需要认证，所有端点均可公开访问。

### 未来计划

- [ ] JWT Token认证
- [ ] API Key认证
- [ ] OAuth 2.0支持
- [ ] 用户角色权限管理

---

## 速率限制

### 限制策略

所有API端点均基于IP地址进行速率限制：

| 端点 | 限制 | 说明 |
|------|------|------|
| `/api/v1/chat/quick-chat` | 10次/分钟 | 快速对话 |
| `/api/v1/chat/deep-research` | 3次/小时 | 深度研究 |
| `/api/v1/reports/*` | 30次/分钟 | 报告查询 |
| `/api/v1/search/*` | 30次/分钟 | 搜索功能 |
| `/api/v1/trending/*` | 30次/分钟 | 热点查询 |

### 响应头

速率限制信息通过以下HTTP头返回：

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1706270400
```

### 429错误

超过速率限制时返回：

```json
{
  "detail": "Rate limit exceeded. Try again in 42 seconds.",
  "retry_after": 42
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "用户友好的错误消息",
  "details": {
    "field": "query",
    "reason": "Query cannot be empty"
  }
}
```

### HTTP状态码

| 状态码 | 说明 | 示例 |
|--------|------|------|
| 200 | 成功 | 请求成功处理 |
| 400 | 请求错误 | 参数验证失败 |
| 404 | 未找到 | 报告不存在 |
| 429 | 速率限制 | 请求过于频繁 |
| 500 | 服务器错误 | 内部错误 |

### 自定义错误码

| 错误码 | 说明 |
|--------|------|
| `VALIDATION_ERROR` | 输入验证失败 |
| `DATA_COLLECTION_ERROR` | 数据采集失败 |
| `LLM_ERROR` | AI模型调用失败 |
| `RESOURCE_NOT_FOUND` | 资源未找到 |
| `RATE_LIMIT_EXCEEDED` | 超过速率限制 |

---

## 聊天API

### Quick Chat - 快速对话

快速回答加密货币相关问题，3秒内响应。

**端点**: `POST /api/v1/chat/quick-chat`

**请求体**:
```json
{
  "query": "What is the current price of Bitcoin?",
  "session_id": null
}
```

**响应**:
```json
{
  "content": "Bitcoin (BTC) is currently trading at $45,000...",
  "symbol": "BTC",
  "query_type": "price",
  "response_time": 2.3,
  "model": "anthropic/claude-3.5-sonnet",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**特性**:
- ⚡ 目标响应时间 < 3秒
- 🤖 使用Claude 3.5 Sonnet模型
- 💬 支持多轮对话
- 🔄 自动识别查询类型

**支持的查询类型**:
- 价格查询: "What is the current price of Bitcoin?"
- 市场概览: "Tell me about Ethereum's performance today"
- 技术解释: "How does Uniswap work?"
- 对比分析: "Compare Bitcoin and Ethereum"

**速率限制**: 10次/分钟

**示例代码**:

```bash
# cURL
curl -X POST "http://localhost:8000/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current price of Bitcoin?",
    "session_id": null
  }'
```

```python
# Python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/chat/quick-chat",
        json={
            "query": "What is the current price of Bitcoin?",
            "session_id": None
        }
    )
    print(response.json())
```

```javascript
// JavaScript
const response = await fetch('http://localhost:8000/api/v1/chat/quick-chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'What is the current price of Bitcoin?',
    session_id: null
  })
});
const data = await response.json();
console.log(data);
```

---

### Deep Research - 深度研究

生成全面的深度研究报告，包含九个核心维度的分析，**自动生成表格和图表**。

**端点**: `POST /api/v1/chat/deep-research`

**请求体**:
```json
{
  "query": "Bitcoin",
  "symbol": "BTC",
  "session_id": null
}
```

**响应**:
```json
{
  "report_id": 123,
  "symbol": "BTC",
  "query": "Bitcoin",
  "tldr": "Bitcoin shows bullish momentum with strong fundamentals...",
  "sections": {
    "market_overview": "Current price: $45,000...",
    "technical_analysis": "Strong uptrend with RSI at 65...",
    "sentiment": "Positive sentiment across social media...",
    "onchain": "Active addresses increasing...",
    "tokenomics": "Fixed supply of 21M BTC...",
    "risks": "Regulatory uncertainty remains..."
  },
  "conclusion": "Overall outlook is positive with moderate risk...",
  "markdown_content": "# Bitcoin Deep Research Report\n\n## TLDR...",
  "data_sources": ["CoinGecko", "Etherscan", "Twitter"],
  "models_used": ["claude-3.5-sonnet", "llama-3.1-70b"],
  "generation_time": 25.3,
  "quality_score": 92,
  "timestamp": "2025-01-26T10:00:00Z",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**九大分析维度**:
1. **TL;DR摘要** - 30秒快速了解核心观点
2. **时间窗分析** - 短期/中期价格走势和关键事件
3. **情绪分析** - 社交媒体、新闻情绪（含情绪分布图）
4. **技术分析** - 趋势、支撑阻力、技术指标（含关键价位表）
5. **链上数据** - 活跃地址、交易量、持币分布
6. **竞品分析** - 同赛道竞品对比（含对比表和估值图）
7. **代币经济学** - 供应模型、解锁时间表（含代币分配表）
8. **风险评估** - 技术风险、监管风险、市场风险（含风险矩阵）
9. **结论与建议** - 投资建议、催化剂日历（含行动建议表）

**📊 自动生成的表格和图表**:
报告会根据数据可用性自动生成以下可视化内容：

**表格类型**（6种）:
- 竞品对比表（市值、TVL、估值倍数等）
- 估值倍数表（P/S、P/E、市值/TVL等）
- 技术分析关键价位表（支撑位、阻力位）
- 代币解锁时间表（解锁时间、数量、百分比）
- 风险矩阵表（风险类型、严重程度、影响）
- 催化剂日历表（事件、时间、预期影响）

**图表类型**（4种）:
- 价格走势图（历史价格变化趋势）
- 情绪分布图（社交媒体提及量分布）
- 估值对比图（竞品估值倍数对比）
- 风险热力图（多维度风险可视化）

> 💡 **提示**: 表格和图表以Base64格式嵌入Markdown，可直接在PDF中渲染

**质量评分标准**:
- 90-100分: 优秀（所有维度完整，数据丰富）
- 70-89分: 良好（大部分维度完整）
- 50-69分: 一般（部分维度缺失）
- <50分: 需改进（多个维度缺失）

**生成时间**:
- 目标: 15-30秒
- 最大: 60秒（超时）

**速率限制**: 3次/小时

---

## 报告API

### 获取报告列表

分页查询所有研究报告，支持筛选和排序。

**端点**: `GET /api/v1/reports`

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `symbol` | string | 否 | - | 按币种筛选（如 BTC, ETH） |
| `report_type` | string | 否 | - | 按类型筛选 |
| `status` | string | 否 | - | 按状态筛选 |
| `page` | int | 否 | 1 | 页码（从1开始） |
| `page_size` | int | 否 | 10 | 每页数量（1-100） |
| `order_by` | string | 否 | created_at | 排序字段 |
| `order_desc` | bool | 否 | true | 是否降序 |

**响应**:
```json
{
  "reports": [
    {
      "id": 123,
      "title": "Bitcoin 深度研究报告",
      "symbol": "BTC",
      "query": "Bitcoin",
      "tldr": "Bitcoin shows bullish momentum...",
      "report_type": "deep_research",
      "status": "completed",
      "quality_score": 92,
      "generation_time": 25.3,
      "created_at": "2025-01-26T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

**示例请求**:
```bash
# 获取所有BTC报告
curl "http://localhost:8000/api/v1/reports?symbol=BTC&page=1&page_size=10"

# 按质量评分降序
curl "http://localhost:8000/api/v1/reports?order_by=quality_score&order_desc=true"
```

**速率限制**: 30次/分钟

---

### 获取报告详情

获取完整的研究报告内容。

**端点**: `GET /api/v1/reports/{report_id}`

**路径参数**:
- `report_id`: 报告ID（整数）

**响应**:
```json
{
  "id": 123,
  "symbol": "BTC",
  "query": "Bitcoin",
  "title": "Bitcoin 深度研究报告",
  "markdown_content": "# Bitcoin Deep Research Report\n\n## TLDR\n...",
  "tldr": "Bitcoin shows bullish momentum...",
  "report_type": "deep_research",
  "status": "completed",
  "quality_score": 92,
  "generation_time": 25.3,
  "data_sources": ["CoinGecko", "Etherscan", "Twitter"],
  "created_at": "2025-01-26T10:00:00",
  "completed_at": "2025-01-26T10:00:25"
}
```

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/reports/123"
```

**速率限制**: 30次/分钟

---

### 创建分享链接

为报告生成可公开访问的分享链接。

**端点**: `POST /api/v1/reports/{report_id}/share`

**路径参数**:
- `report_id`: 报告ID

**请求体**:
```json
{
  "expires_in_days": 30
}
```

**响应**:
```json
{
  "share_token": "abc123def456",
  "share_url": "https://web3search.com/shared/abc123def456",
  "expires_at": "2025-02-26T10:00:00"
}
```

**特性**:
- 🔗 生成唯一的分享令牌
- ⏰ 可设置过期时间（1-365天）
- 🔒 只能分享已完成的报告
- 🚫 可随时禁用分享链接

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/reports/123/share" \
  -H "Content-Type: application/json" \
  -d '{"expires_in_days": 30}'
```

---

### 获取分享报告

通过分享令牌访问报告，无需认证。

**端点**: `GET /api/v1/reports/shared/{share_token}`

**路径参数**:
- `share_token`: 分享令牌

**响应**:
```json
{
  "title": "Bitcoin 深度研究报告",
  "symbol": "BTC",
  "markdown_content": "# Bitcoin Deep Research Report\n\n...",
  "tldr": "Bitcoin shows bullish momentum...",
  "report_type": "deep_research",
  "quality_score": 92,
  "data_sources": ["CoinGecko", "Etherscan"],
  "created_at": "2025-01-26T10:00:00"
}
```

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/reports/shared/abc123def456"
```

---

### 导出报告为PDF

将Markdown格式的研究报告导出为专业的PDF文档，支持中文字体、表格和图表渲染。

**端点**: `GET /api/v1/reports/{report_id}/export/pdf`

**路径参数**:
- `report_id`: 报告ID（整数）

**响应**:
- **Content-Type**: `application/pdf`
- **Content-Disposition**: `attachment; filename="BTC_深度研究报告_20250128.pdf"`
- **Body**: PDF文件的二进制数据

**特性**:
- 📄 专业PDF布局（A4尺寸，页边距优化）
- 🇨🇳 完整中文字体支持（Noto Sans CJK）
- 📊 表格和图表高清渲染
- ⚡ 30秒内生成完成
- 🎨 自定义CSS样式
- 📑 自动生成目录和页码
- 🔒 只能导出已完成的报告

**PDF内容包含**:
1. 报告标题和生成时间
2. TL;DR摘要
3. 九大分析维度的详细内容
4. 自动生成的表格（竞品对比、关键价位、风险矩阵等）
5. 自动生成的图表（价格走势、情绪分布、估值对比等）
6. 数据来源和使用模型
7. 免责声明

**示例请求**:
```bash
# 下载PDF文件
curl "http://localhost:8000/api/v1/reports/123/export/pdf" -o bitcoin_report.pdf

# 使用wget
wget "http://localhost:8000/api/v1/reports/123/export/pdf" -O bitcoin_report.pdf
```

```python
# Python示例
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/reports/123/export/pdf"
    )

    # 保存PDF文件
    with open("bitcoin_report.pdf", "wb") as f:
        f.write(response.content)

    print(f"PDF已保存，大小: {len(response.content)} bytes")
```

```javascript
// JavaScript示例
const response = await fetch('http://localhost:8000/api/v1/reports/123/export/pdf');
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'bitcoin_report.pdf';
a.click();
```

**错误响应**:

```json
{
  "detail": "报告未找到或未完成"
}
```
- **400**: 报告未完成（仍在生成中）
- **404**: 报告不存在
- **500**: PDF生成失败（超时或系统错误）

**性能指标**:
- 小型报告（<10页）：5-10秒
- 中型报告（10-20页）：10-20秒
- 大型报告（20-30页）：20-30秒
- 超时限制：30秒

**速率限制**: 10次/分钟（防止滥用）

---

## 搜索API

### 自动补全搜索

根据用户输入返回匹配的加密货币列表。

**端点**: `GET /api/v1/search/autocomplete`

**查询参数**:
- `q`: 搜索关键词（1-100字符）

**响应**:
```json
{
  "results": [
    {
      "coingecko_id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "market_cap_rank": 1,
      "thumb": "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png"
    }
  ],
  "count": 1
}
```

**特性**:
- ⚡ 快速响应（< 500ms）
- 🔍 模糊搜索（支持部分匹配）
- 📊 按市值排名排序
- 🖼️ 包含币种图标

**搜索策略**:
- 优先匹配币种符号（如 "BTC" → Bitcoin）
- 其次匹配币种名称（如 "bit" → Bitcoin, BitTorrent）
- 最多返回10个结果

**示例请求**:
```bash
# 搜索BTC
curl "http://localhost:8000/api/v1/search/autocomplete?q=btc"

# 搜索包含"uni"的币种
curl "http://localhost:8000/api/v1/search/autocomplete?q=uni"
```

**速率限制**: 30次/分钟

---

## 热点API

### 获取市场热点

多维度识别当前最热门的加密货币。

**端点**: `GET /api/v1/trending/hotspots`

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `limit` | int | 否 | 10 | 返回数量（1-50） |
| `force_refresh` | bool | 否 | false | 强制刷新缓存 |

**响应**:
```json
{
  "hotspots": [
    {
      "coin_id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "market_cap_rank": 1,
      "price_usd": 45000.0,
      "price_change_24h": 5.2,
      "volume_24h": 30000000000,
      "total_score": 85.5,
      "scores_breakdown": {
        "twitter": 22.5,
        "reddit": 18.0,
        "price": 25.5,
        "volume": 14.5,
        "news": 5.0
      },
      "timestamp": "2025-01-26T10:00:00"
    }
  ],
  "count": 1,
  "updated_at": "2025-01-26T10:00:00"
}
```

**评分算法**:

热点得分基于5个维度的加权计算（总分100分）：
- 🐦 Twitter提及量（25%权重）- 社交媒体热度
- 💬 Reddit讨论量（20%权重）- 社区活跃度
- 📈 24h价格变化（30%权重）- 市场表现
- 💰 24h交易量（15%权重）- 流动性指标
- 📰 新闻数量（10%权重）- 媒体关注度

**得分解读**:
- 80-100分: 🔥 极热（强烈关注）
- 60-79分: 🌡️ 热门（值得关注）
- 40-59分: 📊 活跃（正常水平）
- <40分: 📉 冷清（关注度低）

**示例请求**:
```bash
# 获取Top 10热点
curl "http://localhost:8000/api/v1/trending/hotspots?limit=10"

# 强制刷新
curl "http://localhost:8000/api/v1/trending/hotspots?limit=20&force_refresh=true"
```

**速率限制**: 30次/分钟

---

## 健康检查

### Health Check

检查API服务健康状态。

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-26T10:00:00",
  "version": "1.0.0"
}
```

**示例请求**:
```bash
curl "http://localhost:8000/health"
```

---

## SDK示例

### Python SDK

```python
import httpx
from typing import Optional

class Web3SearchClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def quick_chat(self, query: str, session_id: Optional[str] = None):
        """Quick Chat - 快速对话"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat/quick-chat",
            json={"query": query, "session_id": session_id}
        )
        response.raise_for_status()
        return response.json()

    async def deep_research(self, query: str, symbol: Optional[str] = None):
        """Deep Research - 深度研究"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat/deep-research",
            json={"query": query, "symbol": symbol, "session_id": None}
        )
        response.raise_for_status()
        return response.json()

    async def get_hotspots(self, limit: int = 10):
        """获取市场热点"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/trending/hotspots",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

# 使用示例
async def main():
    client = Web3SearchClient()

    # Quick Chat
    result = await client.quick_chat("What is Bitcoin?")
    print(result["content"])

    # Deep Research
    report = await client.deep_research("Bitcoin", "BTC")
    print(report["tldr"])

    # 获取热点
    hotspots = await client.get_hotspots(limit=5)
    for hotspot in hotspots["hotspots"]:
        print(f"{hotspot['symbol']}: {hotspot['total_score']}")
```

### JavaScript SDK

```javascript
class Web3SearchClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async quickChat(query, sessionId = null) {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/quick-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId })
    });
    if (!response.ok) throw new Error('Request failed');
    return await response.json();
  }

  async deepResearch(query, symbol = null) {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/deep-research`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, symbol, session_id: null })
    });
    if (!response.ok) throw new Error('Request failed');
    return await response.json();
  }

  async getHotspots(limit = 10) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/trending/hotspots?limit=${limit}`
    );
    if (!response.ok) throw new Error('Request failed');
    return await response.json();
  }
}

// 使用示例
const client = new Web3SearchClient();

// Quick Chat
const result = await client.quickChat('What is Bitcoin?');
console.log(result.content);

// Deep Research
const report = await client.deepResearch('Bitcoin', 'BTC');
console.log(report.tldr);

// 获取热点
const hotspots = await client.getHotspots(5);
hotspots.hotspots.forEach(h => {
  console.log(`${h.symbol}: ${h.total_score}`);
});
```

---

## 更新日志

### v1.0.0 (2025-01-26)

**新增功能**:
- ✅ Quick Chat API - 快速对话
- ✅ Deep Research API - 深度研究报告
- ✅ 报告管理API - 列表、详情、分享
- ✅ 搜索API - 自动补全
- ✅ 热点API - 市场热点识别

**技术特性**:
- ✅ FastAPI框架
- ✅ OpenAPI/Swagger文档
- ✅ 速率限制（基于IP）
- ✅ 错误处理和降级策略
- ✅ Sentry错误追踪
- ✅ Redis缓存加速

---

## 报告模板示例

### 完整Markdown报告示例

以下是一个包含表格和图表的完整Deep Research报告示例：

```markdown
# BTC 深度研究报告

**生成时间**: 2025-01-28T10:00:00Z
**用户查询**: 分析比特币的技术面和市场情绪
**分析师**: Web3 Search AI

---

## 📌 TL;DR

比特币当前处于牛市阶段，技术面显示强劲的上涨动能，RSI指标显示超买但尚未到达极端区域。链上数据表明鲸鱼地址持续增持，市场情绪乐观。建议分批买入，目标价位$48,000，止损设在$42,000以下。

---

## ⏰ 时间窗分析

**短期（1-2周）**: 预计在$44,000-$46,000区间震荡整理
**中期（1-2月）**: 突破$46,000后有望测试$50,000关口

### 价格走势图

![价格走势](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...)

---

## 😊 情绪分析

社交媒体情绪指数：78/100（乐观）
- Twitter提及量：+45% (24h)
- Reddit讨论热度：+32% (7d)
- 恐慌与贪婪指数：65（贪婪）

### 社交媒体提及分布

![情绪分布](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...)

---

## 📈 技术分析

当前价格处于上升通道中轨，MACD金叉确认，成交量温和放大。

### 关键价位

| 类型 | 价格 | 说明 |
|------|------|------|
| 强支撑 | $42,500 | 10日均线支撑 |
| 弱支撑 | $43,800 | 日内低点 |
| 当前价 | $45,200 | 市场价 |
| 弱阻力 | $46,000 | 前高压力 |
| 强阻力 | $48,000 | 心理关口 |

**技术指标**:
- RSI(14): 67.5（偏多但未超买）
- MACD: 金叉确认
- 布林带: 中轨上方运行

---

## ⛓️ 链上分析

- 活跃地址数：+18% (7d)
- 交易所净流出：-12,500 BTC (7d)
- 鲸鱼地址(>1000 BTC): +3个新增

**解读**: 链上数据显示资金从交易所流向个人钱包，鲸鱼增持迹象明显，看涨信号。

---

## 🔍 竞品分析

### 竞品对比

| 项目 | 市值 | 涨幅(30d) | P/E比 | TVL |
|------|------|----------|--------|-----|
| BTC | $880B | +12% | N/A | N/A |
| ETH | $280B | +18% | N/A | $45B |
| SOL | $45B | +25% | N/A | $3.2B |

### 估值倍数对比

| 项目 | 市值/TVL | FDV/市值 | 日活地址 |
|------|----------|---------|---------|
| BTC | N/A | 1.00 | 850K |
| ETH | 6.2x | 1.05 | 420K |
| SOL | 14.1x | 1.30 | 1.2M |

### 估值倍数对比图

![估值对比](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...)

**对比结论**: BTC作为数字黄金，估值逻辑与其他平台代币不同。ETH和SOL的高涨幅反映了DeFi和应用生态的繁荣。

---

## 💰 代币经济学

**供应模型**: 固定总量21M BTC
**当前流通**: 19.6M BTC（93.3%）
**通胀率**: 1.8%（减半后降低）

### 代币解锁时间表

| 日期 | 事件 | 预计解锁量 | 影响 |
|------|------|-----------|------|
| 2024-04 | 第四次减半 | -50%产量 | 供应减少，利好 |
| 2028-04 | 第五次减半 | -50%产量 | 长期利好 |

**经济学评估**: BTC的固定供应和减半机制是其价值主张的核心，稀缺性驱动长期看涨。

---

## ⚠️ 风险评估

### 风险矩阵

| 风险类型 | 严重程度 | 发生概率 | 影响 | 缓解措施 |
|---------|---------|---------|------|---------|
| 监管风险 | 高 | 中 | -20% | 分散投资 |
| 技术风险 | 中 | 低 | -10% | 使用硬件钱包 |
| 市场风险 | 高 | 高 | -30% | 设置止损 |
| 流动性风险 | 低 | 低 | -5% | 使用主流交易所 |

### 风险热力图

![风险热力图](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...)

**风险总结**: 主要风险来自宏观监管政策和市场波动，建议合理控制仓位。

---

## 🎯 结论与投资建议

**投资评级**: 买入（Buy）
**目标价位**: $48,000（+6.2%）
**止损价位**: $42,000（-7.1%）
**风险收益比**: 1:2.1

**投资策略**:
1. 分三批建仓（$44.5K, $45K, $45.5K）
2. 目标$48K附近分批减仓
3. 跌破$43K止损离场
4. 适合风险偏好中等的投资者

### 催化剂日历

| 日期 | 事件 | 预期影响 |
|------|------|---------|
| 2025-02-01 | 美联储利率决议 | 中性至利好 |
| 2025-02-15 | BTC ETF资金流向数据 | 利好 |
| 2025-03-01 | 减半倒计时（1年） | 长期利好 |

---

**免责声明**: 本报告仅供参考，不构成投资建议。加密货币市场波动大，投资需谨慎。

---

## 📊 报告元数据

### 数据来源
- CoinGecko
- Etherscan
- Twitter
- Reddit
- CryptoPanic

### 使用模型
- **TL;DR**: qwen/qwen3-235b-a22b:free
- **技术分析**: deepseek/deepseek-r1-0528:free
- **情绪分析**: anthropic/claude-3.5-sonnet

**报告生成耗时**: 28.5 秒
**包含表格**: 6 个
**包含图表**: 4 个
```

---

## 联系我们

- **GitHub**: https://github.com/marovole/Web3search
- **Email**: marovole@example.com
- **Issue Tracker**: https://github.com/marovole/Web3search/issues

---

**文档最后更新**: 2025-01-28（添加PDF导出、表格图表增强说明、报告模板示例）
