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
系统后端**SHALL**部署到Railway平台，包含FastAPI、PostgreSQL、Redis和Celery Worker。**集成缓存预热启动流程。**

#### Scenario: 启动时缓存预加载
- **WHEN** Railway后端服务启动
- **THEN** 在uvicorn启动后执行缓存预加载
- **AND** 预加载Top 10币种数据（< 5秒）
- **AND** 预加载日志输出到Railway Logs
- **AND** 预加载失败不阻塞服务启动
- **AND** 健康检查端点(/health)包含预加载状态

#### Scenario: 健康检查包含缓存状态
- **WHEN** 访问/health端点
- **THEN** 响应包含缓存预热信息：
  ```json
  {
    "status": "healthy",
    "cache": {
      "prewarming": {
        "status": "active",
        "last_run": "2025-01-27T12:00:00Z",
        "success_rate": 0.98,
        "cached_coins": 98
      },
      "l1_cache": {
        "size": 85,
        "capacity": 100,
        "hit_rate": 0.82
      },
      "l2_cache": {
        "size": 9850,
        "capacity": 10000,
        "hit_rate": 0.78
      }
    }
  }
  ```
- **AND** 健康检查响应时间< 100ms

#### Scenario: Celery Beat预热任务配置
- **WHEN** Celery Beat启动（Railway Cron Job）
- **THEN** 配置预热任务调度：
  - `prewarm_top10_coins`: schedule=crontab(minute='*/1')  # 每分钟
  - `prewarm_top100_coins`: schedule=crontab(minute='*/5')  # 每5分钟
  - `adjust_prewarming_list`: schedule=crontab(minute=0)  # 每小时
- **AND** 任务注册到Celery Beat scheduler
- **AND** 任务执行日志输出到Railway Logs
- **AND** 任务失败触发Sentry告警

### Requirement: 前端性能优化
前端应用 SHALL 实现全面的性能优化策略，确保快速加载和流畅交互。

#### Scenario: 首屏加载优化
- **WHEN** 用户首次访问应用
- **THEN** 首屏内容在2秒内开始渲染
- **AND** 关键资源预加载和优先级排序
- **AND** 非关键资源延迟加载
- **AND** 使用CDN加速静态资源
- **AND** 实现资源压缩和缓存策略

#### Scenario: 代码分割和懒加载
- **WHEN** 用户导航到不同功能模块
- **THEN** 按路由进行代码分割
- **AND** 组件按需懒加载
- **AND** 第三方库动态导入
- **AND** 预加载下一可能访问的页面
- **AND** 优化包大小，移除未使用代码

#### Scenario: 图片和资源优化
- **WHEN** 应用显示图片或其他媒体资源
- **THEN** 使用WebP格式优化图片大小
- **AND** 实现响应式图片和懒加载
- **AND** 压缩CSS和JavaScript文件
- **AND** 使用Service Worker缓存静态资源
- **AND** 优化字体加载策略

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

### Requirement: 监控和分析集成
前端部署 SHALL 集成全面的监控和分析工具，追踪用户行为和性能指标。

#### Scenario: 性能指标监控
- **WHEN** 用户与应用交互
- **THEN** 收集Core Web Vitals指标（LCP、FID、CLS）
- **AND** 监控页面加载时间和交互响应时间
- **AND** 追踪JavaScript错误和异常
- **AND** 记录API请求成功率和响应时间
- **AND** 提供性能仪表板和告警机制

#### Scenario: 用户行为分析
- **WHEN** 用户使用应用功能
- **THEN** 追踪用户路径和功能使用率
- **AND** 分析会话持续时间和回访率
- **AND** 记录用户操作热图和点击分布
- **AND** 监控关键转化事件（如完成深度研究）
- **AND** 提供用户行为洞察报告

#### Scenario: 错误追踪和告警
- **WHEN** 应用发生错误或异常
- **THEN** 自动捕获和记录错误详情
- **AND** 提供错误堆栈和上下文信息
- **AND** 按严重程度分类和优先级排序
- **AND** 发送实时告警通知
- **AND** 支持错误趋势分析和预防

### Requirement: 安全和隐私保护
前端部署 SHALL 实施全面的安全措施，保护用户数据和隐私。

#### Scenario: 内容安全策略（CSP）
- **WHEN** 页面加载外部资源
- **THEN** 实施严格的CSP头部策略
- **AND** 限制脚本执行来源
- **AND** 防止XSS攻击和数据注入
- **AND** 提供CSP违规报告机制
- **AND** 定期审计和更新安全策略

#### Scenario: 数据传输安全
- **WHEN** 应用与后端API通信
- **THEN** 强制使用HTTPS加密传输
- **AND** 验证API响应数据完整性
- **AND** 实施请求签名和时间戳验证
- **AND** 保护敏感信息（API密钥、令牌）
- **AND** 提供数据脱敏和加密存储

#### Scenario: 用户隐私保护
- **WHEN** 收集用户数据和行为信息
- **THEN** 遵循GDPR和隐私法规要求
- **AND** 提供隐私政策和数据使用说明
- **AND** 实现用户同意管理机制
- **AND** 支持数据访问、更正和删除请求
- **AND** 最小化数据收集，实施匿名化处理

### Requirement: 部署自动化和CI/CD
前端部署 SHALL 实现自动化部署流程和持续集成/持续部署。**CI/CD流程已完成。**

#### Scenario: 自动化部署流程
- **WHEN** 代码推送到主分支
- **THEN** 自动触发构建和部署流程 ✅
- **AND** 运行自动化测试和质量检查 ✅
- **AND** 生成构建报告和性能基准 ✅
- **AND** 部署到预发布环境进行验证 ✅
- **AND** 验证通过后自动部署到生产环境 ✅

### Requirement: Multi-Environment Deployment
The system SHALL support deployment across development, staging, and production environments with proper configuration management.

#### Scenario: Environment Variable Management
- **WHEN** deploying to different environments
- **THEN** environment-specific variables shall be automatically loaded
- **AND** sensitive information shall be properly protected
- **AND** configuration validation shall prevent deployment errors

#### Scenario: Automated Frontend Deployment
- **WHEN** code is merged to main branch
- **THEN** frontend shall be automatically deployed to Vercel
- **AND** build process shall complete without errors
- **AND** deployed version shall pass all health checks

### Requirement: Frontend Production Deployment
The system SHALL provide complete frontend deployment configuration for production use.

#### Scenario: Vercel Platform Integration
- **WHEN** frontend is deployed to Vercel
- **THEN** build configuration shall be optimized for production
- **AND** custom domain shall be properly configured
- **AND** SSL certificates shall be automatically managed
- **AND** edge caching shall be configured for optimal performance

#### Scenario: API Proxy Configuration
- **WHEN** frontend makes API calls from different domains
- **THEN** Vercel shall properly proxy API requests to backend
- **AND** CORS policies shall be correctly configured
- **AND** request headers shall be securely forwarded
- **AND** response caching shall be appropriately managed

#### Scenario: Build Optimization
- **WHEN** frontend application is built for production
- **THEN** assets shall be properly minified and compressed
- **AND** code splitting shall reduce initial bundle size
- **AND** critical CSS shall be inlined for faster rendering
- **AND** static assets shall be optimized for caching

### Requirement: Monitoring and Observability
The system SHALL provide comprehensive monitoring capabilities for the frontend application in production.

#### Scenario: Error Monitoring Integration
- **WHEN** runtime errors occur in the frontend
- **THEN** errors shall be automatically captured and reported
- **AND** error context and user session information shall be collected
- **AND** development team shall be notified of critical errors
- **AND** error trends shall be tracked for analysis

#### Scenario: Performance Metrics Collection
- **WHEN** users interact with the application
- **THEN** key performance metrics shall be automatically collected
- **AND** page load times shall be monitored
- **AND** user interaction delays shall be tracked
- **AND** performance degradation shall trigger alerts

### Requirement: Security Configuration
The system SHALL implement security best practices for frontend deployment.

#### Scenario: Content Security Policy
- **WHEN** pages are loaded in the browser
- **THEN** Content Security Policy headers shall be enforced
- **AND** only approved content sources shall be allowed
- **AND** XSS attacks shall be prevented through CSP directives
- **AND** inline scripts shall be properly controlled

#### Scenario: Secure Headers Configuration
- **WHEN** responses are served to users
- **THEN** security headers shall be properly configured
- **AND** HTTPS shall be enforced through HSTS
- **AND** clickjacking protection shall be enabled
- **AND** content type sniffing shall be prevented

### Requirement: 前端测试质量门禁
系统**SHALL**在CI/CD流程中实施严格的前端测试质量门禁，确保代码质量达到生产标准。

#### Scenario: 测试覆盖率检查
- **WHEN** 开发者提交代码变更时
- **THEN** CI/CD系统自动运行完整前端测试套件
- **AND** 测试覆盖率必须达到80%以上才能通过质量门禁
- **AND** 覆盖率低于阈值时自动阻止部署并提供详细报告
- **AND** 覆盖率报告包含文件级别和函数级别的详细统计

#### Scenario: 单元测试执行
- **WHEN** 前端代码变更触发CI/CD流程时
- **THEN** 系统自动执行所有单元测试 (Jest + React Testing Library)
- **AND** 测试执行时间不超过5分钟 (优化性能)
- **AND** 失败测试提供详细的错误信息和堆栈跟踪
- **AND** 测试结果通过Slack和邮件通知相关开发人员

#### Scenario: Visual Regression测试
- **WHEN** UI组件发生变更时
- **THEN** 系统自动运行Visual Regression测试 (Storybook + Chromatic)
- **AND** 检测到UI变更时自动生成对比报告
- **AND** 变更需要团队成员审核通过才能继续部署
- **AND** 审核记录和变更历史完整保存

#### Scenario: 测试环境管理
- **WHEN** 设置测试执行环境时
- **THEN** 系统提供独立的测试数据库和Mock服务
- **AND** 测试环境数据与生产环境完全隔离
- **AND** 测试数据自动生成和清理机制
- **AND** 支持并行测试执行以提高效率

### Requirement: 测试结果监控和报告
系统**SHALL**提供全面的测试结果监控和报告功能，支持团队了解测试质量趋势。

#### Scenario: 测试覆盖率趋势分析
- **WHEN** 团队需要了解代码质量趋势时
- **THEN** 系统提供测试覆盖率历史趋势图表
- **AND** 显示每个模块的覆盖率变化情况
- **AND** 标识覆盖率下降的文件和模块
- **AND** 提供改进建议和最佳实践指导

#### Scenario: 测试失败分析
- **WHEN** 测试执行失败时
- **THEN** 系统自动分析失败原因和模式
- **AND** 提供详细的错误诊断和修复建议
- **AND** 记录失败频率和修复时间统计
- **AND** 集成到开发环境提供实时反馈

#### Scenario: 质量仪表板
- **WHEN** 项目管理者需要了解整体质量状况时
- **THEN** 系统提供综合质量仪表板
- **AND** 显示测试覆盖率、执行时间、通过率等关键指标
- **AND** 支持按时间段、模块、团队成员维度分析
- **AND** 提供导出功能和定期报告生成

