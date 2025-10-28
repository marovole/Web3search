# Render.com Staging 部署指南 - Phase 4.3

## 概述

本指南用于将 Web3 Search API 部署到 Render.com staging 环境。部署使用 Blueprint 自动化配置系统，通过 `render.yaml` 一键部署数据库、缓存和 API 服务。

## 前置条件

1. Render.com 账户（免费或付费）
2. GitHub 账户并已授予 Render 访问权限
3. 本地已完成 Phase 4.3 的所有变更并推送到 main 分支
4. OpenRouter API Key（用于 LLM 服务）

## 部署步骤

### 步骤 1: 连接 GitHub 仓库到 Render

1. 访问 [https://dashboard.render.com](https://dashboard.render.com)
2. 登录 Render 账户
3. 点击右上角 "New" → "Blueprint"
4. 选择 "GitHub" 并授权连接你的 GitHub 账户
5. 搜索并选择 `Web3search` 仓库

### 步骤 2: 配置 Blueprint 部署

1. Render 会自动检测 `render.yaml` 配置文件
2. 设置 Blueprint 名称：`web3search-staging`
3. 选择部署分支：`main`
4. 点击 "Create Resource" 开始部署

此时 Render 会创建以下资源：
- PostgreSQL 数据库（web3search-postgres）
- Redis 缓存（web3search-redis）
- FastAPI Web 服务（web3search-api）

### 步骤 3: 配置环境变量

部署开始后，需要在 Render 仪表板手动设置敏感环境变量：

#### 必须配置的环境变量

1. **OPENROUTER_API_KEY**
   - 访问 [OpenRouter](https://openrouter.ai) 获取 API Key
   - 在 web3search-api 服务的 Environment 标签中添加
   - 值：`sk-or-v1-xxxx...`

2. **SENTRY_DSN**（可选）
   - 如果使用 Sentry 错误追踪
   - 值：`https://xxxx@xxxx.ingest.sentry.io/xxxx`

3. **CORS_ORIGINS**（如需跨域访问）
   - 默认值：`https://web3search.vercel.app,https://api.web3search.com`
   - 根据实际前端地址修改

#### 配置步骤

1. 访问 Render 仪表板
2. 找到 "web3search-api" 服务
3. 点击 "Environment" 标签
4. 点击 "Add Environment Variable"
5. 添加上述必需的环境变量

**注意**：不要在 `render.yaml` 中放置敏感的 API Keys，使用 Render 的机密存储功能。

### 步骤 4: 监控部署进程

1. 访问 "web3search-api" 服务
2. 点击 "Logs" 标签查看实时部署日志
3. 等待构建完成（通常 5-10 分钟）

#### 预期的部署日志输出

```
Building image...
Step 1/X : FROM python:3.11-slim as builder
...
Successfully built image
Pushing image to registry...
Deploying service...
✓ Service deployed successfully
```

#### 常见部署问题

| 问题 | 症状 | 解决方案 |
|------|------|--------|
| 字体缺失 | PDF 中文字符显示为方块 | 检查 Dockerfile 中字体安装步骤是否执行 |
| WeasyPrint 缺失 | 构建失败，"No module named 'weasyprint'" | 确认 requirements.txt 包含 weasyprint |
| 数据库连接失败 | 服务启动失败，连接字符串错误 | 确认 DATABASE_URL 环境变量正确配置 |
| Redis 连接失败 | 缓存相关操作失败 | 确认 REDIS_URL 环境变量正确配置 |

### 步骤 5: 验证部署成功

部署完成后，执行以下验证步骤：

#### 5.1 健康检查

访问健康检查端点（通过 Render 提供的服务 URL）：

```bash
curl https://web3search-api.onrender.com/health
```

**预期响应**：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T12:00:00Z"
}
```

#### 5.2 API 文档

访问 Swagger UI 文档：
```
https://web3search-api.onrender.com/docs
```

应该能看到所有 API 端点的文档。

#### 5.3 快速聊天 API 测试

```bash
curl -X POST "https://web3search-api.onrender.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current price of Bitcoin?",
    "session_id": null
  }'
```

**预期响应**：3 秒内返回有效的 JSON 响应

#### 5.4 PDF 导出测试（关键验证）

首先执行深度研究生成报告：

```bash
curl -X POST "https://web3search-api.onrender.com/api/v1/chat/deep-research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze Bitcoin technical and sentiment",
    "symbol": "BTC"
  }'
```

获取返回的 `report_id`，然后导出 PDF：

```bash
curl "https://web3search-api.onrender.com/api/v1/reports/{report_id}/export/pdf" \
  -o bitcoin_report.pdf
```

**关键验证项**：
- ✓ 文件大小 > 100KB（包含表格和图表）
- ✓ PDF 可正常打开
- ✓ **中文字体正确显示**（非方块字符）
- ✓ 表格格式正确
- ✓ 图表正确渲染

### 步骤 6: 性能监控

Render 提供实时性能指标：

1. 访问 "web3search-api" 服务
2. 点击 "Metrics" 标签
3. 监控以下关键指标：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| Response Time (p95) | <3s | Quick Chat 响应时间 |
| CPU Usage | <80% | CPU 使用率 |
| Memory Usage | <512MB | 内存使用率 |
| Error Rate | <1% | 错误率 |
| Throughput | >10 req/s | 吞吐量 |

## 常见问题解决

### 问题 1: 中文字体显示为方块

**症状**：PDF 中中文显示为 □

**原因**：字体未正确加载

**解决方案**：
1. 检查 Dockerfile 中的字体安装步骤
2. 检查 PDF CSS 中的 font-family 配置
3. 重新部署服务：`git push` → 自动触发重新构建

### 问题 2: PDF 导出超时（>30 秒）

**症状**：PDF 导出请求返回 504 Gateway Timeout

**原因**：WeasyPrint 性能问题或图表生成缓慢

**解决方案**：
1. 减少图表数量或复杂度
2. 增加 PDF_TIMEOUT 环境变量
3. 考虑升级到更高的 Render 计划

### 问题 3: Redis 连接失败

**症状**：缓存操作失败，日志显示 "Connection refused"

**原因**：Redis 服务未启动或网络连接问题

**解决方案**：
1. 检查 REDIS_URL 环境变量是否正确
2. 访问 Redis 服务的 "Logs" 标签查看状态
3. 确保 Redis 服务处于 "Running" 状态
4. 必要时重启 Redis 服务

### 问题 4: 数据库迁移失败

**症状**：服务启动失败，日志显示数据库错误

**原因**：数据库架构不匹配或迁移脚本失败

**解决方案**：
1. 检查 DATABASE_URL 连接字符串
2. 手动连接数据库检查表结构
3. 运行数据库迁移脚本（如有）

## 下一步：生产部署

Staging 验证通过后，可以按照相同步骤创建生产部署：

1. 在 Render 仪表板创建新的 Blueprint
2. 将部署环境从 staging 切换到 production
3. 更新环境变量（生产级别的 API Keys）
4. 执行完整的生产验证测试
5. 配置自定义域名和 SSL 证书

## 性能对标

部署后应该达到以下性能指标：

| 操作 | 目标响应时间 | 说明 |
|------|------------|------|
| Quick Chat | <3 秒 | 90% 请求 |
| Deep Research | <60 秒 | 包括所有 9 个分析维度 |
| PDF 导出 | <30 秒 | 单个报告 |
| 数据库查询 | <100ms | 平均响应时间 |
| 缓存命中 | <50ms | Redis 缓存 |

## 监控和告警

配置 Render 的告警规则（可选）：

1. CPU 使用率 > 80% - 告警
2. 错误率 > 1% - 告警
3. 响应时间 p95 > 5s - 告警
4. 服务宕机 - 立即告警

## 回滚策略

如果部署出现问题：

1. 访问 Render 仪表板
2. 找到问题的 commit 版本
3. 点击 "Rollback" 返回上一个稳定版本
4. 或者在 GitHub 创建修复 PR，合并后自动重新部署

## 最佳实践

1. **环境变量隔离**：不同环境使用不同的 API Keys
2. **监控告警**：设置关键指标的告警规则
3. **定期备份**：定期备份 PostgreSQL 数据
4. **日志审查**：定期审查错误日志和性能日志
5. **安全扫描**：定期运行安全漏洞扫描
6. **依赖更新**：定期更新 Python 依赖包
7. **性能测试**：在 staging 环境进行充分的性能测试

---

**最后更新**: 2025-01-28
**作者**: Claude Code
**阶段**: Phase 4.3 - 部署验证
