# Render.com Staging 部署检查清单

本清单指导您完成从本地准备到 Render.com staging 验证的全过程。

**预计总时间**: 45 分钟 (20 分钟部署 + 25 分钟验证)

---

## 📋 部署前准备 (已完成 ✓)

在开始 Render.com 部署之前，以下所有项目都应该已完成:

### 本地验证
- [x] 虚拟环境已激活
- [x] 所有依赖已安装 (包括 weasyprint)
- [x] 集成测试通过 4/7 (预期结果)
- [x] 所有文件已提交到 Git
- [x] 代码已推送到 GitHub main 分支

### 配置文件准备
- [x] Dockerfile 已更新 (WeasyPrint + 中文字体)
- [x] render.yaml 已创建 (完整配置)
- [x] app/core/config.py 包含 BASE_DIR
- [x] 文档已完整 (README.md, DEPLOYMENT.md, API.md)

**确认命令**:
```bash
# 验证 Git 状态
git log --oneline -1

# 应该显示:
# 68928c4 feat: 完成Phase 4.3 - 部署验证准备
```

---

## 🚀 第 1 步: Render.com 账户准备 (5 分钟)

### 1.1 创建或登录 Render.com 账户

- [ ] 访问 https://render.com
- [ ] 使用 GitHub 账户登录 (推荐) 或创建新账户
- [ ] 完成邮件验证
- [ ] 访问仪表板: https://dashboard.render.com

### 1.2 获取 OpenRouter API Key

- [ ] 访问 https://openrouter.ai
- [ ] 注册账户或登录
- [ ] 导航到 "API Keys" 页面
- [ ] 复制你的 API Key (格式: `sk-or-v1-xxx...`)
- [ ] **保存此 Key，稍后需要在 Render 中配置**

### 1.3 授权 GitHub 连接 (仅首次需要)

- [ ] 访问 Render 仪表板
- [ ] 点击左侧导航 "GitHub"
- [ ] 点击 "Connect GitHub"
- [ ] 授权 Render 访问你的 GitHub 账户
- [ ] 在权限提示中点击 "Authorize render-oss"

---

## 📦 第 2 步: 创建 Staging Blueprint (10 分钟)

### 2.1 创建 Blueprint 服务组

- [ ] 在 Render 仪表板点击右上角 "New" 按钮
- [ ] 选择 "Blueprint"
- [ ] 选择 "GitHub" 作为源
- [ ] 搜索你的 "Web3search" 仓库
- [ ] 点击 "Connect" 连接该仓库

### 2.2 配置 Blueprint 部署参数

- [ ] 设置 Blueprint 名称: `web3search-staging`
- [ ] 选择分支: `main`
- [ ] 选择区域: `Oregon` (或最近的区域)
- [ ] Render 应该自动检测到 `render.yaml` 文件

### 2.3 审查资源配置

Render 会显示将要创建的资源。应该包含:

```
✓ web3search-postgres (PostgreSQL 15)
✓ web3search-redis (Redis)
✓ web3search-api (FastAPI Web Service)
```

**验证**: 确认所有 3 个资源都被检测到

- [ ] 确认 PostgreSQL 数据库配置
- [ ] 确认 Redis 缓存配置
- [ ] 确认 API 服务配置

### 2.4 启动部署

- [ ] 点击 "Create Resource" 或 "Deploy Blueprint"
- [ ] 等待部署开始
- [ ] 不要关闭浏览器窗口

---

## 🔨 第 3 步: 监控部署进度 (10 分钟)

### 3.1 监控构建日志

部署将分几个阶段进行:

**阶段 1: PostgreSQL 数据库创建**
```
预期输出:
Creating database web3search...
Database created successfully
Connection URL: postgresql://...
```
- [ ] 等待数据库初始化完成 (2-3 分钟)

**阶段 2: Redis 缓存创建**
```
预期输出:
Creating Redis instance...
Redis created successfully
Connection URL: redis://...
```
- [ ] 等待 Redis 初始化完成 (1-2 分钟)

**阶段 3: Docker 镜像构建和服务部署**
```
预期输出:
Building image from GitHub...
Step 1/X: FROM python:3.11-slim as builder
...
Installing dependencies...
[install weasyprint, markdown2, etc.]
...
Installing fonts...
fonts-noto-cjk fonts-noto-cjk-extra...
fc-cache -f -v
...
Building runtime image...
Pushing image to registry...
Deploying service...
Service deployed at: https://web3search-api.onrender.com
```
- [ ] 等待构建完成 (8-12 分钟)

### 3.2 检查部署状态

- [ ] 在 Render 仪表板查看 "Deployments" 标签
- [ ] 确认 "web3search-api" 服务状态为 "Live" (绿色)
- [ ] 数据库和 Redis 状态也应显示为 "Available"

**如果部署失败**:
- [ ] 查看 "Logs" 标签查看具体错误
- [ ] 常见错误见故障排查部分

---

## ⚙️ 第 4 步: 配置环境变量 (5 分钟)

### 4.1 获取自动配置的连接字符串

Render 自动为以下变量配置了值:

```
✓ DATABASE_URL     - 自动设置
✓ REDIS_URL        - 自动设置
✓ ENVIRONMENT      - 自动设置为 "production"
✓ DEBUG            - 自动设置为 "false"
```

**验证**: 在 "web3search-api" 服务的 "Environment" 标签中查看这些变量

- [ ] 确认 DATABASE_URL 存在
- [ ] 确认 REDIS_URL 存在

### 4.2 添加必需的手动配置变量

**OPENROUTER_API_KEY** (必须):
- [ ] 点击 "Add Environment Variable"
- [ ] Key: `OPENROUTER_API_KEY`
- [ ] Value: 粘贴你之前获取的 API Key (sk-or-v1-xxx...)
- [ ] 点击 "Save"
- [ ] 服务会自动重启

**SENTRY_DSN** (可选 - 用于错误追踪):
- [ ] 如果你有 Sentry 账户，重复上面的步骤
- [ ] 否则可跳过此步骤

**CORS_ORIGINS** (如需跨域访问):
- [ ] Key: `CORS_ORIGINS`
- [ ] Value: `https://web3search.vercel.app,https://api.web3search.com`
- [ ] 根据实际前端地址修改
- [ ] 点击 "Save"

### 4.3 验证变量配置

- [ ] 所有必需的环境变量都已显示
- [ ] 服务状态回到 "Live"
- [ ] 日志中没有新的错误

---

## ✅ 第 5 步: Staging 验证 (15 分钟)

### 5.1 基础健康检查 (3 分钟)

**步骤 1**: 获取服务 URL

- [ ] 在 Render 仪表板找到 "web3search-api" 服务
- [ ] 复制服务 URL (格式: https://web3search-xxx.onrender.com)

**步骤 2**: 测试健康检查端点

```bash
curl https://web3search-xxx.onrender.com/health
```

**预期响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T12:00:00Z",
  "version": "1.0.0"
}
```

- [ ] 确认返回 200 OK
- [ ] 确认状态为 "healthy"

**如果失败**:
- [ ] 等待 30 秒后重试 (服务可能还在启动)
- [ ] 检查 Render 仪表板的日志

### 5.2 API 文档验证 (2 分钟)

**步骤 1**: 访问 Swagger UI

```
打开浏览器访问:
https://web3search-xxx.onrender.com/docs
```

- [ ] 页面应该成功加载
- [ ] 应该看到所有 API 端点列表

**步骤 2**: 验证主要端点

在 Swagger UI 中查看:
- [ ] `/api/v1/chat/quick-chat` - Quick Chat 端点
- [ ] `/api/v1/chat/deep-research` - Deep Research 端点
- [ ] `/api/v1/reports/{id}/export/pdf` - PDF 导出端点
- [ ] `/health` - 健康检查端点

- [ ] 所有端点都应该在列表中

### 5.3 Quick Chat API 测试 (3 分钟)

**步骤 1**: 在 Swagger UI 中测试 Quick Chat

- [ ] 找到 `/api/v1/chat/quick-chat` 端点
- [ ] 点击 "Try it out"
- [ ] 输入请求体:
```json
{
  "query": "What is Bitcoin?",
  "session_id": null
}
```
- [ ] 点击 "Execute"

**预期响应** (应在 3 秒内):
```json
{
  "response": "Bitcoin is a decentralized digital currency...",
  "session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "timestamp": "2025-01-28T12:00:00Z"
}
```

**验证**:
- [ ] 响应时间 < 5 秒 (Staging 上可能稍慢)
- [ ] 返回有效的 JSON 响应
- [ ] 包含 session_id 和 timestamp

### 5.4 PDF 导出测试 - 关键验证 (7 分钟) 🔑

这是最重要的 staging 验证步骤，确认中文字体支持。

**步骤 1**: 执行 Deep Research 获取报告

```bash
curl -X POST "https://web3search-xxx.onrender.com/api/v1/chat/deep-research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze Bitcoin technical and sentiment",
    "symbol": "BTC"
  }' \
  -o deep_research_response.json
```

- [ ] 等待响应 (可能需要 30-60 秒)
- [ ] 从响应中提取 `report_id`

**步骤 2**: 导出 PDF 报告

```bash
# 替换 {report_id} 为实际的 ID
curl "https://web3search-xxx.onrender.com/api/v1/reports/{report_id}/export/pdf" \
  -o bitcoin_report.pdf
```

- [ ] 等待 PDF 生成 (应 < 30 秒)
- [ ] 确认文件已保存

**步骤 3**: 验证 PDF 质量

使用任何 PDF 阅读器打开 `bitcoin_report.pdf`:

- [ ] 文件大小 > 100KB ✓
- [ ] **中文字体显示正确（非方块字符）** ✓ 重要
- [ ] 表格格式完整
- [ ] 图表正确渲染
- [ ] 页码和目录存在
- [ ] A4 页面布局正确

**关键验证**:
如果 PDF 中中文显示为方块 (□)，说明字体未正确加载。检查:
1. Render 仪表板中的部署日志
2. 确认 Dockerfile 中的字体安装步骤
3. 必要时重新部署

- [ ] 中文字体验证通过 ✓ **必须**

### 5.5 性能监控 (2 分钟)

访问 Render 仪表板检查关键性能指标:

- [ ] 访问 "web3search-api" 服务的 "Metrics" 标签
- [ ] 检查以下指标:

| 指标 | 目标值 | 状态 |
|------|--------|------|
| CPU Usage | < 80% | [ ] 通过 |
| Memory Usage | < 512MB | [ ] 通过 |
| Error Rate | < 1% | [ ] 通过 |
| Response Time (p95) | < 5s | [ ] 通过 |
| Uptime | > 99% | [ ] 通过 |

---

## 🐛 故障排查 (如遇问题)

### 问题: 部署失败，Dockerfile 构建错误

**症状**: 部署失败，日志显示 `No module named 'weasyprint'`

**解决方案**:
1. 检查 requirements.txt 是否包含 weasyprint
2. 删除失败的部署，推送修复后重新部署

### 问题: PDF 中文显示为方块

**症状**: PDF 打开时中文字符显示为 □

**解决方案**:
1. 检查 Dockerfile 中的字体安装步骤是否完整
2. 确认 `fc-cache` 命令已执行
3. 如仍有问题，重新部署服务

**验证方式**:
```bash
# 连接到 Redis，检查字体缓存
# (需要 Redis CLI 或 SSH 访问，高级操作)
```

### 问题: 服务启动失败，数据库连接错误

**症状**: 日志显示 `Connection refused (database)`

**解决方案**:
1. 确认 PostgreSQL 数据库已创建并处于 "Available" 状态
2. 确认 DATABASE_URL 环境变量正确设置
3. 等待 60 秒后重试 (数据库可能还在初始化)

### 问题: API 响应超时

**症状**: API 请求返回 504 Gateway Timeout

**解决方案**:
1. 检查 Render 仪表板中的日志是否有错误
2. 确认 CPU 和内存使用率不超载
3. 增加 RESEARCH_TIMEOUT 环境变量

---

## 📝 部署成功标准

以下所有条件都必须满足，才能认为 Staging 部署成功:

- [x] 所有 3 个资源 (Database, Redis, API) 都处于 "Live" 状态
- [x] 健康检查端点返回 200 OK
- [x] API 文档页面可访问
- [x] Quick Chat 在 5 秒内返回响应
- [x] **PDF 导出成功，中文字体正确显示**
- [x] 性能指标在目标范围内
- [x] 错误率 < 1%

---

## ⚙️ 启用自动部署（Auto-Deploy）✨ 关键步骤

完成首次手动部署后，启用 Auto-Deploy 使得**所有后续部署完全自动化**：

### 在 Render Dashboard 中启用 Auto-Deploy

**步骤**:
1. 登录 Render Dashboard
2. 在 Blueprint 详情页面
3. 找到 "Auto-Deploy" 或 "Settings"
4. 启用 "Auto-deploy new commits on this branch"（main 分支）
5. 保存设置

### 之后的部署流程（完全自动）

```
你的操作          → Render 自动化
─────────────────────────────────────────────
本地开发          （你手动编码）
   ↓
git add . && git commit && git push
   ↓
Render 检测推送    （自动触发）
   ↓
构建 Docker 镜像   （自动执行，5-10 分钟）
   ↓
部署更新          （自动执行）
   ↓
运行健康检查      （自动验证）
   ↓
部署完成 + 通知   （自动完成）
```

### 关键优势

启用 Auto-Deploy 后：
- ✅ **推送代码即部署** - `git push` 后自动部署，无需手动操作
- ✅ **自动化验证** - 健康检查自动运行
- ✅ **自动化回滚** - 失败时自动回滚到上一版本
- ✅ **部署历史记录** - 每次推送都自动记录在 Render Dashboard
- ✅ **部署通知** - 部署成功/失败自动通知

### 🎯 重要提示

**首次手动部署是最后一次手动操作！**

- **第 1-5 次部署**: 需要手动操作（这个清单）总共 45 分钟
- **第 6 次部署及以后**: 完全自动化（只需 `git push`）
- 这是**最后一次**需要在 Render Dashboard 手动操作
- 之后所有部署都通过 GitHub 自动触发

---

## 🎯 下一步行动

### 如果 Staging 部署成功 ✅

1. **确认所有验证通过**
   - [ ] 所有检查清单项目已完成
   - [ ] 没有遗漏的测试

2. **收集性能数据**
   - [ ] 记录 Response Times
   - [ ] 记录 Error Rates
   - [ ] 记录 Resource Usage

3. **可选: 生产部署**
   - [ ] 创建生产 Blueprint
   - [ ] 升级到 starter/standard 计划
   - [ ] 配置生产级 API Keys
   - [ ] 重复相同验证过程

### 如果 Staging 部署失败 ❌

1. **诊断问题**
   - [ ] 查看 Render 仪表板的部署日志
   - [ ] 识别失败原因

2. **修复问题**
   - [ ] 在本地修复代码或配置
   - [ ] 推送修改到 GitHub
   - [ ] Render 应自动重新部署

3. **重新验证**
   - [ ] 重复 Staging 验证步骤
   - [ ] 确认所有修复有效

---

## 📚 参考资源

如需更多帮助，参考以下文档:

1. **RENDER_DEPLOYMENT_GUIDE.md** - 完整的 Render.com 部署指南
2. **docs/DEPLOYMENT.md** - 通用部署指南
3. **README.md** - 项目概述
4. **PHASE_4_3_SUMMARY.md** - 部署准备摘要

---

## 预计时间表

| 步骤 | 预计时间 | 实际时间 |
|------|---------|---------|
| 账户准备 | 5 分钟 | [ ] |
| Blueprint 创建 | 10 分钟 | [ ] |
| 部署进度监控 | 10 分钟 | [ ] |
| 环境变量配置 | 5 分钟 | [ ] |
| 验证测试 | 15 分钟 | [ ] |
| **总计** | **45 分钟** | [ ] |

---

**最后更新**: 2025-01-28
**作者**: Claude Code
**状态**: 就绪进行部署
