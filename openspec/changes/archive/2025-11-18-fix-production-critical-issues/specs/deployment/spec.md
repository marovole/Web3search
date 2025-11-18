# Deployment Spec Delta

## ADDED Requirements

### Requirement: 前端部署验证
前端部署 **SHALL** 包含自动化验证流程，确保部署成功且可访问。

#### Scenario: SSL 证书验证
- **WHEN** 部署前端到 Cloudflare Pages
- **THEN** 验证 SSL/TLS 证书状态（有效、未过期）
- **AND** 测试 HTTPS 连接成功
- **AND** 检查证书链完整性
- **AND** 验证域名解析正确

#### Scenario: 部署 Smoke Tests
- **WHEN** 前端部署完成
- **THEN** 自动运行 smoke tests 验证核心功能
- **AND** 测试首页加载成功（HTTP 200）
- **AND** 测试关键 API 调用（健康检查、搜索）
- **AND** 测试静态资源加载（CSS, JS, 图片）
- **AND** smoke tests 失败时回滚部署

### Requirement: 部署健康检查
部署流程 **SHALL** 在部署后执行健康检查，确保服务正常运行。

#### Scenario: 后端部署健康检查
- **WHEN** Workers API 部署完成
- **THEN** 等待 30 秒后执行健康检查
- **AND** 验证 `/api/v1/health` 返回 healthy 状态
- **AND** 验证关键端点可访问（搜索、聊天）
- **AND** 检查数据库和缓存连接
- **AND** 健康检查失败时发送告警

#### Scenario: 前端部署健康检查
- **WHEN** 前端部署完成
- **THEN** 验证部署 URL 可访问
- **AND** 测试页面渲染成功（无 JavaScript 错误）
- **AND** 验证 API 通信正常
- **AND** 检查性能指标（FCP < 2s, LCP < 3s）
