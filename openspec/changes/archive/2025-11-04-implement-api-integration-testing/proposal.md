# API集成测试实现提案

## Why
当前项目缺乏完整的前后端API集成测试，导致生产环境部署后出现API路由错误、环境配置问题等故障。需要建立系统化的集成测试框架，确保前后端API接口的正确性、一致性和可靠性，降低生产环境故障风险。

## What Changes
- **新增**端到端API集成测试框架（pytest + requests）
- **新增**前端API集成测试套件（Playwright + API测试）
- **新增**环境配置验证测试（开发/生产环境URL配置）
- **新增**API路由一致性测试（防止路径重复、404错误）
- **新增**API错误处理集成测试（网络错误、超时、重试机制）
- **新增**CI/CD集成测试流程（GitHub Actions自动执行）
- **完善**测试文档和最佳实践指南

## Impact
### 影响的规范
- `specs/api/spec.md` - 新增API测试规范（ADDED）
- `specs/deployment/spec.md` - 修改部署测试要求（MODIFIED）

### 影响的代码
- `backend/tests/integration/` - 新增后端集成测试目录
- `frontend/tests/integration/` - 新增前端集成测试目录
- `.github/workflows/integration-tests.yml` - 新增CI测试工作流
- `backend/tests/conftest.py` - 扩展测试配置
- `frontend/src/api/client.test.ts` - 新增API客户端测试
- `docs/testing-guide.md` - 新增测试指南文档

### 预期收益
- 提前发现API路由配置错误，避免生产环境故障
- 确保前后端API契约一致性
- 提升部署信心和系统可靠性
- 建立自动化测试文化和流程
