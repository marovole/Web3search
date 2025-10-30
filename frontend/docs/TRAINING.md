# 团队培训材料

Web3Search 前端监控和安全系统培训材料。

## 目录

1. [监控系统架构](#监控系统架构)
2. [各模块功能说明](#各模块功能说明)
3. [开发人员使用指南](#开发人员使用指南)
4. [数据分析和报告解读](#数据分析和报告解读)
5. [最佳实践和注意事项](#最佳实践和注意事项)

---

## 监控系统架构

### 整体架构

```
┌─────────────────────────────────────────┐
│         Frontend Application            │
│         (React + TypeScript)            │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼─────┐    ┌─────▼──────┐
│ Monitoring │    │  Security  │
│  Manager   │    │  Manager   │
└─────┬─────┘    └─────┬──────┘
      │                 │
┌─────┴─────────────────┴─────┐
│                              │
│  ┌──────────┐  ┌──────────┐ │
│  │   GA4    │  │  Sentry  │ │
│  └──────────┘  └──────────┘ │
│                              │
│  ┌──────────┐  ┌──────────┐ │
│  │   CSP    │  │    XSS   │ │
│  └──────────┘  └──────────┘ │
│                              │
│  ┌──────────┐  ┌──────────┐ │
│  │  User    │  │  Alert   │ │
│  │ Analytics│  │  System  │ │
│  └──────────┘  └──────────┘ │
└──────────────────────────────┘
```

### 数据流

1. **用户交互** → 触发事件
2. **事件收集** → 各监控系统
3. **数据处理** → 清理、格式化
4. **数据上报** → 第三方服务（GA4、Sentry）
5. **数据分析** → Dashboard 和报告
6. **告警触发** → 异常检测和通知

---

## 各模块功能说明

### 1. Google Analytics 4 (GA4)

#### 功能
- 用户行为追踪
- 页面浏览统计
- 事件追踪
- 转化分析

#### 数据收集
- 自动：页面浏览、会话
- 手动：自定义事件、搜索、功能使用

#### 使用场景
- 分析用户行为
- 优化用户体验
- 追踪转化目标
- 生成用户报告

---

### 2. Sentry

#### 功能
- 错误追踪和监控
- 性能监控
- 会话回放
- 发布追踪

#### 数据收集
- 自动：JavaScript 错误、未处理异常
- 手动：自定义错误、性能指标

#### 使用场景
- 监控生产错误
- 性能优化
- 问题调试
- 版本质量追踪

---

### 3. 用户行为分析

#### 功能
- 自定义事件追踪
- 会话管理
- 用户旅程分析
- 功能使用统计

#### 数据收集
- 搜索操作
- 功能使用
- 性能指标
- 错误事件

#### 使用场景
- 产品分析
- 用户研究
- 功能优化
- A/B 测试

---

### 4. 告警系统

#### 功能
- 性能异常检测
- 错误率监控
- 业务指标监控
- 多渠道通知

#### 监控指标
- 页面加载时间
- API 响应时间
- 错误率
- Core Web Vitals

#### 使用场景
- 实时监控
- 问题预警
- 性能优化
- 质量保障

---

### 5. CSP (Content Security Policy)

#### 功能
- XSS 防护
- 数据注入防护
- 代码执行控制
- 资源加载控制

#### 配置方式
- Meta 标签
- HTTP 响应头
- 动态策略更新

#### 使用场景
- 安全加固
- 漏洞防护
- 合规要求

---

### 6. XSS 防护

#### 功能
- 输入验证
- 输出编码
- HTML 清理
- DOM 操作保护

#### 防护类型
- 反射型 XSS
- 存储型 XSS
- DOM 型 XSS

#### 使用场景
- 用户输入处理
- 内容渲染
- 第三方内容集成

---

## 开发人员使用指南

### 1. 添加事件追踪

#### GA4 事件

```typescript
import { analytics } from '@/services/analytics'

// 追踪按钮点击
analytics.trackEvent('button_click', 'ui', 'download_report')

// 追踪搜索
analytics.trackSearch('Bitcoin', 'quick', 10)

// 追踪功能使用
analytics.trackFeature('deep_research', 'click')
```

#### 自定义事件

```typescript
import { trackEvent } from '@/services/userAnalytics'

trackEvent('custom_event', 'category', {
  label: 'event_label',
  value: 100,
  custom_parameter: 'value'
})
```

---

### 2. 错误追踪

#### 捕获错误

```typescript
import { captureException } from '@/services/sentry'

try {
  riskyOperation()
} catch (error) {
  captureException(error, {
    context: 'operation_name',
    userId: '123',
    additionalInfo: '...'
  })
}
```

#### 记录消息

```typescript
import { captureMessage } from '@/services/sentry'

captureMessage('Important event occurred', 'info', {
  page: window.location.pathname
})
```

---

### 3. 性能追踪

```typescript
import { startSpan } from '@/services/sentry'

// 追踪操作性能
startSpan('expensive_operation', 'task', (span) => {
  performExpensiveOperation()
})
```

---

### 4. 安全最佳实践

#### 输入验证

```typescript
import { sanitizeInput } from '@/services/xssProtection'

const cleanInput = sanitizeInput(userInput)
```

#### HTML 清理

```typescript
import { sanitizeHTML } from '@/services/xssProtection'

const cleanHTML = sanitizeHTML(dirtyHTML)
```

---

## 数据分析和报告解读

### 1. GA4 报告解读

#### 用户报告
- **用户数**: 访问应用的唯一用户
- **新用户**: 首次访问的用户
- **回访用户**: 再次访问的用户

#### 参与度报告
- **会话数**: 用户会话总数
- **平均会话时长**: 用户平均停留时间
- **跳出率**: 单页会话比例
- **页面浏览量**: 页面浏览总数

#### 转化报告
- **转化事件**: 完成的目标事件
- **转化率**: 转化事件比例
- **转化价值**: 转化带来的价值

---

### 2. Sentry 报告解读

#### 错误报告
- **错误率**: 错误发生频率
- **影响用户数**: 受影响的用户数量
- **趋势**: 错误数量变化趋势

#### 性能报告
- **P95 延迟**: 95% 请求的响应时间
- **吞吐量**: 每秒请求数
- **Apdex 分数**: 应用性能指数

---

### 3. 用户行为分析报告

#### 会话分析
- **会话时长**: 用户会话持续时间
- **页面浏览**: 会话中的页面浏览数
- **事件数**: 会话中触发的事件数

#### 功能使用分析
- **功能使用率**: 功能使用频率
- **使用路径**: 功能使用路径
- **流失点**: 用户流失位置

---

## 最佳实践和注意事项

### 1. 事件追踪最佳实践

#### ✅ 正确做法

```typescript
// 使用描述性事件名称
analytics.trackEvent('button_click', 'ui', 'download_report')

// 包含必要的上下文
analytics.trackEvent('search_performed', 'search', {
  query: 'Bitcoin',
  type: 'quick',
  resultCount: 10
})

// 使用一致的命名规范
analytics.trackEvent('feature_used', 'feature', 'deep_research')
```

#### ❌ 错误做法

```typescript
// 避免模糊的事件名称
analytics.trackEvent('click', 'ui') // ❌

// 避免过度追踪
analytics.trackEvent('mouse_move', 'ui') // ❌

// 避免追踪敏感信息
analytics.trackEvent('login', 'auth', {
  password: userPassword // ❌ 不要追踪密码
})
```

---

### 2. 错误处理最佳实践

#### ✅ 正确做法

```typescript
// 提供足够的上下文
captureException(error, {
  context: 'operation_name',
  userId: '123',
  userAgent: navigator.userAgent,
  url: window.location.href
})

// 过滤噪音错误
if (error.message.includes('Network Error')) {
  // 已有重试机制，不需要上报
  return
}
```

#### ❌ 错误做法

```typescript
// 不要捕获所有错误
try {
  everything()
} catch (e) {
  captureException(e) // ❌ 可能捕获预期错误
}

// 不要包含敏感信息
captureException(error, {
  apiKey: secretKey // ❌ 不要包含密钥
})
```

---

### 3. 性能优化最佳实践

#### ✅ 正确做法

```typescript
// 异步加载监控脚本
async function loadMonitoring() {
  await import('@/services/monitoring')
}

// 使用采样率
const sampleRate = 0.1 // 10% 采样

// 批量发送事件
batchEvents(events)
```

#### ❌ 错误做法

```typescript
// 不要阻塞主线程
initMonitoring() // ❌ 同步初始化

// 不要过度采样
const sampleRate = 1.0 // ❌ 100% 采样影响性能
```

---

### 4. 安全最佳实践

#### ✅ 正确做法

```typescript
// 始终验证输入
const cleanInput = sanitizeInput(userInput)

// 使用安全的 DOM 操作
element.textContent = userInput // ✅

// 清理 HTML
const cleanHTML = sanitizeHTML(dirtyHTML)
```

#### ❌ 错误做法

```typescript
// 不要直接使用 innerHTML
element.innerHTML = userInput // ❌

// 不要使用 eval
eval(userInput) // ❌

// 不要信任用户输入
fetch(userProvidedURL) // ❌ 需要验证 URL
```

---

## 常见问题 FAQ

### Q: 如何测试监控功能？

A: 使用开发环境的调试模式，或查看实时报告。

### Q: 监控会影响性能吗？

A: 监控系统经过优化，影响 <2%。使用采样率和异步加载进一步降低影响。

### Q: 如何保护用户隐私？

A: 遵守 GDPR/CCPA，获取用户同意，匿名化数据，不收集敏感信息。

### Q: 如何处理 CSP 违规？

A: 分析违规报告，添加必要的源到 CSP，或使用 nonce。

---

## 培训资源

- [监控使用文档](./MONITORING_GUIDE.md)
- [安全配置指南](./SECURITY_CONFIG.md)
- [问题排查手册](./TROUBLESHOOTING.md)
- [代码示例](../src/services/)

---

**最后更新**: 2025-01-27

