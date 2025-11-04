# 📋 如何获取 Cloudflare Account ID

## 方法1：从 Cloudflare Dashboard 主页获取（最简单）

### 步骤：

1. **登录 Cloudflare Dashboard**
   - 访问：https://dash.cloudflare.com/
   - 使用您的账号登录

2. **查看右侧边栏**
   - 登录后，在**任何页面**的右侧都会显示 Account ID
   - 通常在页面右下角的位置

3. **复制 Account ID**
   - 格式类似：`1234567890abcdef1234567890abcdef`（32位十六进制字符串）
   - 点击旁边的复制图标即可复制

### 视觉位置：

```
┌────────────────────────────────────────────────────────┐
│  Cloudflare Dashboard                                   │
├────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐            ┌──────────────────┐  │
│  │                 │            │  Account Info     │  │
│  │  主要内容区域    │            │                  │  │
│  │                 │            │  Account ID:     │  │
│  │                 │            │  xxxxxxxxxx      │  │
│  │                 │            │  [Copy Icon]     │  │
│  │                 │            │                  │  │
│  └─────────────────┘            └──────────────────┘  │
│                                         ↑               │
│                                    在这里！             │
└────────────────────────────────────────────────────────┘
```

---

## 方法2：从 Pages 项目页面获取

### 步骤：

1. **导航到 Pages**
   - Cloudflare Dashboard → 左侧菜单 → **Workers & Pages**

2. **创建或打开项目**
   - 点击 **Create application** 或打开现有项目

3. **查看项目设置**
   - 在项目设置页面，URL中包含Account ID
   - URL格式：`https://dash.cloudflare.com/<ACCOUNT_ID>/pages/...`

---

## 方法3：从 Workers 页面获取

### 步骤：

1. **导航到 Workers**
   - Cloudflare Dashboard → 左侧菜单 → **Workers & Pages**

2. **查看 Overview**
   - 在右侧边栏会显示 Account ID

---

## 方法4：从 URL 中提取

当您在 Cloudflare Dashboard 的任何页面时：

### 查看浏览器地址栏：

```
https://dash.cloudflare.com/<YOUR_ACCOUNT_ID>/...
                            ↑
                    这就是您的 Account ID
```

例如：
```
https://dash.cloudflare.com/1234567890abcdef1234567890abcdef/pages/new
                            └──────────── Account ID ────────────┘
```

---

## 方法5：使用 Wrangler CLI 获取（适合开发者）

### 如果您已安装 wrangler：

```bash
# 登录 Cloudflare
wrangler login

# 查看账号信息
wrangler whoami
```

输出示例：
```
 ⛅️ wrangler 3.80.0
──────────────────

Getting User settings...
👋 You are logged in with an OAuth Token, associated with the email 'your-email@example.com'!

┌───────────────────┬──────────────────────────────────┐
│ Account Name      │ Your Account Name                │
├───────────────────┼──────────────────────────────────┤
│ Account ID        │ 1234567890abcdef1234567890abcdef │
└───────────────────┴──────────────────────────────────┘
                      ↑
              这就是您的 Account ID
```

---

## 方法6：从 API Token 页面获取

### 步骤：

1. **访问 API Tokens 页面**
   - Cloudflare Dashboard → 右上角头像 → **My Profile**
   - 左侧菜单 → **API Tokens**

2. **查看 Account Resources**
   - 在创建或编辑 API Token 时
   - 会显示可用的 Account ID 列表

---

## 📝 Account ID 格式说明

### 有效的 Account ID 格式：
- **长度**：32个字符
- **字符集**：0-9 和 a-f（十六进制）
- **示例**：`1234567890abcdef1234567890abcdef`

### 无效示例：
- ❌ 包含大写字母：`1234567890ABCDEF...`（需要小写）
- ❌ 包含特殊字符：`1234-5678-90ab-cdef...`（不应有连字符）
- ❌ 长度不对：`123456...`（必须是32位）

---

## 🔍 快速验证 Account ID

### 使用 curl 验证：

```bash
# 替换 YOUR_ACCOUNT_ID 和 YOUR_API_TOKEN
curl -X GET "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json"
```

如果返回账号信息，说明 Account ID 正确！

---

## 🆘 找不到 Account ID？

### 常见问题：

#### 问题1：没有看到右侧边栏
**解决**：
- 尝试刷新页面
- 切换到不同的页面（如 Overview 或 Workers）
- 使用方法4：从URL中提取

#### 问题2：有多个账号
**解决**：
- 在 Dashboard 顶部可以切换账号
- 每个账号都有唯一的 Account ID
- 确保选择了正确的账号

#### 问题3：刚注册的新账号
**解决**：
- 新账号也会立即分配 Account ID
- 尝试访问：https://dash.cloudflare.com/
- 登录后立即在右侧边栏查看

---

## 📸 实际截图位置参考

### Dashboard 主页：

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 Search               👤 Profile     🔔 Notifications   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Overview                              ┌───────────────┐ │
│                                           │ Account Info  │ │
│  • Websites                               │               │ │
│  • Workers & Pages                        │ Account ID:   │ │
│  • R2                                     │ xxxxxx...     │ │
│  • Analytics                              │ 📋 Copy       │ │
│                                           │               │ │
│                                           └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 配置到 GitHub Secrets

获取到 Account ID 后：

### 步骤：

1. **打开 GitHub 仓库**
   - 访问：https://github.com/marovole/Web3search

2. **进入设置**
   - 点击 **Settings** 标签页

3. **添加 Secret**
   - 左侧菜单 → **Secrets and variables** → **Actions**
   - 点击 **New repository secret**

4. **填写信息**
   ```
   Name: CLOUDFLARE_ACCOUNT_ID
   Secret: [粘贴您的 Account ID]
   ```

5. **保存**
   - 点击 **Add secret**

---

## ✅ 验证配置

配置完成后，可以通过以下方式验证：

### 查看 GitHub Actions：

1. 推送代码到 `main` 分支（修改前端任意文件）
2. 访问 GitHub → **Actions** 标签
3. 查看 **Deploy to Cloudflare Pages** 工作流
4. 如果 Account ID 正确，部署会成功

### 本地验证（使用 wrangler）：

```bash
cd workers

# 配置环境变量
export CLOUDFLARE_ACCOUNT_ID="your-account-id"

# 测试部署（不会实际部署）
wrangler deploy --dry-run
```

---

## 📚 相关文档

- [Cloudflare Account ID 官方文档](https://developers.cloudflare.com/fundamentals/get-started/basic-tasks/find-account-and-zone-ids/)
- [Cloudflare API 文档](https://developers.cloudflare.com/api/)
- [GitHub Actions Secrets 文档](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## 💡 小贴士

1. **Account ID 是公开信息**
   - 不是敏感数据，可以安全地存储在 GitHub Actions
   - API Token 才是需要保密的

2. **一个账号一个 ID**
   - 每个 Cloudflare 账号只有一个 Account ID
   - 即使有多个域名或项目，Account ID 也是相同的

3. **保存备份**
   - 建议将 Account ID 保存到本地笔记中
   - 方便后续配置其他项目使用

---

**帮助更新**：2025-11-04  
**适用版本**：Cloudflare Dashboard 2024-2025
