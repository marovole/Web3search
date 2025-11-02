# CI/CD Testing Integration

本文档说明了Web3search项目中的测试工具如何集成到CI/CD流水线中。

## 🔄 CI/CD 流水线概览

我们的CI/CD流水线使用GitHub Actions，包含以下阶段：

### 1. 测试阶段 (test)
- **多Node.js版本测试**: 在Node.js 18和20上运行
- **ESLint检查**: 代码质量检查
- **TypeScript类型检查**: 类型安全验证
- **单元测试**: Jest + React Testing Library
- **覆盖率检查**: 生成并验证测试覆盖率
- **E2E测试**: Playwright端到端测试

### 2. 构建阶段 (build)
- **应用构建**: Vite构建优化
- **包大小分析**: 分析构建产物大小

### 3. 质量门控阶段 (quality-gates)
- **覆盖率质量门控**: 确保覆盖率达到80%+
- **可访问性测试**: jest-axe自动化a11y检查
- **性能测试**: Lighthouse CI性能评估

### 4. 安全扫描阶段 (security-scan)
- **依赖漏洞扫描**: npm audit
- **代码安全扫描**: Trivy漏洞扫描

### 5. 部署阶段 (deploy)
- **预发布环境**: develop分支自动部署到staging
- **生产环境**: main分支自动部署到production
- **冒烟测试**: 部署后运行基本功能验证

## 📊 测试覆盖率

### 覆盖率要求
- **行覆盖率**: ≥ 80%
- **函数覆盖率**: ≥ 80%
- **分支覆盖率**: ≥ 80%
- **语句覆盖率**: ≥ 80%

### 覆盖率报告
- 生成的覆盖率文件: `coverage/coverage-summary.json`
- HTML报告: `coverage/lcov-report/index.html`
- 上传到Codecov进行可视化跟踪

## 🧪 测试类型

### 单元测试
```bash
# 运行所有单元测试
npm run test:unit

# 监听模式
npm run test:watch

# 生成覆盖率
npm run test:coverage
```

### 集成测试
```bash
# 运行集成测试
npm run test:integration
```

### E2E测试
```bash
# 运行E2E测试
npm run test:e2e

# UI模式
npm run test:e2e:ui

# 查看报告
npm run test:e2e:report
```

### 可访问性测试
```bash
# 运行a11y测试
npm run test:a11y
```

### 性能测试
```bash
# 运行Lighthouse性能测试
npm run test:lighthouse
```

## 🎯 质量门控

### 自动化检查
1. **代码质量**: ESLint + TypeScript
2. **测试覆盖率**: Jest + 覆盖率阈值
3. **安全漏洞**: npm audit + Trivy
4. **性能指标**: Lighthouse CI
5. **可访问性**: jest-axe

### 部署条件
- ✅ 所有测试通过
- ✅ 覆盖率达到阈值
- ✅ 安全扫描通过
- ✅ 构建成功

## 📈 测试报告

### 自动生成的报告
- **测试报告**: `test-report.json`
- **覆盖率报告**: `coverage/`
- **E2E报告**: `playwright-report/`
- **冒烟测试报告**: `smoke-test-report.json`
- **性能报告**: `.lighthouseci/`

### 报告查看
- GitHub Actions中的artifacts
- Codecov覆盖率报告
- Lighthouse CI性能报告

## 🔧 环境配置

### 测试环境变量
```env
NODE_ENV=test
VITE_ENABLE_MOCK_API=true
VITE_ENABLE_TEST_MODE=true
VITE_DISABLE_ANALYTICS=true
```

### CI/CD Secrets
- `VERCEL_TOKEN`: Vercel部署令牌
- `VERCEL_ORG_ID`: Vercel组织ID
- `VERCEL_PROJECT_ID`: Vercel项目ID
- `SLACK_WEBHOOK_URL`: Slack通知webhook
- `CODECOV_TOKEN`: Codecov上传令牌

## 🚀 部署流程

### Staging部署 (develop分支)
1. 代码推送到develop分支
2. 运行完整测试套件
3. 构建应用
4. 部署到Vercel staging
5. 发送Slack通知

### Production部署 (main分支)
1. 代码推送到main分支
2. 运行完整测试套件 + 安全扫描
3. 构建应用
4. 部署到Vercel production
5. 运行冒烟测试
6. 发送Slack通知

## 🛠️ 本地开发

### 运行CI测试
```bash
# 模拟CI环境运行测试
npm run test:ci

# 检查覆盖率
npm run test:coverage-check

# 生成完整测试报告
npm run test:report
```

### 调试E2E测试
```bash
# 调试模式
npm run test:e2e:debug

# 指定测试文件
npx playwright test tests/e2e/search.spec.ts
```

## 📋 最佳实践

### 1. 测试编写
- 使用测试数据工厂生成mock数据
- 遵循AAA模式 (Arrange, Act, Assert)
- 保持测试独立和可重复
- 使用描述性的测试名称

### 2. 覆盖率维护
- 新功能必须包含测试
- 保持覆盖率在80%以上
- 定期审查和优化测试

### 3. 性能监控
- 关注Lighthouse性能分数
- 监控构建包大小变化
- 优化关键渲染路径

### 4. 安全考虑
- 定期更新依赖包
- 及时修复安全漏洞
- 使用最小权限原则

## 🔍 故障排除

### 常见问题

**测试在CI中失败但在本地通过**
- 检查Node.js版本差异
- 确认环境变量设置
- 查看CI日志中的详细错误

**覆盖率不达标**
- 运行 `npm run test:coverage -- --coverageReporters=text`
- 查看未覆盖的代码行
- 添加相应测试用例

**E2E测试超时**
- 增加测试超时时间
- 检查网络连接
- 优化测试等待策略

**部署失败**
- 检查构建错误
- 确认Vercel配置
- 验证环境变量

### 获取帮助
- 查看GitHub Actions日志
- 检查测试报告artifacts
- 联系开发团队

---

## 📚 相关文档

- [Jest配置](./JEST-CONFIG.md)
- [Playwright配置](./E2E-TESTING.md)
- [测试策略](./TESTING-STRATEGY.md)
- [部署指南](./DEPLOYMENT.md)
