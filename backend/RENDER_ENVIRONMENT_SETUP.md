# Render 环境变量配置指南

## 🚨 重要：修复 502 错误后需要手动配置

修复 render.yaml 后，需要在 Render Dashboard 中手动设置以下环境变量。

---

## 必需的环境变量

### 1. OPENROUTER_API_KEY (必需)
**用途**: AI 功能（Quick Chat, Deep Research）
**获取方式**:
1. 访问 https://openrouter.ai/
2. 注册账号
3. 进入 API Keys 页面
4. 创建新 API Key
5. 免费额度: $5 credits

**设置值**: `sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 2. JWT_SECRET_KEY (必需)
**用途**: JWT 认证加密
**生成方式**:
```bash
# 使用以下命令生成（已为你生成）
openssl rand -base64 64
```

**设置值**:
```
3T2GYsmMZn0SDKbqsRARZk9zYJe3XFf5nMtDc4ptRiqziGW2KUj2kZ7iTM0fotq4vNX2/uJfdn5CjfUxNAUY8w==
```

---

### 3. SIGNATURE_SECRET_KEY (必需)
**用途**: API 签名验证
**生成方式**:
```bash
# 使用以下命令生成（已为你生成）
openssl rand -base64 64
```

**设置值**:
```
vhHEQ8SskegHd+GitLPBNrJGgZ6yj6hgxBNf32BC09IG7bqyWzJm5b/vwcNcMPHMhCD1GoqwKUSI42Enx9D7LQ==
```

---

### 4. DATABASE_URL (可选，Render 会自动设置)
如果使用 Render PostgreSQL，此变量会自动配置。
如果使用外部数据库，需要手动设置。

**设置值**: `postgresql://user:pass@host:port/dbname`

---

### 5. CORS_ORIGINS (已配置)
**值**: `https://web3search.vercel.app,https://www.web3search.vercel.app`

此值已在 render.yaml 中设置，无需手动配置。

---

## 可选环境变量

### 6. COINGECKO_API_KEY (可选)
**用途**: 加密货币价格数据
**获取方式**: https://www.coingecko.com/en/api

**设置值**: `CG-xxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 7. SENTRY_DSN (可选)
**用途**: 错误追踪
**获取方式**: https://sentry.io/

**设置值**: `https://xxxxxxxx.ingest.sentry.io/xxxxx`

---

### 8. 其他可选 API 密钥

- **ETHERSCAN_API_KEY**: Ethereum 区块链数据
- **TWITTER_BEARER_TOKEN**: Twitter 数据
- **REDDIT_CLIENT_ID** / **REDDIT_CLIENT_SECRET**: Reddit 数据
- **CRYPTOPANIC_API_KEY**: 加密新闻

---

## 📋 配置步骤

### 在 Render Dashboard 中设置环境变量

1. 登录 https://dashboard.render.com
2. 找到 `web3search-api` 服务
3. 点击 **Environment** 标签页
4. 点击 **Add Environment Variable**
5. 逐一添加以下变量：

| 变量名 | 值 | 备注 |
|--------|-----|------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | **必需** |
| `JWT_SECRET_KEY` | 见上方生成的密钥 | **必需** |
| `SIGNATURE_SECRET_KEY` | 见上方生成的密钥 | **必需** |
| `COINGECKO_API_KEY` | `CG-...` | 可选 |
| `SENTRY_DSN` | `https://...` | 可选 |

---

## 🔍 验证配置

### 1. 重新部署服务
- 在 Render Dashboard 中
- 找到 web3search-api
- 点击 **Manual Deploy** → **Deploy latest commit**

### 2. 查看部署日志
- 点击 **Events** 标签页
- 查看部署状态
- 确认没有错误

### 3. 测试 API
```bash
# 测试健康检查
curl https://web3search-api.onrender.com/health

# 应该返回 200 OK
{
  "status": "healthy",
  "timestamp": "..."
}
```

---

## 🚨 如果仍然遇到问题

### 1. 检查日志
```bash
curl https://web3search-api.onrender.com/docs  # 502 表示服务未启动
```

### 2. 查看 Render 日志
- Dashboard → web3search-api → **Logs**
- 查找错误信息
- 常见错误：
  - `ModuleNotFoundError` → 依赖未正确安装
  - `KeyError` → 环境变量缺失
  - `Database connection failed` → 数据库配置错误

### 3. 使用最小化配置
如果完整配置有问题，可以暂时使用 minimal_render.yaml:
1. 备份当前配置: `cp render.yaml render.yaml.backup`
2. 使用最小配置: `cp minimal_render.yaml render.yaml`
3. 重新部署
4. 确认服务能启动后再逐步添加功能

---

## 📊 预期行为

修复并配置后，API 应该：
- ✅ 健康检查: `/health` → 200 OK
- ✅ API 文档: `/docs` → Swagger UI
- ✅ Quick Chat: `/api/v1/quick-chat` → AI 响应
- ✅ Deep Research: `/api/v1/deep-research` → 深度分析
- ❌ 如果没有配置 OPENROUTER_API_KEY → 500 错误

---

**上次更新**: 2025-11-07
**问题**: 修复 502 Bad Gateway 错误
**状态**: 等待手动配置环境变量
