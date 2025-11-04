## ADDED Requirements

### Requirement: 部署前集成测试验证
系统 SHALL 在部署前执行完整的集成测试套件，确保代码质量和功能正确性。

#### Scenario: CI集成测试门禁
- **WHEN** Pull Request创建或更新
- **THEN** 自动触发集成测试工作流
- **AND** 运行后端API集成测试（pytest）
- **AND** 运行前端API集成测试（Vitest）
- **AND** 执行端到端功能测试（Playwright）
- **AND** 所有测试通过后才允许合并代码

#### Scenario: 部署前完整性检查
- **WHEN** 代码合并到main分支准备部署
- **THEN** 执行完整的测试套件（单元+集成+E2E）
- **AND** 验证环境配置正确性
- **AND** 测试API端点可达性
- **AND** 检查数据库迁移脚本
- **AND** 验证所有依赖项可用

#### Scenario: 部署后烟雾测试
- **WHEN** 服务部署完成
- **THEN** 自动执行烟雾测试套件
- **AND** 验证健康检查端点响应正常
- **AND** 测试关键API端点（/api/v1/chat/*, /api/v1/reports/*）
- **AND** 检查前端应用可访问性
- **AND** 验证前后端API通信正常
- **AND** 失败时触发告警并回滚部署

## MODIFIED Requirements

### Requirement: CI/CD自动化
系统**SHALL**实施持续集成和持续部署流程，**包括完整的集成测试验证**。

#### Scenario: GitHub Actions自动测试
- **WHEN** 创建Pull Request
- **THEN** 自动触发GitHub Actions工作流
- **AND** 运行单元测试（pytest）
- **AND** 运行代码质量检查（pylint/black）
- **AND** 运行前端测试（Jest）
- **AND** **运行API集成测试套件（新增）**
- **AND** **运行端到端功能测试（新增）**
- **AND** 所有检查通过后PR才能合并
- **AND** 测试失败时在PR页面显示错误详情

#### Scenario: 自动部署流程
- **WHEN** PR合并到main分支
- **THEN** 自动触发以下流程：
  1. GitHub Actions运行完整测试套件**（包括集成测试）**
  2. 测试通过后Vercel开始前端部署
  3. **执行部署前环境配置验证（新增）**
  4. Railway自动拉取最新代码
  5. Railway重新构建Docker镜像
  6. Railway滚动更新服务（零停机）
  7. **执行部署后烟雾测试（新增）**
  8. **验证API端点可达性（新增）**
- **AND** 整个流程10分钟内完成
- **AND** 每个步骤状态在Slack频道实时通知
- **AND** **集成测试或烟雾测试失败时自动回滚（新增）**

#### Scenario: 部署版本标记
- **WHEN** 部署成功后**且所有测试通过**
- **THEN** 自动创建Git tag（如v1.2.3）
- **AND** tag推送到远程仓库
- **AND** 创建GitHub Release（包含变更日志**和测试报告**）
- **AND** 在Railway中标记部署版本
- **AND** 前端在页面footer显示当前版本号

### Requirement: 健康检查与监控
系统**SHALL**提供健康检查端点和实时监控能力，**包括集成测试状态监控**。

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
    "version": "1.0.0",
    "tests": {
      "last_integration_test": "2025-01-15T09:00:00Z",
      "last_test_status": "passed",
      "coverage": "85%"
    }
  }
  ```
- **AND** 检查数据库连接（执行简单查询）
- **AND** 检查Redis连接（执行PING命令）
- **AND** 检查Celery状态（查询活跃Worker）
- **AND** **报告最近一次集成测试状态（新增）**
- **AND** 如任何服务不健康，返回503状态码

#### Scenario: Railway健康检查配置
- **WHEN** Railway配置健康检查
- **THEN** 设置检查路径：`/health`
- **AND** 检查间隔：30秒
- **AND** 超时时间：10秒
- **AND** 失败阈值：3次连续失败
- **AND** **健康检查包含API端点可达性验证（新增）**
- **AND** 失败时Railway自动重启服务
