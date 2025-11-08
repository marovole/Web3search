## Why
生产环境 https://web3search.pages.dev/ 在2025年11月8日的全面测试（PRODUCTION_TEST_REPORT.md）中暴露出严重功能缺陷。Playwright自动化测试显示：**5个测试通过（26.3%），10个失败（52.6%），4个超时（21.1%）**。核心功能如页面导航、Quick Chat API调用和路由配置存在P0级问题，直接影响用户正常使用。这些问题源于生产环境配置错误、React Router路由失效和API代理配置不当，需要在OpenSpec层定义明确的修复要求。

## What Changes
修复生产环境中的以下关键问题：

1. **页面导航完全失效修复**（P0）
   - 修复历史记录（/history）和监控列表（/watchlist）页面路由
   - 解决React Router生产环境配置错误
   - 修正Cloudflare Pages SPA重定向规则

2. **Quick Chat功能修复**（P0）
   - 修复前端API配置逻辑，使用完整后端URL
   - 消除路径重复问题（`/api/api/v1` → `/api/v1`）
   - 确保通过Cloudflare Pages代理正确访问后端API

3. **测试稳定性改进**（P1）
   - 统一开发环境和生产环境的选择器策略
   - 更新Playwright测试选择器匹配生产DOM结构
   - 增强测试的错误诊断能力

4. **API测试方法优化**（P2）
   - 修改API集成测试使用前端代理路径
   - 不再直接访问后端API端点
   - 增加代理机制的测试覆盖

5. **部署验证增强**（P1）
   - 增加生产环境部署的自动化验证
   - 添加部署后烟雾测试（API端点可达性）
   - 集成测试失败触发自动回滚

**BREAKING**: 移除生产环境相对API路径配置，统一使用完整URL

## Impact
- **Affected specs**: `chat-interface`, `deployment`, `api`
- **Affected code**:
  - frontend/src/utils/env.ts（API配置逻辑）
  - frontend/src/services/api.ts（API客户端）
  - frontend/src/App.tsx（路由配置）
  - frontend/public/_redirects（Cloudflare Pages代理规则）
  - frontend/tests/e2e/*.spec.ts（测试选择器）
  - Render/Railway健康检查配置
  - CI/CD部署流程（集成测试验证）
