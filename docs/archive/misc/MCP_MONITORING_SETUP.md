# Render MCP 服务器监控配置（可选）

**注意**: 这是完全可选的。Render Dashboard 网页版已经足够强大。此配置仅用于在 Claude Desktop 中快速查看部署状态。

---

## 📋 概述

Render MCP 服务器允许你在 Claude 中查看：
- ✅ 服务列表和状态
- ✅ 部署历史
- ✅ 实时日志
- ✅ 性能指标

**不支持**:
- ❌ 创建新服务（用 Dashboard 或 CLI）
- ❌ 配置环境变量（用 Dashboard）
- ❌ 触发部署（自动或用 Dashboard）

---

## 🔧 配置步骤

### 步骤 1: 获取 Render API Key

1. 登录 https://dashboard.render.com
2. 进入 **Account Settings**
3. 点击 **API Keys**
4. 点击 **Create API Key**
5. 给 API Key 命名（例如：`claude-mcp-monitoring`）
6. 选择权限：**Read-only**（只读访问）
7. 复制生成的 API Key
8. **保管好这个 Key**（不要分享或提交到 Git）

### 步骤 2: 配置 Claude Desktop MCP

编辑 Claude Desktop 配置文件：

**文件位置**:
```
macOS/Linux:
~/.claude/claude_desktop_config.json

Windows:
%APPDATA%\Claude\claude_desktop_config.json
```

**修改内容**:

```json
{
  "mcpServers": {
    "render": {
      "command": "npx",
      "args": ["-y", "@render/mcp-server"],
      "env": {
        "RENDER_API_KEY": "rnd_xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

替换 `rnd_xxxxxxxxxxxxxxxxxxxxxxxx` 为你的实际 API Key。

### 步骤 3: 重启 Claude Desktop

1. 完全关闭 Claude Desktop
2. 重新打开
3. MCP 服务器应自动加载

---

## 📊 使用示例

### 查看所有服务

**在 Claude 中提问**:
```
查看我的 Render 服务列表
```

**Claude 会返回**:
```
我找到 3 个服务：

1. web3search-postgres
   - 类型: PostgreSQL
   - 状态: Available
   - 创建时间: 2025-01-28

2. web3search-redis
   - 类型: Redis
   - 状态: Available
   - 创建时间: 2025-01-28

3. web3search-api
   - 类型: Web Service
   - 状态: Live
   - URL: https://web3search-api.onrender.com
   - 创建时间: 2025-01-28
```

### 查看最新部署

**在 Claude 中提问**:
```
查看 web3search-api 的最新部署状态
```

**Claude 会返回**:
```
最近 5 个部署：

1. 部署 ID: dep-xxx
   状态: Succeeded ✅
   时间: 2 小时前
   Commit: 68928c4 "feat: 完成 Phase 4.3"

2. 部署 ID: dep-xxx
   状态: Succeeded ✅
   时间: 5 小时前
   Commit: a3ea960 "chore: archive add-intelligent-cache-prewarming"

3. 部署 ID: dep-xxx
   状态: Failed ❌
   时间: 8 小时前
   原因: Docker build failed
```

### 查看服务日志

**在 Claude 中提问**:
```
显示 web3search-api 的最近 50 行构建日志
```

**Claude 会返回**:
```
[构建日志输出，最后 50 行]

...
Step 15/15: FROM python:3.11-slim
...
Building Docker image: Success ✅
Pushing to registry: Success ✅
Deploying service: Success ✅
Service is running: Health check passed ✅
```

### 查看实时应用日志

**在 Claude 中提问**:
```
显示 web3search-api 的最近应用日志（最后 100 行）
```

---

## 💡 实用场景

### 场景 1: 快速检查部署状态

```
你推送了代码，想知道部署进度
↓
提问: "web3search-api 现在是什么状态？"
↓
Claude 立即告诉你:
- 服务是否 Live
- 最新部署是否成功
- 如果失败，具体错误是什么
```

### 场景 2: 诊断部署失败

```
部署失败了，你想查看详细日志
↓
提问: "web3search-api 最后的构建日志是什么？"
↓
Claude 显示完整的构建日志
↓
你立即看到错误原因（比如 Python 包冲突）
↓
修复代码，重新 git push
↓
自动重新部署
```

### 场景 3: 性能问题排查

```
API 响应变慢，想查看资源使用情况
↓
提问: "web3search-api 的 CPU 和内存使用率是多少？"
↓
Claude 显示:
- CPU 使用率: 45%
- 内存使用率: 320MB / 512MB
- 响应时间: p95 = 2.3s
↓
问题可能不在资源，而在代码逻辑
```

---

## ⚡ 常用命令集锦

### 获取服务信息

```
提问: "列出所有 Render 服务"
提问: "web3search-api 的详细信息"
提问: "web3search-postgres 的连接字符串"
```

### 查看部署历史

```
提问: "web3search-api 的最近 10 个部署"
提问: "最后一次成功的部署是什么时候？"
提问: "上一次部署失败的原因是什么？"
```

### 查看日志

```
提问: "web3search-api 的构建日志"
提问: "web3search-api 的应用日志（最后 200 行）"
提问: "显示 web3search-api 今天的所有错误日志"
```

### 管理服务

```
提问: "暂停 web3search-api 服务"
提问: "恢复 web3search-api 服务"
提问: "web3search-api 的当前状态是什么？"
```

---

## 🔒 安全注意事项

### 1. API Key 安全

**✅ 安全做法**:
```json
// 在配置文件中使用 API Key
{
  "env": {
    "RENDER_API_KEY": "rnd_xxxxxxx"
  }
}
```

**❌ 不安全做法**:
```
- 不要将 API Key 提交到 GitHub
- 不要在代码中硬编码 API Key
- 不要在公开渠道分享 API Key
```

### 2. 权限最小化

创建 API Key 时：
- ✅ 选择 **Read-only** 权限
- ✅ 不需要写入权限（MCP 只用于监控）
- ✅ 定期轮换 API Key（建议 3 个月）

### 3. API Key 泄露处理

如果 API Key 被泄露：
```
1. 立即登录 Render Dashboard
2. 进入 API Keys 设置
3. 删除泄露的 Key
4. 创建新的 Key
5. 更新本地配置
```

---

## 🆘 故障排查

### 问题: "Command not found: npx"

**原因**: Node.js/npm 未安装或不在 PATH 中

**解决**:
```bash
# 安装 Node.js（使用 Homebrew）
brew install node

# 验证安装
npm --version
```

### 问题: "Invalid API Key"

**原因**: API Key 不正确或已过期

**解决**:
1. 检查 API Key 是否正确复制
2. 检查是否有多余的空格或换行符
3. 重新生成新的 API Key

### 问题: "Connection refused"

**原因**: Claude Desktop 无法连接到 MCP 服务器

**解决**:
1. 检查配置文件是否正确
2. 重启 Claude Desktop
3. 检查 npx 是否工作：`npx --version`

---

## 📝 配置文件完整示例

```json
{
  "mcpServers": {
    "render": {
      "command": "npx",
      "args": ["-y", "@render/mcp-server"],
      "env": {
        "RENDER_API_KEY": "rnd_xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    },
    "filesystem": {
      "command": "node",
      "args": ["/path/to/mcp-filesystem/index.js"],
      "disabled": false
    }
  }
}
```

---

## 🎯 使用建议

### 何时使用 MCP 监控

✅ **适合使用**:
- 快速检查部署状态（5 秒内）
- 查看部署日志诊断问题
- 监控服务健康状况
- 在 Claude 中进行问题排查

❌ **不适合使用**:
- 创建新服务（用 Dashboard 或 CLI）
- 配置环境变量（用 Dashboard）
- 大规模管理（用 Dashboard）
- 首次部署设置

### 推荐工作流

```
日常开发:
git push 代码 → Render 自动部署 → 自动部署完成

需要检查状态:
提问 Claude: "部署完成了吗？" → Claude 查询 MCP → 返回最新状态

遇到问题:
部署失败 → 提问 Claude: "显示构建日志" → Claude 显示日志 → 快速诊断

---

注意: 大部分时间你无需主动检查，自动部署会通知你结果。
只有在需要快速诊断时才使用 MCP。
```

---

## 📚 相关文档

- **AUTO_DEPLOY_EXPLAINED.md** - 自动部署工作原理
- **STAGING_DEPLOYMENT_CHECKLIST.md** - 部署检查清单
- **RENDER_DEPLOYMENT_GUIDE.md** - 完整部署指南

---

## ⚡ 总结

| 功能 | MCP | Dashboard | CLI |
|------|-----|-----------|-----|
| 查看服务状态 | ✅ | ✅ | ✅ |
| 查看日志 | ✅ | ✅ | ✅ |
| 创建服务 | ❌ | ✅ | ✅ |
| 配置变量 | ❌ | ✅ | ✅ |
| 触发部署 | ❌ | ✅ | ✅ |
| 易用性 | 🟢 (在 Claude 中) | 🟢 (可视化) | 🔴 (命令行) |

**建议**: 作为可选补充工具，主要依赖自动部署 + Dashboard。

---

**最后更新**: 2025-01-28
**状态**: 可选配置，不必须
