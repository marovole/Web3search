# Deep Research 错误日志检查指南

## 问题
Deep Research 端点返回 500 错误，需要查看详细错误日志来定位问题。

## 检查步骤

### 1. 访问 Render Dashboard
- 登录: https://dashboard.render.com
- 选择服务: `web3search-api`

### 2. 查看实时日志
- 点击 "Logs" 标签
- 查看最新的错误日志

### 3. 查找关键错误信息
搜索以下关键词：
- `❌ 数据聚合失败`
- `❌ 数据格式化失败`
- `❌ Deep Research引擎调用失败`
- `完整堆栈跟踪`
- `Traceback`

### 4. 常见错误类型

#### 数据聚合失败
```
❌ 数据聚合失败 [错误类型]: 错误消息
   完整堆栈跟踪:
   ...
```
**可能原因：**
- CoinGecko API 调用失败
- Etherscan/BSCScan API 调用失败
- 网络超时
- API 密钥配置错误

#### 数据格式化失败
```
❌ 数据格式化失败 [错误类型]: 错误消息
```
**可能原因：**
- 数据格式不符合预期
- 缺少必需字段

#### LLM 调用失败
```
❌ Deep Research引擎调用失败 [错误类型]: 错误消息
```
**可能原因：**
- Claude/GPT API 调用失败
- API 密钥配置错误
- 请求超时
- 配额限制

### 5. 手动测试并查看日志

运行以下命令，然后立即查看 Render 日志：

```bash
curl -X POST https://web3search-api.onrender.com/api/v1/chat/deep-research \
  -H "Content-Type: application/json" \
  -d '{"query": "Bitcoin", "symbol": "BTC"}' \
  -v
```

在 Render Dashboard 中查看实时日志输出。

### 6. 检查环境变量

确认以下环境变量已正确配置：
- `COINGECKO_API_KEY` (可选)
- `ETHERSCAN_API_KEY`
- `BSCSCAN_API_KEY`
- `ANTHROPIC_API_KEY` (Claude)
- `OPENAI_API_KEY` (GPT)
- `DATABASE_URL` (PostgreSQL)

### 7. 检查服务资源

- 内存使用情况
- CPU 使用情况
- 磁盘空间
- 网络连接

## 报告错误

如果找到错误日志，请记录：
1. 错误类型
2. 错误消息
3. 完整堆栈跟踪
4. 发生时间
5. 请求参数（query, symbol）

将这些信息提供给开发团队进行进一步排查。

