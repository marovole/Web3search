# Proposal: fix-api-404-errors

## Summary
修复生产环境API URL配置错误导致的404问题，恢复前端应用的完整功能。

## Problem Statement
当前生产环境的前端应用出现多个API请求404错误，导致以下功能无法正常工作：
1. 热点数据加载失败（`/api/api/v1/trending/hotspots`）
2. 搜索自动完成失败（`/api/api/v1/search/autocomplete`）
3. 快速对话功能失败（`/api/api/v1/chat/quick-chat`）
4. 深度研究功能失败（`/api/api/v1/chat/deep-research/stream`）

**根本原因**：`src/utils/env.ts` 第127-129行的生产环境配置逻辑错误，将 `API_BASE_URL` 设置为 `/api`，但 API 调用时又添加 `/api/v1` 前缀，导致路径重复：`/api` + `/api/v1` = `/api/api/v1`。

**影响范围**：
- 所有生产环境用户无法使用核心功能
- 用户体验严重受损
- 系统实际上不可用

## Solution Approach
修复环境配置逻辑，使用正确的完整后端URL，并在Vercel中配置相应的环境变量。

### 核心变更
1. **修改 `src/utils/env.ts`**：
   - 将生产环境的 `API_BASE_URL` 从 `/api` 改为完整的后端URL
   - 使用 `https://web3search-api.onrender.com` 作为后端API地址

2. **配置Vercel环境变量**：
   - 添加 `VITE_API_BASE_URL=https://web3search-api.onrender.com`
   - 添加 `VITE_ENVIRONMENT=production`

3. **验证修复**：
   - 本地构建测试
   - 验证API请求路径正确性
   - 部署到Vercel生产环境
   - 确认所有API端点正常工作

## Success Criteria
- ✅ 所有API请求路径正确（`/api/v1/...` 而非 `/api/api/v1/...`）
- ✅ 热点数据正常加载
- ✅ 搜索自动完成正常工作
- ✅ 快速对话功能正常工作
- ✅ 深度研究功能正常工作
- ✅ 控制台无404错误
- ✅ 用户可以正常使用所有核心功能

## Impact Analysis

### Capabilities Affected
- **chat-interface**: API请求路径修复，恢复对话功能
- **deployment**: 环境配置优化，正确的API URL配置

### User Impact
- **Before Fix**: 用户无法使用任何核心功能，只能看到错误提示
- **After Fix**: 用户可以正常使用所有功能，体验流畅

### Technical Debt
- **Adds**: 无
- **Resolves**: 修复了配置错误导致的生产环境问题

### Risks
- **Low Risk**: 配置修改简单直接，影响范围明确
- **Mitigation**: 本地测试验证后再部署，可快速回滚

## Implementation Timeline
- **Total Estimate**: 30分钟
- **Phase 1**: 修复代码配置（10分钟）
- **Phase 2**: 配置Vercel环境变量（5分钟）
- **Phase 3**: 测试验证（15分钟）

## Dependencies
- Vercel项目访问权限（配置环境变量）
- 后端API服务正常运行（`https://web3search-api.onrender.com`）

## Related Changes
- 无

## Decision Log
### 2025-11-03: 选择完整URL而非相对路径
- **Decision**: 使用完整后端URL（`https://web3search-api.onrender.com`）而非相对路径（`/api`）
- **Rationale**:
  1. Vercel部署不使用API代理功能
  2. 前端需要直接访问后端API
  3. 避免路径重复问题
  4. 简化配置管理
- **Alternatives Considered**:
  1. 配置Vercel API代理 - 需要额外配置且增加复杂度
  2. 修改API服务层逻辑 - 影响范围更大，风险更高
