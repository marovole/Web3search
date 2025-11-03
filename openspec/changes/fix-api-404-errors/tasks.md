# Tasks: fix-api-404-errors

## Overview
修复生产环境API URL配置错误，恢复前端应用功能。

## Task Breakdown

### T1: 修复环境配置文件
**Description**: 修改 `src/utils/env.ts` 中的生产环境API配置逻辑

**Steps**:
1. 打开 `src/utils/env.ts`
2. 定位到第127-129行的生产环境配置
3. 将 `config.API_BASE_URL = '/api'` 改为 `config.API_BASE_URL = 'https://web3search-api.onrender.com'`
4. 保存文件

**Validation**:
- 代码修改正确
- 无语法错误
- 逻辑清晰

**Dependencies**: 无

**Estimated Time**: 5分钟

---

### T2: 配置Vercel环境变量
**Description**: 在Vercel项目中添加必要的环境变量

**Steps**:
1. 登录Vercel Dashboard
2. 进入 `web3search-frontend` 项目设置
3. 导航到 Environment Variables 页面
4. 添加以下变量：
   - Name: `VITE_API_BASE_URL`, Value: `https://web3search-api.onrender.com`, Environment: Production
   - Name: `VITE_ENVIRONMENT`, Value: `production`, Environment: Production
5. 保存配置

**Validation**:
- 环境变量正确添加
- 生产环境配置生效

**Dependencies**: T1（代码修改完成）

**Estimated Time**: 5分钟

---

### T3: 本地构建测试
**Description**: 在本地环境测试修复后的代码

**Steps**:
1. 设置本地环境变量：`export VITE_API_BASE_URL=https://web3search-api.onrender.com`
2. 运行构建：`npm run build`
3. 运行预览：`npm run preview`
4. 使用Chrome DevTools检查网络请求
5. 验证API请求路径为 `/api/v1/...` 而非 `/api/api/v1/...`
6. 测试核心功能：
   - 热点数据加载
   - 搜索自动完成
   - 快速对话
   - 深度研究

**Validation**:
- 构建成功无错误
- 预览服务器正常启动
- 所有API请求路径正确
- 核心功能正常工作
- 无404错误

**Dependencies**: T1（代码修改完成）

**Estimated Time**: 10分钟

---

### T4: 提交代码变更
**Description**: 提交修复代码到Git仓库

**Steps**:
1. 添加修改文件：`git add src/utils/env.ts`
2. 提交变更：`git commit -m "fix: 修复生产环境API URL配置错误"`
3. 推送到远程：`git push origin main`

**Validation**:
- 代码成功提交
- 推送到远程仓库成功
- CI/CD流程触发

**Dependencies**: T3（本地测试通过）

**Estimated Time**: 2分钟

---

### T5: 部署到Vercel生产环境
**Description**: 将修复部署到生产环境

**Steps**:
1. 等待Vercel自动部署或手动触发：`vercel --prod`
2. 监控部署状态
3. 等待部署完成

**Validation**:
- 部署成功完成
- 新版本上线
- 无构建错误

**Dependencies**: T2（环境变量配置完成）, T4（代码提交完成）

**Estimated Time**: 5分钟

---

### T6: 生产环境验证
**Description**: 验证生产环境修复效果

**Steps**:
1. 访问生产环境URL：`https://frontend-lemon-pi-26.vercel.app`
2. 清除浏览器缓存（强制刷新）
3. 打开Chrome DevTools Network面板
4. 测试所有核心功能：
   - 加载主页，检查热点数据
   - 尝试搜索，验证自动完成
   - 发送快速对话消息
   - 执行深度研究查询
5. 检查所有API请求：
   - 验证请求路径为 `/api/v1/...`
   - 确认无404错误
   - 检查响应状态码（应为200）
6. 检查Console日志，确认无错误

**Validation**:
- 所有API请求路径正确
- 无404错误
- 所有核心功能正常工作
- 用户体验流畅
- Console无报错

**Dependencies**: T5（生产环境部署完成）

**Estimated Time**: 10分钟

---

### T7: 归档OpenSpec变更
**Description**: 完成变更后归档OpenSpec

**Steps**:
1. 运行验证：`openspec validate fix-api-404-errors --strict`
2. 确认所有验证通过
3. 归档变更：使用 `/openspec:archive` 命令
4. 更新项目状态文档

**Validation**:
- OpenSpec验证通过
- 变更成功归档
- 相关specs已更新

**Dependencies**: T6（生产环境验证通过）

**Estimated Time**: 5分钟

---

## Task Dependencies Graph

```
T1 (修复代码)
  ├─> T2 (配置环境变量)
  └─> T3 (本地测试)
        └─> T4 (提交代码)
              ├─> T5 (部署生产)
              │     └─> T6 (生产验证)
              │           └─> T7 (归档变更)
              └─> (与T2并行)
```

## Parallel Execution Opportunities
- T2（配置环境变量）可以在T3（本地测试）期间并行执行
- 但T5必须等待T2和T4都完成

## Testing Strategy

### Unit Tests
不需要新的单元测试，这是配置修复。

### Integration Tests
- 本地环境API集成测试（T3）
- 生产环境端到端测试（T6）

### Manual Testing Checklist
- [ ] 热点数据正常加载
- [ ] 搜索自动完成正常工作
- [ ] 快速对话功能正常
- [ ] 深度研究功能正常
- [ ] API请求路径正确（`/api/v1/...`）
- [ ] 无404错误
- [ ] Console无错误日志

## Rollback Plan
如果修复失败或导致新问题：

1. **快速回滚**:
   - 在Vercel Dashboard点击"Rollback"到上一个版本
   - 或者使用Git回滚：`git revert HEAD && git push`

2. **回滚验证**:
   - 确认系统恢复到修复前状态
   - 验证无新增问题

3. **问题分析**:
   - 检查详细错误日志
   - 分析失败原因
   - 制定新的修复方案

## Success Metrics
- 404错误数量：从100%降至0%
- API请求成功率：从0%提升至>95%
- 用户可用功能：从0个恢复至所有核心功能
- 响应时间：API响应时间<3秒
- 错误日志：Console无404或API错误

## Post-Deployment Actions
1. 监控生产环境24小时
2. 收集用户反馈
3. 记录修复经验和教训
4. 更新部署文档和检查清单
