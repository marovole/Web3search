## MODIFIED Requirements

### Requirement: API集成测试框架
系统 **SHALL** 提供完整的API集成测试框架，确保前后端接口的正确性和一致性，**使用前端代理路径而非直接访问后端**。

#### Scenario: 后端API集成测试
- **WHEN** 运行后端集成测试套件
- **THEN** 所有核心API端点通过测试（/api/v1/chat/*, /api/v1/reports/*）
- **AND** 测试使用真实的数据库和Redis连接
- **AND** 测试覆盖率达到80%以上
- **AND** 测试执行时间< 2分钟

#### Scenario: 前端API客户端测试（通过代理）
- **WHEN** 运行前端集成测试
- **THEN** API客户端通过前端代理路径（/api/v1/*）发送请求
- **AND** 环境配置正确加载（开发/生产环境）
- **AND** 错误处理逻辑正常工作
- **AND** 所有API调用使用正确的URL路径
- **AND** **不直接调用后端URL（https://web3search-api.onrender.com）**

**Rationale**: 修复测试方法，确保测试通过实际部署环境（Cloudflare Pages代理），而非绕过代理直接访问后端。

#### Scenario: 端到端API流程测试（端到端）
- **WHEN** 执行E2E测试
- **THEN** 完整的用户交互流程正常工作
- **AND** Quick Chat和Deep Research功能可用
- **AND** 错误场景得到正确处理
- **AND** 测试在CI/CD环境中稳定运行
- **AND** **测试使用生产环境的代理配置**

### Requirement: API路由一致性验证
系统 **SHALL** 验证前后端API路由配置的一致性，防止路径错误，**并在生产环境使用完整后端URL**。

#### Scenario: 开发环境URL路径验证
- **WHEN** 前端在开发环境构建API请求URL（使用Vite代理）
- **THEN** build URL pattern shall be: `/api/v1/...`（相对路径）
- **AND** Vite dev server shall proxy to backend (http://localhost:8000)
- **AND** no duplication like `/api/api/v1` shall occur
- **AND** URL building logic shall pass unit tests

#### Scenario: 生产环境URL路径验证（修复版）
- **WHEN** 前端在生产环境构建API请求URL
- **THEN** 使用完整的后端URL: `https://web3search-api.onrender.com/api/v1/...`
- **AND** **不进行路径拼接或添加前缀**
- **AND** 从环境变量VITE_API_BASE_URL直接读取完整URL
- **AND** URL验证应检查是否为完整URL（以https://开头）
- **AND** 验证不应出现`/api/api`重复模式

**Rationale**: 明确生产环境与开发环境的URL构建差异，确保生产环境使用完整URL防止路径重复错误。

#### Scenario: 环境配置测试
- **WHEN** 应用加载环境配置
- **THEN** 根据运行环境正确设置API_BASE_URL
- **AND** 生产环境检测逻辑正确（hostname包含pages.dev, vercel.app, web3search.ai等）
- **AND** 环境变量VITE_API_BASE_URL正确解析为完整URL
- **AND** 配置错误时有明确的错误提示和验证失败

#### Scenario: API端点可达性测试（通过前端）
- **WHEN** 运行端点可达性测试
- **THEN** 所有定义的API端点通过前端代理返回有效响应（非404）
- **AND** 健康检查端点（/api/health）正常工作
- **AND** API文档页面（/api/docs）可访问
- **AND** 测试覆盖所有环境（开发/预发布/生产）
- **AND** **测试不直接访问后端域名**

### Requirement: API错误处理集成测试
系统 **SHALL** 测试各种错误场景下的API行为和恢复机制，**同时在开发和生产环境使用一致的测试策略**。

#### Scenario: 网络错误处理测试
- **WHEN** 模拟网络中断或超时（在E2E测试中）
- **THEN** 前端正确显示错误提示
- **AND** 自动重试机制正常工作（最多3次）
- **AND** 用户可以手动重试失败的请求
- **AND** 离线状态下的行为符合预期（显示离线提示）

#### Scenario: 后端错误响应测试
- **WHEN** 后端返回错误状态码（4xx, 5xx）
- **THEN** 前端正确解析错误信息
- **AND** 显示用户友好的错误消息（非技术性描述）
- **AND** 错误详情记录到日志（Sentry）
- **AND** 特定错误触发相应的恢复流程（如token过期触发重新认证）

#### Scenario: 速率限制测试
- **WHEN** 触发API速率限制（429状态码）
- **THEN** 前端显示"请求过于频繁"提示
- **AND** 显示剩余等待时间倒计时（从Retry-After头解析）
- **AND** 等待期结束后自动允许重试
- **AND** 速率限制信息从响应头正确解析
- **AND** 提供"升级账户"选项（如果适用）

### Requirement: CI/CD集成测试自动化
系统 **SHALL** 在CI/CD流程中自动执行集成测试，确保代码质量，**并验证生产环境配置**。

#### Scenario: PR触发集成测试（包含配置验证）
- **WHEN** 创建或更新Pull Request
- **THEN** 自动触发完整的集成测试套件
- **AND** 运行后端API集成测试（pytest）
- **AND** 运行前端API集成测试（Vitest，通过代理）
- **AND** 执行端到端功能测试（Playwright）
- **AND** **验证生产环境API URL配置**
- **AND** 测试结果显示在PR检查中
- **AND** 测试失败时阻止代码合并
- **AND** 测试报告上传为CI工件

#### Scenario: 测试环境配置（与生产环境一致）
- **WHEN** CI环境运行集成测试
- **THEN** 自动配置测试数据库和Redis
- **AND** 正确设置环境变量和密钥
- **AND** 测试运行在隔离的环境中
- **AND** 测试完成后清理临时资源
- **AND** **测试环境的代理配置与生产环境一致**

#### Scenario: 部署前集成测试（烟雾测试）
- **WHEN** 代码合并到main分支准备部署
- **THEN** 执行完整的测试套件（单元+集成+E2E）
- **AND** 验证环境配置正确性（特别是API_BASE_URL）
- **AND** 测试通过前端代理的API端点可达性
- **AND** 测试所有关键用户流程（Quick Chat, Deep Research, 页面导航）
- **AND** 测试失败时阻止部署并触发告警

#### Scenario: 部署后烟雾测试
- **WHEN** 服务部署完成（Cloudflare Pages + Render）
- **THEN** 自动执行烟雾测试套件
- **AND** 验证健康检查端点响应正常（/api/health）
- **AND** 测试关键API端点通过代理的可达性（/api/v1/chat/*, /api/v1/reports/*）
- **AND** 检查前端应用可访问性（https://web3search.pages.dev）
- **AND** 验证前后端API通信正常（通过代理）
- **AND** 失败时触发告警并回滚部署
- **AND** 生成测试报告并上传到GitHub Release

#### Scenario: 测试覆盖率报告
- **WHEN** 集成测试执行完成
- **THEN** 生成详细的覆盖率报告
- **AND** 覆盖率低于80%时测试失败
- **AND** 覆盖率趋势可视化展示
- **AND** 未覆盖的代码路径明确标识
- **AND** 报告包含API客户端、错误处理、路由配置的覆盖情况
