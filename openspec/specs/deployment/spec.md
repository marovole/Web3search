# deployment Specification

## Purpose
TBD - created by archiving change add-crypto-ai-search-platform. Update Purpose after archive.
## Requirements
### Requirement: Vercel前端部署
系统前端**SHALL**部署到Vercel平台，提供全球CDN加速和自动HTTPS。

#### Scenario: 自动部署成功
- **WHEN** Git仓库main分支有新提交（如合并PR）
- **THEN** Vercel自动触发构建流程
- **AND** 执行`npm run build`（构建React应用）
- **AND** 构建成功后自动部署到生产环境
- **AND** 部署时间< 3分钟（从提交到上线）
- **AND** 部署完成后发送Slack/Email通知

#### Scenario: 预览环境部署
- **WHEN** 创建新的Pull Request
- **THEN** Vercel自动为PR创建预览环境
- **AND** 预览URL格式：`https://web3search-pr-123.vercel.app`
- **AND** PR页面显示预览链接（可点击访问）
- **AND** 预览环境使用独立的环境变量（如测试API URL）
- **AND** PR合并或关闭后自动删除预览环境

#### Scenario: 环境变量配置
- **WHEN** Vercel部署时
- **THEN** 从Vercel Dashboard读取环境变量
- **AND** 包含以下变量：
  - `VITE_API_URL`: 后端API地址（如https://api.web3search.ai）
  - `VITE_ENVIRONMENT`: 环境标识（production/staging/development）
- **AND** 支持生产环境和预览环境使用不同配置
- **AND** 敏感变量加密存储（Vercel自动加密）

#### Scenario: 部署回滚
- **WHEN** 新部署出现严重问题（如页面白屏）
- **THEN** 在Vercel Dashboard点击"Rollback"
- **AND** 1分钟内回滚到上一个稳定版本
- **AND** 自动更新生产URL指向旧版本
- **AND** 通知开发团队回滚事件

### Requirement: Railway后端部署
系统后端**SHALL**部署到Railway平台，包含FastAPI、PostgreSQL、Redis和Celery Worker。

#### Scenario: 完整服务部署
- **WHEN** Railway项目配置完成
- **THEN** 部署以下服务：
  1. **backend**：FastAPI应用（监听8000端口）
  2. **worker**：Celery后台任务
  3. **postgres**：PostgreSQL 15数据库
  4. **redis**：Redis 7缓存服务
- **AND** 所有服务在同一私有网络（内部通信无需公网）
- **AND** 仅backend服务暴露公网访问（通过Railway提供的域名）
- **AND** 服务间通过内部DNS通信（如`postgres.railway.internal`）

#### Scenario: 环境变量自动注入
- **WHEN** Railway启动服务
- **THEN** 自动注入以下环境变量：
  - `DATABASE_URL`: PostgreSQL连接字符串（自动生成）
  - `REDIS_URL`: Redis连接字符串（自动生成）
  - `PORT`: 应用监听端口（Railway分配）
- **AND** 手动配置的变量：
  - `OPENROUTER_API_KEY`: OpenRouter API密钥
  - `COINGECKO_API_KEY`: CoinGecko API密钥
  - `TWITTER_BEARER_TOKEN`: Twitter API令牌
- **AND** 变量变更无需重新部署（自动重启服务）

#### Scenario: 数据库迁移自动执行
- **WHEN** 后端服务启动时
- **THEN** 自动执行数据库迁移脚本（使用Alembic）
- **AND** 运行`alembic upgrade head`
- **AND** 迁移成功后启动FastAPI应用
- **AND** 迁移失败时服务启动失败并记录错误日志
- **AND** 保留迁移历史记录（`alembic_version`表）

#### Scenario: Celery Worker配置
- **WHEN** worker服务启动
- **THEN** 执行命令`celery -A tasks worker --loglevel=info`
- **AND** 连接到Redis作为消息队列
- **AND** 自动发现并注册所有定时任务
- **AND** Worker数量可通过环境变量`CELERY_WORKERS`配置（默认1）
- **AND** Worker健康检查：每分钟执行测试任务

#### Scenario: 服务扩展
- **WHEN** 流量增加需要扩容
- **THEN** 在Railway Dashboard调整服务实例数
- **AND** backend服务支持水平扩展（多实例负载均衡）
- **AND** worker服务支持增加Worker数量
- **AND** PostgreSQL和Redis支持升级配置（CPU/内存/存储）
- **AND** 扩展操作无停机时间（滚动更新）

### Requirement: 健康检查与监控
系统**SHALL**提供健康检查端点和实时监控能力。

#### Scenario: 健康检查端点
- **WHEN** Railway或外部监控服务访问`GET /health`端点
- **THEN** 返回200状态码和健康状态JSON：
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00Z",
    "services": {
      "database": "connected",
      "redis": "connected",
      "celery": "running"
    },
    "version": "1.0.0"
  }
  ```
- **AND** 检查数据库连接（执行简单查询）
- **AND** 检查Redis连接（执行PING命令）
- **AND** 检查Celery状态（查询活跃Worker）
- **AND** 如任何服务不健康，返回503状态码

#### Scenario: Railway健康检查配置
- **WHEN** Railway配置健康检查
- **THEN** 设置检查路径：`/health`
- **AND** 检查间隔：30秒
- **AND** 超时时间：10秒
- **AND** 失败阈值：3次连续失败
- **AND** 失败时Railway自动重启服务

#### Scenario: 实时日志聚合
- **WHEN** 服务运行时
- **THEN** 所有日志输出到stdout/stderr
- **AND** Railway自动收集并聚合日志
- **AND** 在Railway Dashboard查看实时日志流
- **AND** 支持日志过滤（按服务/级别/时间）
- **AND** 保留最近7天的日志

#### Scenario: 性能监控指标
- **WHEN** 服务运行时
- **THEN** Railway自动监控以下指标：
  - CPU使用率（p50/p95/p99）
  - 内存使用量（MB）
  - 网络流量（入站/出站）
  - HTTP请求数（成功/失败）
  - 响应时间（p50/p95/p99）
- **AND** 在Railway Dashboard展示指标图表
- **AND** 当CPU > 80%或内存> 90%时发送告警

### Requirement: HTTPS与域名配置
系统**SHALL**支持自定义域名并自动配置HTTPS证书。

#### Scenario: Vercel自定义域名
- **WHEN** 在Vercel Dashboard添加自定义域名（如web3search.ai）
- **THEN** Vercel提供DNS配置指引（CNAME记录）
- **AND** 配置DNS后自动验证域名所有权
- **AND** 验证成功后自动申请Let's Encrypt证书
- **AND** 证书自动续期（过期前30天）
- **AND** 强制HTTPS重定向（HTTP请求301到HTTPS）

#### Scenario: Railway自定义域名
- **WHEN** 在Railway Dashboard为backend服务添加自定义域名（如api.web3search.ai）
- **THEN** Railway提供DNS配置（A或CNAME记录）
- **AND** 配置DNS后自动验证
- **AND** 自动申请并配置SSL证书
- **AND** 支持WebSocket升级（wss://）

#### Scenario: CORS配置更新
- **WHEN** 配置自定义域名后
- **THEN** 在FastAPI中更新allow_origins配置：
  ```python
  allow_origins=[
      "https://web3search.ai",
      "https://www.web3search.ai",
      "https://*.vercel.app",  # 预览环境
      "http://localhost:3000"  # 本地开发
  ]
  ```
- **AND** 支持通配符域名（预览环境）
- **AND** 验证Origin头防止CSRF攻击

### Requirement: 备份与灾难恢复
系统**SHALL**定期备份数据并支持快速恢复。

#### Scenario: 数据库自动备份
- **WHEN** Railway PostgreSQL服务运行
- **THEN** 每日凌晨2点自动创建数据库快照
- **AND** 保留最近7天的备份
- **AND** 备份存储在Railway的持久化存储中
- **AND** 支持手动触发备份（Railway Dashboard）

#### Scenario: 数据库恢复
- **WHEN** 需要恢复数据库（如误删除数据）
- **THEN** 在Railway Dashboard选择历史备份
- **AND** 点击"Restore"执行恢复
- **AND** 恢复过程中服务暂时不可用（5-10分钟）
- **AND** 恢复完成后自动重启相关服务

#### Scenario: 配置备份
- **WHEN** 环境变量或配置变更
- **THEN** 导出当前配置（Railway CLI）：
  ```bash
  railway env export > .env.backup
  ```
- **AND** 提交配置备份到Git（加密敏感信息）
- **AND** 定期验证配置备份可用性

#### Scenario: 灾难恢复演练
- **WHEN** 每月进行一次灾难恢复演练
- **THEN** 模拟数据库崩溃场景
- **AND** 从备份恢复数据
- **AND** 验证服务正常运行
- **AND** 测试数据完整性
- **AND** 记录恢复时间（目标< 15分钟）
- **AND** 优化恢复流程

### Requirement: CI/CD自动化
系统**SHALL**实施持续集成和持续部署流程。

#### Scenario: GitHub Actions自动测试
- **WHEN** 创建Pull Request
- **THEN** 自动触发GitHub Actions工作流
- **AND** 运行单元测试（pytest）
- **AND** 运行代码质量检查（pylint/black）
- **AND** 运行前端测试（Jest）
- **AND** 所有检查通过后PR才能合并
- **AND** 测试失败时在PR页面显示错误详情

#### Scenario: 自动部署流程
- **WHEN** PR合并到main分支
- **THEN** 自动触发以下流程：
  1. GitHub Actions运行完整测试套件
  2. 测试通过后Vercel开始前端部署
  3. Railway自动拉取最新代码
  4. Railway重新构建Docker镜像
  5. Railway滚动更新服务（零停机）
- **AND** 整个流程10分钟内完成
- **AND** 每个步骤状态在Slack频道实时通知

#### Scenario: 部署版本标记
- **WHEN** 部署成功后
- **THEN** 自动创建Git tag（如v1.2.3）
- **AND** tag推送到远程仓库
- **AND** 创建GitHub Release（包含变更日志）
- **AND** 在Railway中标记部署版本
- **AND** 前端在页面footer显示当前版本号

