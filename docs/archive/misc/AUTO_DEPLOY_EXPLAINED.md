# GitHub + Render Auto-Deploy 完整指南

**为什么选择这个方案？** 这是最简单、最可靠的完全自动化部署方案。

---

## 📊 架构说明

```
GitHub Repository (main branch)
         ↓
    你的代码推送
         ↓
Render Webhook (自动触发)
         ↓
Render 构建和部署
         ↓
自动验证 (健康检查)
         ↓
部署完成/失败通知
```

---

## 🎯 工作流程详解

### 第 1 次部署（首次手动设置）

**步骤概述** (总共 50 分钟):

1. **准备（5 分钟）**
   - 获取 Render.com 账户
   - 获取 OpenRouter API Key
   - 授权 GitHub 连接

2. **创建 Blueprint（10 分钟）**
   - 在 Render Dashboard 点击 "New" → "Blueprint"
   - 连接 Web3search GitHub 仓库
   - Render 自动检测 `render.yaml`
   - 点击 "Create Resource"

3. **配置环境变量（5 分钟）**
   - 设置 `OPENROUTER_API_KEY`
   - 设置 `SENTRY_DSN`（可选）
   - 设置 `CORS_ORIGINS`（可选）

4. **监控首次部署（15 分钟）**
   - 等待 Docker 构建完成
   - 等待数据库初始化
   - 等待服务启动

5. **验证首次部署（15 分钟）**
   - 健康检查
   - API 文档
   - Quick Chat 测试
   - PDF 导出测试（最关键）

6. **启用 Auto-Deploy（5 分钟）**
   - Blueprint 设置中启用 Auto-Deploy
   - 选择 main 分支
   - 保存设置

---

### 第 2 次及以后部署（完全自动化）

**每次部署流程**（无需人工干预）:

```
1. 本地开发和修改
   └─ 编辑代码、修复 bug、添加功能
      ↓

2. 提交代码
   └─ git add .
   └─ git commit -m "your message"
      ↓

3. 推送到 GitHub
   └─ git push origin main
      ↓
      [自动化开始 ⬇️]
      ↓

4. GitHub 向 Render 发送 Webhook
   └─ Render 检测到新推送
   └─ 自动触发部署流程
      ↓

5. Render 构建新的 Docker 镜像
   └─ 安装所有依赖
   └─ 编译 Python 包
   └─ 构建完成（通常 5-10 分钟）
      ↓

6. Render 部署新服务
   └─ 停止旧服务
   └─ 启动新服务
   └─ 检查健康状态
      ↓

7. Render 自动验证
   └─ 运行健康检查
   └─ 确认服务响应正常
   └─ 部署成功 ✅
      ↓

8. 自动通知
   └─ 邮件通知（可选）
   └─ Slack 通知（可选）
   └─ 部署链接和版本号
```

**总耗时**：5-15 分钟（无需你的操作）

---

## ✅ 启用 Auto-Deploy 的具体步骤

### 前置条件

首次部署必须已成功：
- [ ] 所有 3 个资源都处于 "Live" 状态
- [ ] 健康检查返回 200 OK
- [ ] 环境变量已配置

### 启用步骤

#### 方式 1: 通过 Render Dashboard UI（推荐）

```
1. 登录 https://dashboard.render.com

2. 找到你的 Blueprint
   └─ 左侧导航栏 → 你的服务列表
   └─ 点击 Blueprint 名称（web3search-staging）

3. 进入 Blueprint 设置
   └─ 点击 "Settings" 或 "Configuration"
   └─ 查找 "Auto-Deploy" 或 "Deployment" 选项

4. 启用自动部署
   选项 A（推荐）：
   - 找到 "Auto-deploy new commits"
   - 选择分支：main
   - 切换开关：开启 ✅

   选项 B（如果选项 A 不可用）：
   - 找到 "Connected Repository"
   - 点击 "Enable Auto-Deploy"
   - 选择分支：main
   - 保存设置

5. 保存并确认
   - 点击 "Save"
   - 页面刷新后应看到确认消息
   - Auto-Deploy 状态应显示为 "Enabled"
```

#### 方式 2: 通过 Render CLI

如果你已安装 Render CLI：

```bash
# 登录 Render
render login

# 列出所有 Blueprint
render blueprint list

# 启用特定 Blueprint 的自动部署
render blueprint auto-deploy --enable --branch main
```

---

## 🔄 自动部署工作原理

### GitHub Webhook 机制

```
当你执行 git push 时：

GitHub 发送 Webhook
    └─ HTTP POST 请求
    └─ URL: Render 提供的 Webhook 端点
    └─ 包含: 仓库信息、commit 哈希、分支名等
       ↓
Render 接收 Webhook
    └─ 验证请求来自 GitHub
    └─ 检查推送的分支是否是 main
    └─ 如果匹配，触发部署流程
       ↓
自动构建和部署
    └─ 克隆最新代码
    └─ 运行构建命令（Dockerfile）
    └─ 启动新服务
    └─ 运行健康检查
       ↓
完成和通知
    └─ 部署成功或失败
    └─ 发送通知
    └─ 更新部署状态
```

### 关键点

1. **完全自动化** - Webhook 自动触发，无需手动操作
2. **快速反馈** - 通常在 5-15 分钟内完成
3. **原子操作** - 要么完全成功，要么完全回滚
4. **零停机** - 使用 Blue-Green 部署或其他方式确保无停机

---

## 📝 典型的开发流程（使用 Auto-Deploy）

### 修复 Bug 示例

```bash
# 1. 创建新分支（可选）
git checkout -b fix/pdf-chinese-font

# 2. 修改代码
# 编辑 app/services/report/pdf_exporter.py
nano app/services/report/pdf_exporter.py

# 3. 本地测试（可选）
python -m pytest tests/

# 4. 提交代码
git add .
git commit -m "fix: 修复 PDF 中文字体显示问题"

# 5. 推送到 GitHub
git push origin fix/pdf-chinese-font

# 6. 创建 Pull Request（可选）
# 在 GitHub 上打开 PR

# 7. 合并到 main（PR 通过审核后）
git checkout main
git merge fix/pdf-chinese-font
git push origin main

# ⬇️ 以下完全自动 ⬇️

# [Render 自动检测推送]
# [Render 自动构建 Docker 镜像（5-10 分钟）]
# [Render 自动部署到 Staging]
# [Render 自动运行健康检查]
# [Render 自动发送通知]

# 8. 验证部署完成
# 访问 https://web3search-api.onrender.com/health
# 应返回 200 OK

# 9. 享受自动部署！ 🎉
```

---

## 🚀 部署后的实际体验

### 场景：发现一个 Bug 并修复

**传统手动部署流程**:
```
发现 bug (1分钟)
  ↓
修改代码 (5分钟)
  ↓
手动上传到 Render (5分钟)
  ↓
手动验证 (10分钟)
  ↓
总耗时: ~21分钟，需要人工干预
```

**使用 Auto-Deploy 流程**:
```
发现 bug (1分钟)
  ↓
修改代码 (5分钟)
  ↓
git push (1分钟)
  ↓
[等待自动部署 5-15分钟 - 无需人工干预]
  ↓
验证部署完成 (2分钟)
  ↓
总耗时: ~9-15分钟，完全自动化
```

**节省时间**: 6-12 分钟/次（积少成多！）

---

## ⚠️ 注意事项和最佳实践

### 1. 不要直接推送到 main（生产环保）

**不推荐**:
```bash
# ❌ 直接推送到 main，自动部署到生产
git push origin main
```

**推荐**:
```bash
# ✅ 创建特性分支
git checkout -b feature/new-feature

# ✅ 推送特性分支
git push origin feature/new-feature

# ✅ 创建 PR，进行代码审核
# 在 GitHub 上打开 PR

# ✅ PR 通过审核后才合并到 main
git checkout main
git merge feature/new-feature
git push origin main

# [自动部署触发]
```

### 2. 配置保护分支规则（可选但推荐）

在 GitHub 仓库设置中：
```
Settings → Branches → Branch protection rules

创建规则：
├─ Branch name pattern: main
├─ Require pull request reviews: ✅ (2 个审核者)
├─ Require status checks: ✅ (tests must pass)
├─ Require branches to be up to date: ✅
└─ Include administrators: ✅
```

这样可以防止意外直接推送到 main。

### 3. 监控部署状态

Render Dashboard：
- 访问 https://dashboard.render.com/
- 查看 "Deployments" 标签
- 每次推送的部署历史都会记录
- 点击每个部署可查看详细日志

### 4. 失败时自动回滚

如果新部署失败：
```
新部署失败
  ↓
Render 检测到健康检查失败
  ↓
自动回滚到上一个成功的版本
  ↓
服务恢复正常
  ↓
发送失败通知和日志
```

你可以：
1. 查看日志找出失败原因
2. 本地修复
3. 再次 git push
4. 自动重新部署

### 5. 环境变量更新需要手动操作

Auto-Deploy 只会自动部署代码变更。

环境变量变更需要手动操作：
```
1. 登录 Render Dashboard
2. 进入服务设置
3. 找到 "Environment Variables"
4. 修改或添加变量
5. 保存（服务会自动重启）
```

---

## 📊 对比：手动 vs Auto-Deploy

| 方面 | 手动部署 | Auto-Deploy |
|------|---------|------------|
| 每次部署耗时 | 15-30 分钟 | 0 分钟（自动） |
| 人工干预 | 每次都需要 | 首次配置后无需 |
| 部署频率限制 | 低（需要时间）| 无限制 |
| 错误风险 | 高（手动操作） | 低（自动化） |
| 回滚时间 | 15-30 分钟 | 1-2 分钟（自动） |
| 适合场景 | 大型变更、生产关键部署 | 日常开发、快速迭代 |
| 生产推荐 | 配合 PR 审核 | ✅ 推荐（最安全） |

---

## 🎯 总结

### 首次部署（一次性成本）
- **耗时**: 50 分钟
- **频率**: 只需一次
- **结果**: 完整自动化部署系统搭建完成

### 后续部署（永久收益）
- **耗时**: 0 分钟（自动）
- **频率**: 无限次
- **结果**: 代码推送 = 自动部署

### ROI 计算
如果平均每周部署 5 次：
- 手动方式：5 × 20 分钟 = 100 分钟/周 = 400 分钟/月
- Auto-Deploy：首次 50 分钟 + 0 分钟/周 = 50 分钟/月
- **节省**: 350 分钟/月 = ~6 小时/月 🎉

---

## 🔧 高级配置（可选）

### Slack 通知集成

当部署成功/失败时自动通知 Slack：

```
1. 在 Render Dashboard 进入 "Notifications"
2. 添加 Slack Webhook
3. 选择 "Deploy succeeded" 和 "Deploy failed"
4. 保存配置

之后每次部署都会自动发送 Slack 消息
```

### 多环境部署

如果你想要 staging + production：

```
配置两个 Blueprint：
├─ web3search-staging (main 分支 → 自动部署)
└─ web3search-production (release 分支 → 手动审核后部署)

工作流：
main (开发) → PR → 代码审核 → 合并 → 自动部署到 staging
    ↓ (验证通过后)
release (发布) → 手动合并 → 自动部署到 production
```

---

**最后更新**: 2025-01-28
**建议**: 立即启用 Auto-Deploy！这将是改进开发流程的最佳决策之一。
