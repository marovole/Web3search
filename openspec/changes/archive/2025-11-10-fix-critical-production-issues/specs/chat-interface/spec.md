# Chat Interface Specification Delta

## ADDED Requirements

### Requirement: 错误边界和降级处理

聊天界面 MUST 实现错误边界，捕获 JavaScript 运行时错误并提供友好的降级 UI。

#### Scenario: 全局错误边界捕获未处理的错误
**Given** 聊天界面组件渲染或更新时发生错误
**When** 错误未被组件内部捕获
**Then** 全局错误边界捕获该错误
**And** 显示友好的错误提示："出现问题了，请刷新页面重试"
**And** 提供"刷新页面"和"返回首页"按钮
**And** 错误详情记录到日志（不显示给用户）

#### Scenario: 局部错误边界不影响其他组件
**Given** 聊天消息列表渲染时发生错误
**When** 错误被局部错误边界捕获
**Then** 仅消息列表区域显示错误提示
**And** 输入框和其他 UI 组件继续正常工作
**And** 用户可以继续发送新消息

#### Scenario: 错误边界集成 Sentry
**Given** 错误边界捕获到错误
**When** Sentry 已启用
**Then** 将错误报告发送到 Sentry
**And** 包含错误堆栈、组件栈、用户信息（脱敏）
**And** 包含当前路由和状态信息

### Requirement: 组件测试 ID 标准化

关键 UI 组件 MUST 添加 data-testid 属性，便于自动化测试。

#### Scenario: 聊天输入框包含测试 ID
**Given** 聊天界面渲染完成
**When** 查找聊天输入框
**Then** 输入框元素包含 `data-testid="chat-input"` 或 `data-testid="search-input"`
**And** 测试脚本可以使用该 ID 选择元素

#### Scenario: 主题切换按钮包含测试 ID
**Given** 页面头部渲染完成
**When** 查找主题切换按钮
**Then** 按钮元素包含 `data-testid="theme-toggle"`
**And** 测试脚本可以使用该 ID 选择元素

#### Scenario: 关键按钮包含测试 ID
**Given** 聊天界面渲染完成
**When** 查找关键交互按钮
**Then** 以下按钮包含 data-testid：
 - 发送按钮：`data-testid="send-button"`
 - 模式切换按钮：`data-testid="mode-toggle"`
 - 清空输入按钮：`data-testid="clear-input"`
**And** 测试脚本可以使用这些 ID 进行交互测试

### Requirement: API 错误处理和用户反馈

当 API 请求失败时，聊天界面 MUST 提供清晰的错误提示和恢复选项。

#### Scenario: API 不可用时显示错误提示
**Given** 用户发送聊天消息
**When** API 返回 500 或 503 错误
**Then** 在聊天界面显示错误消息："服务暂时不可用，请稍后重试"
**And** 提供"重试"按钮
**And** 消息输入框保持可用（不清空用户输入）

#### Scenario: API 超时时显示等待提示
**Given** 用户发送聊天消息
**When** API 请求超过 30 秒未响应
**Then** 显示加载指示器和提示："正在处理，请稍候..."
**And** 60 秒后仍未响应，显示超时错误
**And** 提供"取消"和"继续等待"按钮

#### Scenario: 网络离线时显示离线提示
**Given** 用户发送聊天消息
**When** 浏览器检测到网络离线
**Then** 立即显示离线提示："网络连接断开，请检查网络"
**And** 禁用发送按钮
**And** 网络恢复后自动重新启用发送按钮

## MODIFIED Requirements

### Requirement: 聊天界面环境配置

聊天界面 SHALL 直接使用构建时注入的环境变量，不依赖运行时检测。

#### Scenario: 使用构建时 API URL
**Given** 聊天界面初始化
**When** 配置 API 客户端
**Then** 使用 `import.meta.env.VITE_API_BASE_URL` 作为 API 基础 URL
**And** 不使用 `window.location.hostname` 或其他运行时检测
**And** 如果环境变量未设置，抛出错误并显示配置指南

#### Scenario: 调试模式控制
**Given** 聊天界面初始化
**When** 检查调试模式开关
**Then** 使用 `import.meta.env.VITE_DEBUG_MODE` 控制调试输出
**And** 生产环境（VITE_DEBUG_MODE=false）不输出 console.log
**And** 开发环境（VITE_DEBUG_MODE=true）输出详细日志

## ADDED Requirements

### Requirement: Cloudflare Workers API 集成

聊天界面 MUST 正确调用 Cloudflare Workers API，支持流式响应。

#### Scenario: 发送聊天请求到 Workers API
**Given** 用户输入聊天消息并点击发送
**When** 前端发起 API 请求
**Then** 请求发送到 `${VITE_API_BASE_URL}/api/v1/chat/quick-chat`
**And** 请求方法为 POST
**And** 请求头包含：
 - Content-Type: application/json
 - Accept: text/event-stream（流式） 或 application/json（非流式）
**And** 请求体包含：
```json
{
  "query": "<用户输入>",
  "conversation_id": "<uuid>",
  "stream": true
}
```

#### Scenario: 处理 SSE 流式响应
**Given** Workers API 返回 SSE 流
**When** 前端接收流数据
**Then** 使用 EventSource 或 fetch API 处理流：
```javascript
const response = await fetch(url, {
  method: 'POST',
  body: JSON.stringify(data),
  headers: {'Accept': 'text/event-stream'}
});
const reader = response.body.getReader();
```
**And** 逐行解析 SSE 格式：
 - 每行格式为 `data: {json}`
 - 最后一行为 `data: [DONE]`
**And** 实时更新聊天界面显示生成的内容
**And** 处理流中断和错误

#### Scenario: 显示流式响应内容
**Given** SSE 流正在传输 AI 响应
**When** 接收到新的数据块
**Then** 将数据块追加到聊天消息中
**And** 实时渲染消息（每接收一个 token 就更新 UI）
**And** 显示打字指示器（typing indicator）
**And** 流结束后隐藏打字指示器

#### Scenario: 处理 API 速率限制
**Given** 用户频繁发送聊天请求
**When** API 返回 429 Too Many Requests
**Then** 显示速率限制提示："请求过于频繁，请 X 分钟后重试"
**And** 禁用发送按钮 X 分钟
**And** 显示倒计时："还需等待 X 秒"
**And** 从响应头 `Retry-After` 读取等待时间

### Requirement: 搜索自动完成集成

搜索输入框 MUST 调用 Workers 自动完成 API 提供实时建议。

#### Scenario: 触发自动完成请求
**Given** 用户在搜索框输入关键词
**When** 输入长度 >= 2 字符
**Then** 防抖 300ms 后发起请求到 `${VITE_API_BASE_URL}/api/v1/search/autocomplete?q=<keyword>`
**And** 请求方法为 GET
**And** 取消上一个未完成的请求（避免竞态）

#### Scenario: 显示自动完成结果
**Given** 自动完成 API 返回结果
**When** 前端接收响应
**Then** 解析响应：
```json
{
  "query": "bitcoin",
  "results": [
    {"keyword": "Bitcoin price", "category": "cryptocurrency"},
    {"keyword": "Bitcoin mining", "category": "technology"}
  ],
  "count": 2,
  "cached": true
}
```
**And** 在下拉菜单显示结果（最多 10 条）
**And** 高亮匹配的关键词
**And** 显示分类标签（category）

#### Scenario: 选择自动完成建议
**Given** 自动完成下拉菜单显示建议
**When** 用户点击或使用键盘选择某个建议
**Then** 将建议填充到搜索框
**And** 隐藏下拉菜单
**And** 触发搜索（如果配置）

### Requirement: 报告生成状态追踪

如果实现报告生成功能，界面 MUST 显示报告生成进度。

#### Scenario: 请求生成报告
**Given** 用户请求生成报告
**When** 发起请求到 `${VITE_API_BASE_URL}/api/v1/reports/generate`
**Then** API 返回 202 Accepted 和报告 ID
**And** 前端保存报告 ID 到状态
**And** 显示生成中提示："报告生成中，预计需要 2 分钟"

#### Scenario: 轮询报告状态
**Given** 报告生成请求已发起
**When** 前端开始轮询状态
**Then** 每 5 秒请求 `GET /api/v1/reports/<report_id>`
**And** 解析响应获取状态和进度：
```json
{
  "status": "processing",
  "progress": 65
}
```
**And** 更新进度条显示
**And** 状态为 "completed" 时停止轮询并显示报告内容
**And** 状态为 "failed" 时停止轮询并显示错误消息

#### Scenario: 取消报告生成
**Given** 报告正在生成中
**When** 用户点击取消按钮
**Then** 停止轮询
**And** （可选）发送取消请求到 API
**And** 清除报告 ID 和进度显示
