# 前端监控使用指南

Web3Search 前端应用的完整监控和分析系统使用指南。

## 目录

1. [监控系统概览](#监控系统概览)
2. [Google Analytics 4 使用](#google-analytics-4-使用)
3. [Sentry 性能监控](#sentry-性能监控)
4. [用户行为分析](#用户行为分析)
5. [性能指标说明](#性能指标说明)
6. [告警系统](#告警系统)
7. [常见问题排查](#常见问题排查)

---

## 监控系统概览

### 监控架构

```
┌─────────────────────┐
│   Frontend App      │
│   (React + Vite)    │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼────────┐
│   GA4  │   │   Sentry   │
│        │   │            │
└───┬────┘   └───┬────────┘
    │            │
┌───▼────────────▼───┐
│  User Analytics    │
│  (Custom Tracking) │
└──────────┬─────────┘
           │
    ┌──────▼──────┐
    │  Alert      │
    │  System     │
    └─────────────┘
```

### 监控组件

| 组件 | 用途 | 数据收集 |
|------|------|----------|
| **Google Analytics 4** | 用户行为追踪、页面浏览、转化分析 | 页面浏览、事件、用户属性 |
| **Sentry** | 错误追踪、性能监控、用户体验指标 | 错误、性能数据、会话回放 |
| **用户行为分析** | 自定义事件追踪、会话管理 | 搜索、交互、功能使用 |
| **告警系统** | 性能异常检测、错误率监控 | 指标阈值、告警通知 |

---

## Google Analytics 4 使用

### 1. 快速开始

#### 获取 Measurement ID

1. 访问 [Google Analytics](https://analytics.google.com/)
2. 创建 GA4 属性（如果还没有）
3. 在"管理" → "数据流"中创建 Web 数据流
4. 复制 Measurement ID（格式：`G-XXXXXXXXXX`）

#### 配置环境变量

在 `.env` 文件中添加：

```bash
VITE_GA_MEASUREMENT_ID=G-XXXXXXXXXX
VITE_ENABLE_ANALYTICS=true
```

#### 初始化

监控系统会在应用启动时自动初始化 GA4。如果用户已同意数据收集，GA4 将自动开始追踪。

### 2. 事件追踪

#### 自动追踪的事件

- **页面浏览** (`page_view`): 自动追踪所有路由导航
- **会话开始** (`session_start`): 用户会话开始
- **会话结束** (`session_end`): 用户会话结束

#### 自定义事件追踪

```typescript
import { analytics } from '@/services/analytics'

// 追踪搜索事件
analytics.trackSearch('Bitcoin', 'quick', 5)

// 追踪功能使用
analytics.trackFeature('deep_research', 'click')

// 追踪自定义事件
analytics.trackEvent('button_click', 'ui', 'download_report', 1)

// 追踪性能指标
analytics.trackPerformance('page_load_time', 1500, 'ms')
```

#### 事件参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `eventName` | 事件名称 | `'button_click'` |
| `category` | 事件类别 | `'ui'`, `'search'`, `'feature'` |
| `label` | 事件标签 | `'download_report'` |
| `value` | 数值 | `1`, `1500` |
| `custom_parameters` | 自定义参数 | `{ report_id: '123' }` |

### 3. 数据查看

#### GA4 控制台

1. 访问 [Google Analytics](https://analytics.google.com/)
2. 选择对应的 GA4 属性
3. 查看报表：
   - **实时**: 查看当前用户活动
   - **获取**: 查看用户来源
   - **参与度**: 查看页面浏览、事件
   - **转化**: 查看目标完成情况

#### 关键指标

- **用户数**: 访问应用的用户数量
- **会话数**: 用户会话数量
- **页面浏览量**: 页面浏览总数
- **平均会话时长**: 用户平均停留时间
- **跳出率**: 单页会话比例
- **事件数**: 触发的事件总数

### 4. 隐私合规

GA4 集成完全符合 GDPR 和 CCPA 要求：

- ✅ 需要用户明确同意才收集数据
- ✅ 支持用户撤回同意
- ✅ IP 地址匿名化
- ✅ Cookie 标志设置（GDPR 合规）

---

## Sentry 性能监控

### 1. 快速开始

#### 获取 DSN

1. 访问 [Sentry.io](https://sentry.io/)
2. 创建项目（选择 React）
3. 复制 DSN（格式：`https://xxxxx@o12345.ingest.sentry.io/67890`）

#### 配置环境变量

```bash
VITE_SENTRY_DSN=https://xxxxx@o12345.ingest.sentry.io/67890
VITE_ENABLE_SENTRY=true
VITE_SENTRY_ENVIRONMENT=production
```

#### 初始化

Sentry 会在应用启动时自动初始化（生产环境）。

### 2. 错误追踪

#### 自动捕获的错误

- JavaScript 运行时错误
- 未处理的 Promise 拒绝
- 资源加载失败
- 网络请求错误

#### 手动捕获错误

```typescript
import { captureException, captureMessage } from '@/services/sentry'

try {
  // 可能出错的代码
  riskyOperation()
} catch (error) {
  captureException(error, {
    context: 'user_action',
    userId: '123',
    additionalInfo: '...'
  })
}

// 捕获消息
captureMessage('Something important happened', 'info', {
  page: window.location.pathname
})
```

### 3. 性能监控

#### Web Vitals 追踪

Sentry 自动追踪以下 Core Web Vitals：

- **LCP** (Largest Contentful Paint): 最大内容绘制时间
- **FID** (First Input Delay): 首次输入延迟
- **CLS** (Cluster Layout Shift): 累积布局偏移

#### 自定义性能追踪

```typescript
import { startSpan } from '@/services/sentry'

// 追踪操作性能
startSpan('expensive_operation', 'task', (span) => {
  // 执行耗时操作
  performExpensiveOperation()
})
```

### 4. 会话回放

Sentry Replay 自动记录用户会话，帮助调试问题：

- 记录用户操作路径
- 捕获错误发生时的上下文
- 重现用户遇到的问题

### 5. 数据查看

#### Sentry Dashboard

1. 访问 [Sentry.io](https://sentry.io/)
2. 选择项目
3. 查看：
   - **Issues**: 错误列表和详情
   - **Performance**: 性能指标和事务
   - **Releases**: 版本发布和错误统计
   - **Replays**: 会话回放记录

#### 关键指标

- **错误率**: 错误发生频率
- **P95 延迟**: 95% 请求的响应时间
- **吞吐量**: 每秒请求数
- **Apdex 分数**: 应用性能指数

---

## 用户行为分析

### 1. 功能概述

用户行为分析系统提供自定义的事件追踪和会话管理，补充 GA4 的数据。

### 2. 使用方式

```typescript
import { startTracking, trackEvent, trackPerformance, trackError } from '@/services/userAnalytics'

// 开始追踪
startTracking('user-123')

// 追踪事件
trackEvent('search_performed', 'search', {
  query: 'Bitcoin',
  type: 'quick',
  resultCount: 10
})

// 追踪性能
trackPerformance('api_response_time', 500, 'ms')

// 追踪错误
trackError(new Error('Something went wrong'), {
  context: 'search'
})
```

### 3. 会话管理

系统自动管理用户会话：

- 会话 ID 生成和管理
- 会话超时检测（30 分钟）
- 会话事件记录
- 会话数据导出

### 4. 事件类型

| 事件类型 | 说明 | 示例 |
|----------|------|------|
| `page_view` | 页面浏览 | 路由导航 |
| `search` | 搜索操作 | Quick Chat, Deep Research |
| `interaction` | 用户交互 | 点击、输入 |
| `performance` | 性能指标 | 加载时间、响应时间 |
| `error` | 错误事件 | JavaScript 错误 |
| `engagement` | 参与度指标 | 滚动深度、停留时间 |
| `feature_usage` | 功能使用 | 功能点击、使用频率 |

---

## 性能指标说明

### Core Web Vitals

#### Largest Contentful Paint (LCP)

**目标**: < 2.5 秒

测量页面主要内容加载完成的时间。

- **良好**: < 2.5 秒
- **需要改进**: 2.5 - 4.0 秒
- **差**: > 4.0 秒

#### First Input Delay (FID)

**目标**: < 100 毫秒

测量用户首次与页面交互到浏览器响应的时间。

- **良好**: < 100 毫秒
- **需要改进**: 100 - 300 毫秒
- **差**: > 300 毫秒

#### Cumulative Layout Shift (CLS)

**目标**: < 0.1

测量页面视觉稳定性。

- **良好**: < 0.1
- **需要改进**: 0.1 - 0.25
- **差**: > 0.25

### 自定义性能指标

- **页面加载时间**: 从请求到页面完全加载
- **首屏渲染时间**: 首次内容绘制时间
- **API 响应时间**: 后端 API 调用耗时
- **资源加载时间**: CSS、JS、图片等资源加载

---

## 告警系统

### 1. 告警规则

系统自动监控以下指标：

- **性能异常**: 页面加载时间 > 3 秒
- **错误率**: 错误率 > 5%
- **API 失败**: API 请求失败率 > 10%
- **用户体验**: Core Web Vitals 超出阈值

### 2. 告警通知

告警将通过以下渠道发送：

- **Sentry**: 自动创建 Issue
- **Slack** (可选): 发送到指定频道
- **邮件** (可选): 发送到指定邮箱

### 3. 配置告警

告警规则在 `frontend/src/services/alertManager.ts` 中配置。可以自定义：

- 告警阈值
- 告警条件
- 通知渠道
- 冷却时间

---

## 常见问题排查

### 1. GA4 数据未显示

**可能原因**:
- Measurement ID 未配置
- 用户未同意数据收集
- 浏览器阻止了 GA4 脚本

**解决方法**:
1. 检查环境变量 `VITE_GA_MEASUREMENT_ID` 是否正确
2. 检查用户是否已同意数据收集
3. 检查浏览器控制台是否有错误
4. 使用 GA4 DebugView 实时查看事件

### 2. Sentry 错误未上报

**可能原因**:
- DSN 未配置
- 开发环境默认禁用 Sentry
- 网络问题

**解决方法**:
1. 检查环境变量 `VITE_SENTRY_DSN` 是否正确
2. 确认 `VITE_ENABLE_SENTRY=true`
3. 检查浏览器网络请求是否成功
4. 查看 Sentry 控制台是否有配额限制

### 3. 性能指标异常

**可能原因**:
- 第三方脚本加载慢
- API 响应慢
- 资源文件过大

**解决方法**:
1. 检查 Network 面板查看资源加载时间
2. 使用 Performance 面板分析性能瓶颈
3. 检查 API 响应时间
4. 优化代码分割和懒加载

### 4. 用户行为数据缺失

**可能原因**:
- 追踪未初始化
- 事件未正确触发
- 数据延迟

**解决方法**:
1. 检查 `startTracking()` 是否已调用
2. 验证事件是否正确触发
3. 检查 GA4 实时报告（数据可能有延迟）

---

## 最佳实践

### 1. 事件命名规范

- 使用小写字母和下划线
- 使用动词 + 名词格式：`click_button`, `search_performed`
- 保持一致的命名风格

### 2. 性能优化

- 异步加载监控脚本
- 批量发送事件
- 使用采样率减少数据量

### 3. 隐私保护

- 始终获取用户同意
- 不收集敏感信息
- 定期审查数据收集需求

### 4. 监控维护

- 定期检查监控系统健康状态
- 审查告警规则和阈值
- 清理过期数据
- 更新监控配置

---

## 参考资源

- [Google Analytics 4 文档](https://developers.google.com/analytics/devguides/collection/ga4)
- [Sentry React 文档](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Web Vitals 指南](https://web.dev/vitals/)
- [GDPR 合规指南](https://gdpr.eu/)

---

**最后更新**: 2025-01-27

