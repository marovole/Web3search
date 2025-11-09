## MODIFIED Requirements

### Requirement: 对话界面响应式设计
聊天界面 **SHALL** 提供现代化的响应式设计，**完整支持Deep Research进度可视化**，**并确保生产环境页面导航完全正常**。

#### Scenario: 桌面端布局
- **WHEN** 用户在桌面端访问应用
- **THEN** 界面显示为三栏布局（侧边栏、聊天区域、信息面板）
- **AND** 所有功能按钮和控件正常显示和交互
- **AND** 支持键盘快捷键操作
- **AND** **Deep Research进度显示在独立面板中**
- **AND** **页面导航（/history, /watchlist）通过React Router正确路由，无404错误**

**Rationale**: 修复生产环境页面导航失效问题，确保历史记录和监控列表页面可访问且正确渲染。

#### Scenario: Deep Research进度可视化
- **WHEN** Deep Research任务执行中
- **THEN** 显示六维分析进度面板：
  - TL;DR生成：⏳ 进行中（40%）
  - 基本面分析：✅ 已完成
  - 技术分析：⏸️ 等待中
  - 链上数据：✅ 已完成
  - 社媒情绪：⏳ 进行中（75%）
  - 竞品对比：⏸️ 等待中
- **AND** 使用图标和颜色区分状态（进行中/已完成/失败）
- **AND** 显示总体进度条（0-100%）
- **AND** 显示预计剩余时间
- **AND** 已完成的维度内容实时显示在聊天区域

#### Scenario: Deep Research结果展示
- **WHEN** Deep Research完成
- **THEN** 在聊天区域展示完整的结构化报告
- **AND** 使用折叠面板组织各个分析维度
- **AND** 表格和图表正确渲染
- **AND** 提供"导出PDF"和"分享链接"按钮
- **AND** 支持复制单个章节内容
- **AND** 提供"重新生成"选项（针对失败的维度）

#### Scenario: 页面导航功能正常
- **WHEN** 用户点击"历史记录"按钮
- **THEN** 浏览器URL变更为 /history
- **AND** 历史记录页面在2秒内加载完成
- **AND** 页面显示报告历史列表
- **AND** 无JavaScript错误在控制台
- **AND** 用户可以点击返回按钮回到主页

**Rationale**: 确保React Router生产环境配置正确，Cloudflare Pages SPA重定向规则正常工作。

#### Scenario: 监控列表页面访问
- **WHEN** 用户点击"监控列表"按钮
- **THEN** 浏览器URL变更为 /watchlist
- **AND** 监控列表页面在2秒内加载完成
- **AND** 页面显示用户关注项目列表
- **AND** 支持项目添加/删除操作
- **AND** 页面刷新后状态保持

### Requirement: API Interface Integration
The system **SHALL** provide seamless integration between frontend and backend APIs with proper error handling and routing, **using complete backend URLs in production environment**.

#### Scenario: API Route Consistency
- **WHEN** frontend makes API calls to backend
- **THEN** all routes shall use correct base URL without path duplication
- **AND** API requests shall be routed to `https://web3search-api.onrender.com/api/v1/...`
- **AND** no 404 errors shall occur due to incorrect URL construction
- **AND** environment configuration shall properly set API_BASE_URL to complete URL
- **AND** **production environment SHALL NOT use relative paths like `/api`**

**Rationale**: 修复生产环境API URL配置错误，确保前端正确构建API请求路径，避免路径重复（`/api/api/v1`）导致的404错误。统一使用完整后端URL。

#### Scenario: Production Environment API Configuration
- **WHEN** application runs in production environment (detected by hostname)
- **THEN** API_BASE_URL shall be set to `https://web3search-api.onrender.com`
- **AND** environment variable VITE_API_BASE_URL shall be properly configured
- **AND** API requests shall successfully reach backend endpoints
- **AND** all chat-related API calls shall work correctly
- **AND** Quick Chat responses shall arrive within 3 seconds

**Rationale**: 确保生产环境配置正确，恢复快速对话和深度研究功能的正常运作。移除导致请求失败的相对路径逻辑。

#### Scenario: API Error Prevention with URL Validation
- **WHEN** API configuration is loaded at application startup
- **THEN** URL validation shall prevent path duplication
- **AND** configuration logic shall use complete URLs in production (not relative paths)
- **AND** API service layer shall not add duplicate path prefixes
- **AND** validation errors shall be logged with actionable messages
- **AND** configuration shall be checked in CI/CD pipeline before deployment

**Rationale**: 从根本上防止API路径配置错误，建立清晰的环境配置规范。简化配置逻辑，消除开发和生产环境的差异导致的错误。

#### Scenario: Cloudflare Pages API Proxy Configuration
- **WHEN** frontend makes API requests through Cloudflare Pages
- **THEN** requests to `/api/v1/*` shall proxy to backend without path modification
- **AND** proxy response time shall be < 100ms overhead
- **AND** CORS headers shall be correctly forwarded
- **AND** error responses from backend shall properly propagate to frontend

### Requirement: Frontend Error Handling
The system **SHALL** provide comprehensive error handling for all frontend operations with user-friendly feedback and **automatic retry mechanisms for network failures**.

#### Scenario: Network Error Recovery with Retry
- **WHEN** network connectivity is lost or API request times out (after 10 seconds)
- **THEN** the system shall display appropriate error message: "网络连接不稳定，请检查网络后重试"
- **AND** automatically retry failed requests up to 3 times with exponential backoff (1s, 3s, 5s)
- **AND** maintain user session state during offline periods
- **AND** provide manual "重试" button after all retries exhausted
- **AND** log detailed error information for debugging with error codes

**Rationale**: 增强网络错误恢复能力，改善用户体验，提供清晰的错误反馈和恢复选项。

#### Scenario: API Error Display
- **WHEN** backend returns error responses (4xx, 5xx)
- **THEN** frontend shall display clear, actionable error messages in user's language
- **AND** provide users with recovery options when applicable (e.g., "重新发送", "刷新页面")
- **AND** log detailed error information including request ID, timestamp, and response body
- **AND** categorize errors by type (network, authentication, server, rate limit)

#### Scenario: Quick Chat Error Handling
- **WHEN** Quick Chat API request fails or returns error after user sends message
- **THEN** display error message in chat interface: "消息发送失败，请重试"
- **AND** provide "重新发送" button to retry the message
- **AND** preserve user input if retry fails
- **AND** log error to monitoring system with conversation context
- **AND** after 3 consecutive failures, suggest "刷新页面"

### Requirement: 用户交互体验
系统 **SHALL** 提供流畅、友好的用户交互体验，**包含输入验证、加载状态和错误提示的完整流程**。

#### Scenario: 输入验证与提示
- **WHEN** 用户在输入框输入文字
- **THEN** 实时显示字符计数（最多1000字）
- **AND** 超过1000字时显示警告"输入过长，请精简问题"
- **AND** 支持Enter键发送、Shift+Enter换行
- **AND** 空输入时发送按钮禁用（灰色）

#### Scenario: 加载状态动画
- **WHEN** 系统处理请求时
- **THEN** 显示加载动画（跳动的点点或波纹效果）
- **AND** Quick Chat显示"思考中..."
- **AND** Deep Research显示详细进度文案
- **AND** 用户可以点击"停止生成"按钮取消请求

#### Scenario: 错误提示友好
- **WHEN** 请求失败（如API错误、超时）
- **THEN** 显示用户友好的错误提示：
  - 网络错误 → "网络连接不稳定，请检查网络后重试"
  - API限流 → "请求过于频繁，请稍后再试（剩余时间XX秒）"
  - 服务器错误 → "服务暂时不可用，我们正在修复中"
- **AND** 提供"重试"按钮
- **AND** 不显示技术性错误信息（如堆栈跟踪）

### Requirement: 智能错误处理和重试机制
聊天界面 **SHALL** 提供智能的错误处理和重试机制，确保用户体验的连续性。

#### Scenario: 网络连接错误与自动恢复
- **WHEN** 检测到网络连接中断或不稳定
- **THEN** 显示友好的离线状态提示："您已离线，请检查网络连接"
- **AND** 自动保存用户输入的内容到localStorage
- **AND** 网络恢复后自动重试失败的请求
- **AND** 提供手动"刷新页面"按钮作为备选方案
- **AND** 显示重试次数和状态（"正在重试(1/3)..."）

#### Scenario: API请求失败处理
- **WHEN** API请求失败或超时（状态码4xx/5xx或网络超时）
- **THEN** 显示具体的错误信息和建议解决方案
- **AND** 提供"重试发送"选项
- **AND** 记录失败的消息，允许稍后重新发送
- **AND** 区分临时错误（自动重试）和永久错误（需要用户操作）
- **AND** 对于严重错误（如500），显示"联系支持"选项

### Requirement: API客户端错误处理集成
系统 **SHALL** 在API客户端层面统一处理错误，确保所有API调用都有适当的错误处理。

#### Scenario: API客户端统一错误处理
- **WHEN** 任何API请求失败（网络错误、超时、4xx/5xx响应）
- **THEN** API客户端捕获错误并转换为标准化的错误对象
- **AND** 错误对象包含：错误码、错误消息、请求ID、时间戳
- **AND** 根据错误类型自动决定重试策略
- **AND** 将错误信息传递给UI组件显示
- **AND** 记录错误日志到监控系统（Sentry）

#### Scenario: Quick Chat API错误场景
- **WHEN** Quick Chat API返回错误响应或超时
- **THEN** frontend检测错误类型（timeout, 4xx, 5xx, network）
- **AND** 对超时错误（10秒）自动重试最多3次
- **AND** 对4xx错误显示用户友好的消息（如"请求格式错误"）
- **AND** 对5xx错误显示"服务暂时不可用"并记录详细日志
- **AND** 对网络错误显示"网络连接失败"并启用离线模式
- **AND** 所有错误状态在UI中清晰显示，不阻塞用户输入

### Requirement: 响应消息格式化与交互
系统 **SHALL** 正确渲染AI响应的Markdown格式，并支持丰富的交互功能。

#### Scenario: Markdown渲染正确性
- **WHEN** AI返回Markdown格式的响应（包含##标题、**粗体**、*斜体*、列表、表格、代码块）
- **THEN** frontend正确渲染所有Markdown元素
- **AND** 标题（#/##/###）显示不同字号和颜色
- **AND** 粗体（**text**）和斜体（*text*）正确显示
- **AND** 列表（- item）显示为项目符号或编号
- **AND** 表格（| col |）渲染为HTML表格，支持横向滚动（移动端）
- **AND** 代码块（```code```）有语法高亮和复制按钮
- **AND** 链接可点击跳转并在新标签页打开

#### Scenario: 代码块交互功能
- **WHEN** 响应包含代码块时
- **THEN** 显示语法高亮（支持Solidity、JavaScript、Python等）
- **AND** 提供"复制代码"按钮，点击后复制到剪贴板
- **AND** 提供代码语言标签显示
- **AND** 长代码块支持展开/折叠
- **AND** 显示行号便于引用

#### Scenario: 表格交互优化
- **WHEN** 响应包含Markdown表格时
- **THEN** 正确渲染为HTML表格
- **AND** 表头有背景色区分
- **AND** 长表格支持横向滚动（特别是移动端）
- **AND** 表格内容可复制
- **AND** 支持表格内链接点击

### Requirement: 测试一致性与稳定性
系统 **SHALL** 确保开发和生产环境测试选择器一致，提高测试可靠性。

#### Scenario: 选择器策略统一
- **WHEN** 编写或维护Playwright E2E测试
- **THEN** 使用data-testid属性作为主要选择器
- **AND** 避免依赖CSS类名或文本内容的选择器
- **AND** 为关键交互元素添加data-testid属性
- **AND** 在前后端代码中统一使用相同的选择器策略
- **AND** 测试代码中选择器定义在constants文件中，便于维护

#### Scenario: 生产环境测试稳定性
- **WHEN** 运行生产环境测试（https://web3search.pages.dev）
- **THEN** 测试选择器与生产DOM结构完全匹配
- **AND** 添加适当的等待条件（waitForSelector, waitForLoadState）
- **AND** 测试超时设置合理（页面导航120秒，API调用30秒）
- **AND** 失败的测试提供详细的错误信息和截图
- **AND** 测试结果包含性能指标（响应时间、加载时间）
