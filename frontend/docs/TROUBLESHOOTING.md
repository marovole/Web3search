# 问题排查手册

Web3Search 前端监控和安全系统问题排查指南。

## 目录

1. [监控数据缺失](#监控数据缺失)
2. [Sentry 错误上报失败](#sentry-错误上报失败)
3. [CSP 违规问题](#csp-违规问题)
4. [性能问题诊断](#性能问题诊断)
5. [常见错误和解决方案](#常见错误和解决方案)

---

## 监控数据缺失

### 问题：GA4 数据未显示

#### 症状
- GA4 控制台没有数据
- 实时报告显示 0 用户
- 事件未记录

#### 排查步骤

1. **检查环境变量**
   ```bash
   echo $VITE_GA_MEASUREMENT_ID
   ```
   应该显示 `G-XXXXXXXXXX` 格式的 ID

2. **检查用户同意**
   ```javascript
   // 在浏览器控制台检查
   localStorage.getItem('analytics_consent')
   ```
   应该返回 `'true'`

3. **检查 GA4 初始化**
   ```javascript
   // 在浏览器控制台检查
   window.gtag
   window.dataLayer
   ```
   应该存在且为函数/数组

4. **检查网络请求**
   - 打开浏览器 DevTools → Network
   - 筛选 `collect` 或 `google-analytics`
   - 查看是否有请求发送到 GA4

5. **使用 GA4 DebugView**
   - 安装 [GA Debugger](https://chrome.google.com/webstore/detail/google-analytics-debugger)
   - 打开 DebugView 实时查看事件

#### 解决方案

- **环境变量未设置**: 配置 `VITE_GA_MEASUREMENT_ID`
- **用户未同意**: 引导用户接受同意
- **脚本被阻止**: 检查浏览器扩展或 CSP 策略
- **网络问题**: 检查防火墙或代理设置

---

### 问题：用户行为分析数据缺失

#### 症状
- 自定义事件未记录
- 会话数据不完整
- 性能指标缺失

#### 排查步骤

1. **检查追踪是否启动**
   ```javascript
   // 检查 localStorage
   localStorage.getItem('user_session_id')
   ```

2. **检查事件队列**
   ```javascript
   // 在控制台检查
   // 事件应该被添加到队列
   ```

3. **检查错误日志**
   ```javascript
   // 查看浏览器控制台错误
   ```

#### 解决方案

- **追踪未启动**: 调用 `startTracking()`
- **事件格式错误**: 检查事件参数格式
- **队列溢出**: 增加队列大小或刷新频率

---

## Sentry 错误上报失败

### 问题：错误未上报到 Sentry

#### 症状
- Sentry 控制台没有错误
- 浏览器控制台有错误但 Sentry 未捕获
- 手动 `captureException` 无效果

#### 排查步骤

1. **检查环境变量**
   ```bash
   echo $VITE_SENTRY_DSN
   echo $VITE_ENABLE_SENTRY
   ```
   DSN 格式应为 `https://xxx@xxx.ingest.sentry.io/xxx`
   `VITE_ENABLE_SENTRY` 应为 `true`

2. **检查环境**
   ```javascript
   // Sentry 在开发环境默认禁用
   // 检查 process.env.NODE_ENV 或 VITE_ENVIRONMENT
   ```

3. **检查 Sentry 初始化**
   ```javascript
   // 在浏览器控制台检查
   // 应该有初始化日志
   ```

4. **检查网络请求**
   - 打开 DevTools → Network
   - 筛选 `sentry.io`
   - 查看是否有请求发送

5. **检查错误过滤**
   ```javascript
   // 检查 beforeSend 过滤器
   // 某些错误可能被过滤
   ```

#### 解决方案

- **DSN 未设置**: 配置 `VITE_SENTRY_DSN`
- **开发环境禁用**: 设置 `VITE_ENABLE_SENTRY=true` 强制启用
- **网络阻止**: 检查防火墙或代理
- **错误被过滤**: 检查 `beforeSend` 过滤逻辑
- **配额耗尽**: 检查 Sentry 配额限制

---

### 问题：性能数据缺失

#### 症状
- Performance 面板无数据
- Web Vitals 未记录
- 事务追踪缺失

#### 排查步骤

1. **检查采样率**
   ```javascript
   // 检查 tracesSampleRate 配置
   // 生产环境可能设置为 0.1 (10%)
   ```

2. **检查性能监控启动**
   ```javascript
   // 确认性能监控已启用
   ```

3. **检查 Performance API**
   ```javascript
   // 在控制台检查
   window.performance
   performance.getEntriesByType('navigation')
   ```

#### 解决方案

- **采样率过低**: 临时提高采样率测试
- **性能监控未启用**: 检查配置
- **浏览器不支持**: 检查浏览器兼容性

---

## CSP 违规问题

### 问题：资源被 CSP 阻止

#### 症状
- 脚本无法加载
- 样式不生效
- 图片无法显示
- 控制台 CSP 违规错误

#### 排查步骤

1. **检查 CSP 违规报告**
   ```javascript
   // 监听违规事件
   document.addEventListener('securitypolicyviolation', (e) => {
     console.log('CSP Violation:', e)
   })
   ```

2. **检查被阻止的资源**
   - 查看浏览器控制台错误
   - 查看 Network 面板失败请求
   - 查看 CSP 违规报告

3. **检查 CSP 策略**
   ```javascript
   // 检查当前 CSP
   // 在 DevTools → Application → Cookies → 查看响应头
   ```

#### 解决方案

- **脚本被阻止**: 添加脚本源到 `script-src`
- **样式被阻止**: 添加样式源到 `style-src`
- **图片被阻止**: 添加图片源到 `img-src`
- **字体被阻止**: 添加字体源到 `font-src`

**示例修复**:
```javascript
// 修改 CSP 策略
const csp = `script-src 'self' https://cdn.example.com; style-src 'self' 'unsafe-inline';`
```

---

### 问题：CSP 违规报告过多

#### 症状
- Sentry 中大量 CSP 违规报告
- 性能影响
- 日志噪音

#### 解决方案

1. **修复违规源**
   - 分析违规报告
   - 添加必要的源到 CSP
   - 移除不必要的内联脚本

2. **使用 nonce**
   - 为内联脚本生成 nonce
   - 在 CSP 中包含 nonce

3. **过滤噪声**
   - 过滤已知的第三方违规
   - 使用 CSP 报告端点聚合

---

## 性能问题诊断

### 问题：页面加载慢

#### 排查步骤

1. **检查 Network 面板**
   - 查看资源加载时间
   - 识别慢资源
   - 检查资源大小

2. **检查 Performance 面板**
   - 录制性能分析
   - 查看主线程活动
   - 识别性能瓶颈

3. **检查监控开销**
   ```javascript
   // 检查监控脚本加载时间
   performance.getEntriesByType('resource')
     .filter(r => r.name.includes('analytics') || r.name.includes('sentry'))
   ```

#### 解决方案

- **资源过大**: 启用代码分割和懒加载
- **监控脚本慢**: 异步加载监控脚本
- **第三方脚本慢**: 延迟加载非关键脚本
- **API 响应慢**: 优化后端或使用缓存

---

### 问题：监控影响性能

#### 症状
- 页面加载时间增加
- 交互延迟
- 性能指标异常

#### 排查步骤

1. **测量监控开销**
   ```javascript
   // 测量监控初始化时间
   const start = performance.now()
   // 初始化监控
   const end = performance.now()
   console.log('Monitoring overhead:', end - start)
   ```

2. **检查采样率**
   ```javascript
   // 检查是否有过高的采样率
   ```

3. **检查事件频率**
   ```javascript
   // 检查是否发送过多事件
   ```

#### 解决方案

- **降低采样率**: 调整 Sentry 采样率
- **批量事件**: 批量发送事件减少请求
- **延迟加载**: 延迟非关键监控初始化
- **优化代码**: 优化监控代码性能

---

## 常见错误和解决方案

### 错误：`gtag is not defined`

**原因**: Google Analytics 未初始化

**解决方案**:
```javascript
// 检查 Measurement ID
if (!import.meta.env.VITE_GA_MEASUREMENT_ID) {
  console.warn('GA Measurement ID not configured')
}

// 检查用户同意
if (!localStorage.getItem('analytics_consent')) {
  // 请求用户同意
}
```

---

### 错误：`Sentry is not initialized`

**原因**: Sentry 未正确初始化

**解决方案**:
```javascript
// 检查 DSN
if (!import.meta.env.VITE_SENTRY_DSN) {
  console.warn('Sentry DSN not configured')
}

// 检查环境
if (import.meta.env.DEV) {
  // 开发环境可能禁用 Sentry
}
```

---

### 错误：CSP 违规 `script-src`

**原因**: 脚本源不在 CSP 白名单

**解决方案**:
```javascript
// 添加脚本源到 CSP
// 或使用 nonce
const nonce = generateNonce()
const csp = `script-src 'self' 'nonce-${nonce}'`
```

---

### 错误：`localStorage is not available`

**原因**: 隐私模式或存储限制

**解决方案**:
```javascript
// 检查存储可用性
try {
  localStorage.setItem('test', 'test')
  localStorage.removeItem('test')
} catch (e) {
  // 使用内存存储降级
}
```

---

## 调试技巧

### 1. 启用调试模式

```javascript
// GA4 调试
localStorage.setItem('ga_debug', 'true')

// Sentry 调试
localStorage.setItem('sentry_debug', 'true')
```

### 2. 查看监控数据

```javascript
// 查看 GA4 dataLayer
console.log(window.dataLayer)

// 查看 Sentry 事件
// 在 Sentry Dashboard 查看
```

### 3. 模拟事件

```javascript
// 手动触发 GA4 事件
window.gtag('event', 'test_event', {
  event_category: 'test',
  event_label: 'manual_test'
})

// 手动捕获 Sentry 错误
captureException(new Error('Test error'))
```

---

## 联系支持

如果问题仍未解决：

1. 查看相关文档
2. 检查 GitHub Issues
3. 联系开发团队

---

**最后更新**: 2025-01-27

