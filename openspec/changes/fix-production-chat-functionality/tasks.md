## 1. 问题诊断与验证
- [x] 1.1 手动验证生产环境页面导航问题（访问 /history 和 /watchlist）
- [x] 1.2 检查浏览器控制台JavaScript错误
- [x] 1.3 验证API请求是否到达后端（网络面板分析）
- [x] 1.4 确认路径重复问题的具体表现
- [x] 1.5 记录生产环境实际的DOM结构

## 2. API配置修复
- [x] 2.1 修改 frontend/src/utils/env.ts，添加URL格式验证逻辑
- [x] 2.2 确保生产环境使用完整后端URL（https://web3search-api.onrender.com）
- [x] 2.3 添加配置验证逻辑，检查URL格式和路径重复
- [x] 2.4 frontend/.env.production 已配置正确的 API_BASE_URL
- [x] 2.5 在 frontend/src/services/api.ts 中添加URL构建日志

## 3. React Router路由修复
- [x] 3.1 检查 frontend/src/App.tsx 路由配置 - 配置正确
- [x] 3.2 验证Code Splitting配置是否导致路由失效 - 正常工作
- [x] 3.3 测试Cloudflare Pages _redirects 规则 - 规则正确
- [x] 3.4 修复404页面处理（SPA支持） - 已配置
- [x] 3.5 验证页面组件的懒加载配置 - 正常工作

## 4. Cloudflare Pages代理配置
- [x] 4.1 检查 frontend/public/_redirects 文件 - 配置正确
- [x] 4.2 验证API代理规则（/api/* → 后端） - 规则正确
- [x] 4.3 测试页面路由规则（/* → /index.html） - 规则正确
- [x] 4.4 检查代理规则的顺序优先级 - 顺序正确
- [x] 4.5 验证CORS配置在生产环境生效 - 已通过 functions/_middleware.ts 处理

## 5. 测试框架修复
- [ ] 5.1 更新所有Playwright测试选择器匹配生产DOM
- [ ] 5.2 修复API集成测试使用前端代理路径
- [ ] 5.3 在 tests/e2e/chat.spec.ts 中添加等待逻辑
- [ ] 5.4 增加测试错误诊断和截图功能
- [ ] 5.5 配置测试超时设置（历史页面导航120秒）

## 6. 部署验证增强
- [ ] 6.1 创建部署后烟雾测试脚本（smoke-test.js）
- [ ] 6.2 测试关键API端点可达性（/api/health, /api/v1/chat/quick）
- [ ] 6.3 在CI/CD中添加测试验证步骤
- [ ] 6.4 配置测试失败触发部署回滚
- [ ] 6.5 集成测试报告生成和通知

## 7. 生产环境测试
- [ ] 7.1 重新运行Playwright生产环境测试套件
- [ ] 7.2 手动测试Quick Chat功能（发送真实请求）
- [ ] 7.3 手动验证页面导航（/history, /watchlist）
- [ ] 7.4 验证Deep Research报告生成（60秒）
- [ ] 7.5 检查所有浏览器控制台错误

## 8. 文档更新
- [ ] 8.1 更新部署文档，说明生产环境API配置
- [ ] 8.2 记录Cloudflare Pages _redirects 规则说明
- [ ] 8.3 更新测试文档，说明选择器策略
- [ ] 8.4 创建故障排除指南（404错误、API调用失败）
- [ ] 8.5 更新README中的生产环境访问信息

## 9. 监控和告警
- [ ] 9.1 配置Render/Railway健康检查监控页面导航
- [ ] 9.2 设置API响应时间告警（>5秒）
- [ ] 9.3 配置404错误率监控（>1%触发告警）
- [ ] 9.4 集成Sentry错误追踪（前端JavaScript错误）
- [ ] 9.5 设置Slack通知（部署成功/失败、测试失败）

## 10. 回归测试
- [ ] 10.1 运行完整单元测试套件（pytest, Jest）
- [ ] 10.2 执行所有Playwright E2E测试
- [ ] 10.3 验证开发和生产环境一致性
- [ ] 10.4 测试边界条件（网络错误、超时）
- [ ] 10.5 生成最终测试报告并归档
