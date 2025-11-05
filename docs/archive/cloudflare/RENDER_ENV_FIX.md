# 🔧 Render 环境变量修复指南

## ⚠️ 问题诊断

**错误信息**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
SIGNATURE_SECRET_KEY
  Field required [type=missing, input_value={...}, input_type=dict]
```

**原因**: Render Dashboard中缺少必需的环境变量 `SIGNATURE_SECRET_KEY`

---

## ✅ 快速修复步骤（3分钟）

### 步骤1：登录Render Dashboard

访问：https://dashboard.render.com/

### 步骤2：找到web3search-api服务

在Dashboard中找到并点击 `web3search-api` 服务

### 步骤3：添加缺失的环境变量

点击左侧菜单 **Environment** → **Environment Variables**

#### 需要添加的变量：

**1. SIGNATURE_SECRET_KEY**（必需）
```
Key: SIGNATURE_SECRET_KEY
Value: [生成一个32位以上的随机字符串]
```

**生成方法**：
```bash
# 方法1：使用openssl
openssl rand -hex 32

# 方法2：使用Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# 方法3：使用在线工具
# 访问：https://www.random.org/strings/
# 生成一个64字符的随机字符串
```

**示例值**（请使用您自己生成的）：
```
a1b2c3d4e5f6789012345678901234567890abcdefghijklmnopqrstuvwxyz1234
```

**2. JWT_SECRET_KEY**（如果也缺失）
```
Key: JWT_SECRET_KEY  
Value: [生成另一个32位以上的随机字符串]
```

### 步骤4：保存并重新部署

1. 点击 **Save Changes**
2. Render会自动触发重新部署
3. 等待2-3分钟完成部署

---

## 📋 完整环境变量检查清单

确保以下所有环境变量都已配置：

### 必需的变量（Required）

- [ ] **ENVIRONMENT** = `production`
- [ ] **DEBUG** = `false`
- [ ] **LOG_LEVEL** = `INFO`
- [ ] **SIGNATURE_SECRET_KEY** = `[64位随机字符串]`
- [ ] **JWT_SECRET_KEY** = `[64位随机字符串]`
- [ ] **DATABASE_URL** = `[自动从数据库连接]`
- [ ] **REDIS_URL** = `[自动从Redis连接]`

### 可选但推荐的变量（Optional）

- [ ] **OPENROUTER_API_KEY** = `[您的OpenRouter API密钥]`
- [ ] **CORS_ORIGINS** = `https://web3search.pages.dev,https://web3search.ai`
- [ ] **ENABLE_SIGNATURE_VERIFICATION** = `true`
- [ ] **SENTRY_DSN** = `[Sentry DSN，如需错误追踪]`

---

## 🔍 验证环境变量

### 检查当前配置的变量

在Render Dashboard → Environment页面，应该看到：

```
✅ ENVIRONMENT = production
✅ DEBUG = false
✅ LOG_LEVEL = INFO
✅ SIGNATURE_SECRET_KEY = ****** (已配置)
✅ JWT_SECRET_KEY = ****** (已配置)
✅ DATABASE_URL = postgresql://... (来自数据库)
✅ REDIS_URL = redis://... (来自Redis)
```

### 部署后测试

等待部署完成后（2-3分钟），运行测试：

```bash
# 测试健康检查
curl https://web3search-api.onrender.com/health

# 预期响应：
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

---

## 🚀 生成环境变量的脚本

如果您想批量生成，可以使用以下脚本：

```bash
#!/bin/bash

echo "生成Web3 Search所需的环境变量"
echo "================================"
echo ""

echo "SIGNATURE_SECRET_KEY=$(openssl rand -hex 32)"
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
echo ""

echo "复制上述值到Render Dashboard的Environment Variables中"
```

保存为 `generate-secrets.sh`，然后运行：
```bash
chmod +x generate-secrets.sh
./generate-secrets.sh
```

---

## 📝 Render配置文件更新

`backend/render.yaml` 中已经定义了这些变量：

```yaml
envVars:
  # Security Configuration
  - key: JWT_SECRET_KEY
    sync: false  # Must be set manually in Render Dashboard
    description: "JWT Secret Key - Must be set manually"
    
  - key: SIGNATURE_SECRET_KEY
    sync: false  # Must be set manually in Render Dashboard  
    description: "API Signature Secret Key - Must be set manually"
```

**注意**: 这些变量标记为 `sync: false`，意味着：
- 不会从Git同步
- 必须在Render Dashboard手动设置
- 这是为了安全考虑

---

## ⏱️ 预期时间线

| 步骤 | 时间 |
|------|------|
| 生成密钥 | 1分钟 |
| 添加到Render | 1分钟 |
| 自动重新部署 | 2-3分钟 |
| 验证服务 | 1分钟 |
| **总计** | **5-6分钟** |

---

## 🆘 故障排查

### 问题1：仍然报错缺少变量

**解决**：
1. 确认变量名拼写正确（区分大小写）
2. 确认点击了"Save Changes"
3. 等待自动重新部署完成
4. 查看Deploy日志确认新变量已加载

### 问题2：服务启动失败

**解决**：
1. 检查Deploy日志中的具体错误
2. 确认密钥长度至少32字符
3. 确认没有特殊字符导致解析错误

### 问题3：数据库连接失败

**解决**：
1. 确认PostgreSQL实例状态为"Available"
2. 确认DATABASE_URL自动关联正确
3. 检查数据库是否需要初始化表结构

---

## ✅ 完成检查

配置完成后，确认：

- [ ] SIGNATURE_SECRET_KEY已添加
- [ ] JWT_SECRET_KEY已添加（如之前缺失）
- [ ] Render显示"Deploy Succeeded"
- [ ] 健康检查返回200
- [ ] 后端日志无错误

---

## 📞 需要帮助？

如果问题持续：
1. 查看Render Deploy日志
2. 查看Runtime日志
3. 确认所有环境变量格式正确
4. 尝试手动重新部署

---

**创建时间**: 2025-11-04  
**预计修复时间**: 5-6分钟  
**优先级**: 🔴 高（阻塞部署）
