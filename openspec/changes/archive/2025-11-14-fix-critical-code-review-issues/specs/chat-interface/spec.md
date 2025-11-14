# Chat Interface Specification Deltas

## MODIFIED Requirements

### Requirement: SSE流式响应
系统 SHALL 支持Server-Sent Events（SSE）实现流式输出和实时进度推送，**完整实现Deep Research流式进度更新**。使用标准EventSource API并正确处理GET请求。

#### Scenario: 流式输出逐字显示
- **WHEN** 用户发送Quick Chat请求
- **THEN** 系统通过SSE推送消息片段，前端逐字显示
- **AND** 使用标准EventSource API连接SSE端点
- **AND** 处理`message`事件接收数据流
- **AND** 流式结束后自动关闭连接

#### Scenario: EventSource连接建立
- **WHEN** 前端需要建立SSE连接
- **THEN** 使用EventSource API发起GET请求
- **AND** 将请求参数编码为URL query parameters
- **AND** 验证query参数长度不超过2000字符
- **AND** 正确处理URL编码（特殊字符、空格、UTF-8）
- **AND** 示例实现：
  ```typescript
  const queryParams = new URLSearchParams({
    query: request.query,
    ...(request.conversation_id && { conversation_id: request.conversation_id }),
  })
  const url = `${API_BASE_URL}/api/v1/chat/deep-research/stream?${queryParams}`
  const eventSource = new EventSource(url)
  ```

**Implementation**: `frontend/src/services/api.ts:107`

#### Scenario: 查询长度验证
- **WHEN** 用户输入Deep Research查询
- **THEN** 前端必须验证查询长度
- **AND** 如果查询超过2000字符，显示错误提示："查询内容过长，请缩短至2000字符以内"
- **AND** 阻止表单提交
- **AND** 在输入框下方显示字符计数器
- **AND** 字符计数器在接近限制时变红（如超过1800字符）

**Rationale**: EventSource使用GET请求，URL长度受浏览器和代理服务器限制（通常2048字符）。限制为2000字符提供安全缓冲。

#### Scenario: SSE连接异常处理
- **WHEN** SSE连接中断（如网络抖动）
- **THEN** EventSource自动尝试重连（浏览器内置功能）
- **AND** 前端显示"连接中断，正在重连..."
- **AND** 3次重连失败后，显示错误并提供手动重试按钮
- **AND** 清理EventSource资源（调用eventSource.close()）

#### Scenario: Deep Research完整进度推送
- **WHEN** Deep Research任务执行中
- **THEN** 后端通过SSE推送各阶段进度事件
- **AND** 前端监听`message`事件并解析JSON数据
- **AND** 根据事件类型更新UI：
  - `progress`: 更新进度条和当前阶段文本
  - `result`: 显示最终研究报告
  - `error`: 显示错误信息并关闭连接
  - `done`: 标记任务完成并关闭连接
- **AND** 示例事件处理：
  ```typescript
  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data)
    switch (data.type) {
      case 'progress':
        updateProgress(data.stage, data.content)
        break
      case 'result':
        displayResult(data.content)
        break
      case 'error':
        showError(data.message)
        eventSource.close()
        break
      case 'done':
        markComplete()
        eventSource.close()
        break
    }
  })
  ```

#### Scenario: EventSource生命周期管理
- **WHEN** 组件挂载/卸载或页面切换
- **THEN** 必须正确管理EventSource生命周期
- **AND** 组件挂载时创建EventSource连接
- **AND** 组件卸载时调用`eventSource.close()`释放资源
- **AND** 用户取消请求时立即关闭连接
- **AND** 使用React useEffect清理函数管理资源：
  ```typescript
  useEffect(() => {
    const eventSource = new EventSource(url)
    // ... event handlers
    return () => {
      eventSource.close() // 清理
    }
  }, [url])
  ```

#### Scenario: SSE错误状态处理
- **WHEN** EventSource遇到错误
- **THEN** 监听`error`事件
- **AND** 区分错误类型：
  - 网络错误（readyState === EventSource.CLOSED）
  - HTTP错误（如429 Rate Limited, 414 URI Too Long）
  - 服务器错误（5xx）
- **AND** 显示相应的用户友好错误信息
- **AND** 对于414错误，提示用户缩短查询
- **AND** 对于429错误，显示"请求过于频繁，请稍后再试"

---

### Requirement: 智能错误处理和重试机制
聊天界面 SHALL 提供智能的错误处理和重试机制，确保用户体验的连续性。**特别处理SSE特定错误场景**。

#### Scenario: API请求失败
- **WHEN** API请求失败或超时
- **THEN** 显示友好的错误提示
- **AND** 根据错误类型提供具体建议：
  - 414 URI Too Long → "查询内容过长，请缩短后重试"
  - 429 Too Many Requests → "请求过于频繁，请等待X秒后重试"
  - 500+ Server Error → "服务暂时不可用，请稍后重试"
  - Network Error → "网络连接失败，请检查网络后重试"
- **AND** 提供"重试"按钮
- **AND** 对于速率限制错误，显示倒计时直到允许重试

#### Scenario: SSE连接超时
- **WHEN** SSE连接建立后长时间无响应（超过30秒）
- **THEN** 前端显示超时警告
- **AND** 继续等待（不立即关闭，因为Deep Research可能需要较长时间）
- **AND** 如果超过2分钟仍无响应，自动关闭连接并提示用户
- **AND** 提供"取消"按钮允许用户主动终止

---

### Requirement: 用户交互体验
系统**SHALL**提供流畅、友好的用户交互体验。**特别关注表单验证和输入限制**。

#### Scenario: 输入验证与提示
- **WHEN** 用户在输入框输入文字
- **THEN** 实时验证输入合法性
- **AND** 对于Deep Research，显示字符计数（X / 2000）
- **AND** 超过1800字符时，计数器变黄色警告
- **AND** 超过2000字符时，计数器变红色并禁用发送按钮
- **AND** 显示提示："查询内容不能超过2000字符"
- **AND** 验证不能为空（禁用发送按钮）

#### Scenario: 表单提交防护
- **WHEN** 用户点击发送按钮
- **THEN** 再次验证查询长度（防止绕过客户端验证）
- **AND** 如果验证失败，阻止提交并显示错误
- **AND** 验证成功后，禁用发送按钮防止重复提交
- **AND** 显示加载状态
- **AND** 请求完成或失败后，重新启用发送按钮

---

## ADDED Requirements

### Requirement: URL参数编码与安全
前端 SHALL 正确编码URL参数，防止注入攻击和字符编码问题。

#### Scenario: Query参数编码
- **WHEN** 构建SSE连接URL
- **THEN** 使用`URLSearchParams`自动处理编码
- **AND** 支持所有UTF-8字符（中文、日文、特殊符号等）
- **AND** 正确转义特殊字符（空格→%20, &→%26, =→%3D）
- **AND** 不手动拼接查询字符串（避免注入）

#### Scenario: XSS防护
- **WHEN** 从URL参数接收数据或显示用户输入
- **THEN** 使用React的默认转义机制（JSX）
- **AND** 不使用`dangerouslySetInnerHTML`除非必要
- **AND** 对于Markdown渲染，使用经过安全处理的库（如react-markdown）
- **AND** 配置CSP头部限制内联脚本

---

### Requirement: 用户输入辅助
系统 SHALL 提供输入辅助功能，帮助用户构建有效的查询。

#### Scenario: 查询模板
- **WHEN** 用户首次访问Deep Research
- **THEN** 显示常见查询模板：
  - "分析比特币最近的价格走势和市场情绪"
  - "比较以太坊和Solana的技术优劣"
  - "解释DeFi中的无常损失及如何避免"
- **AND** 点击模板自动填入输入框
- **AND** 模板长度保证在2000字符以内

#### Scenario: 智能查询建议
- **WHEN** 用户输入查询接近2000字符限制
- **THEN** 显示"建议缩短查询"提示
- **AND** 提供AI辅助缩短功能（可选，未来功能）
- **AND** 建议将长查询拆分为多个短查询

---

## Implementation Notes

**Breaking Change**: 前端SSE客户端实现从假设的POST请求改为正确的GET请求。虽然这在代码中已经使用EventSource（只支持GET），但后端之前实现为POST导致功能完全不可用。此次修复使前端和后端契约一致。

**Migration**: 不涉及数据迁移。前端代码`frontend/src/services/api.ts:107-114`已经正确使用EventSource和GET，只需确保后端端点也改为GET即可。

**Testing**:
- 手动测试：使用浏览器开发者工具Network标签验证EventSource连接
- 自动化测试：使用Playwright E2E测试验证Deep Research流式输出
- 边界测试：测试1999字符、2000字符、2001字符查询
