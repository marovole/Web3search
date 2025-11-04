## ADDED Requirements

### Requirement: API集成测试框架
系统 SHALL 提供完整的API集成测试框架，确保前后端接口的正确性和一致性。

#### Scenario: 后端API集成测试
- **WHEN** 运行后端集成测试套件
- **THEN** 所有核心API端点通过测试（/api/v1/chat/*, /api/v1/reports/*）
- **AND** 测试使用真实的数据库和Redis连接
- **AND** 测试覆盖率达到80%以上
- **AND** 测试执行时间< 2分钟

#### Scenario: 前端API客户端测试
- **WHEN** 运行前端集成测试
- **THEN** API客户端正确处理请求和响应
- **AND** 环境配置正确加载（开发/生产环境）
- **AND** 错误处理逻辑正常工作
- **AND** 所有API调用使用正确的URL路径

#### Scenario: 端到端API流程测试
- **WHEN** 执行E2E测试
- **THEN** 完整的用户交互流程正常工作
- **AND** Quick Chat和Deep Research功能可用
- **AND** 错误场景得到正确处理
- **AND** 测试在CI/CD环境中稳定运行

### Requirement: API路由一致性验证
系统 SHALL 验证前后端API路由配置的一致性，防止路径错误。

#### Scenario: URL路径验证
- **WHEN** 前端构建API请求URL
- **THEN** 不出现路径重复（如`/api/api/v1`）
- **AND** 生产环境使用完整URL（`https://web3search-api.onrender.com/api/v1/...`）
- **AND** 开发环境使用相对路径（`/api/v1/...`）配合代理
- **AND** URL构建逻辑通过单元测试验证

#### Scenario: 环境配置测试
- **WHEN** 应用加载环境配置
- **THEN** 根据运行环境正确设置API_BASE_URL
- **AND** 生产环境检测逻辑正确（hostname判断）
- **AND** 环境变量VITE_API_BASE_URL正确解析
- **AND** 配置错误时有明确的错误提示

#### Scenario: API端点可达性测试
- **WHEN** 运行端点可达性测试
- **THEN** 所有定义的API端点返回有效响应（非404）
- **AND** 健康检查端点正常工作
- **AND** API文档页面可访问
- **AND** 测试覆盖所有环境（开发/预发布/生产）

### Requirement: API错误处理集成测试
系统 SHALL 测试各种错误场景下的API行为和恢复机制。

#### Scenario: 网络错误处理测试
- **WHEN** 模拟网络中断或超时
- **THEN** 前端正确显示错误提示
- **AND** 自动重试机制正常工作
- **AND** 用户可以手动重试失败的请求
- **AND** 离线状态下的行为符合预期

#### Scenario: 后端错误响应测试
- **WHEN** 后端返回错误状态码（4xx, 5xx）
- **THEN** 前端正确解析错误信息
- **AND** 显示用户友好的错误消息
- **AND** 错误详情记录到日志
- **AND** 特定错误触发相应的恢复流程

#### Scenario: 速率限制测试
- **WHEN** 触发API速率限制
- **THEN** 前端显示"请求过于频繁"提示
- **AND** 显示剩余等待时间倒计时
- **AND** 等待期结束后自动允许重试
- **AND** 速率限制信息从响应头正确解析

### Requirement: CI/CD集成测试自动化
系统 SHALL 在CI/CD流程中自动执行集成测试，确保代码质量。

#### Scenario: PR触发集成测试
- **WHEN** 创建或更新Pull Request
- **THEN** 自动触发完整的集成测试套件
- **AND** 测试结果显示在PR检查中
- **AND** 测试失败时阻止合并
- **AND** 测试报告上传为CI工件

#### Scenario: 测试环境配置
- **WHEN** CI环境运行集成测试
- **THEN** 自动配置测试数据库和Redis
- **AND** 正确设置环境变量和密钥
- **AND** 测试运行在隔离的环境中
- **AND** 测试完成后清理临时资源

#### Scenario: 测试覆盖率报告
- **WHEN** 集成测试执行完成
- **THEN** 生成详细的覆盖率报告
- **AND** 覆盖率低于阈值时测试失败
- **AND** 覆盖率趋势可视化展示
- **AND** 未覆盖的代码路径明确标识
