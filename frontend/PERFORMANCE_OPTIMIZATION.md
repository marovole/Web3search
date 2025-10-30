# 前端性能优化工具使用指南

本文档介绍前端性能优化功能和相关工具的使用方法。

## 概述

已实现的前端性能优化功能包括：
- 代码分割和懒加载
- 图片和资源优化
- Bundle分析和优化
- 缓存策略实现
- 性能监控和验证

## 工具列表

### 1. 性能测试工具 (`performanceTester.ts`)

自动测试性能指标是否达到验收标准。

**使用方法：**
```typescript
import performanceTester from './utils/performanceTester'

// 运行所有测试
const results = await performanceTester.runAllTests()

// 验证验收标准
const validation = await performanceTester.validateAcceptanceCriteria()
console.log(validation.summary)
```

### 2. 性能基准线管理器 (`performanceBaselineManager.ts`)

建立和管理性能基准线，用于对比优化效果。

**使用方法：**
```typescript
import performanceBaselineManager from './utils/performanceBaselineManager'

// 建立基准线
await performanceBaselineManager.establishBaseline()

// 对比当前性能
const comparisons = await performanceBaselineManager.compareWithBaseline()
```

### 3. 离线功能测试工具 (`offlineFunctionalityTester.ts`)

测试Service Worker和离线功能。

**使用方法：**
```typescript
import offlineFunctionalityTester from './utils/offlineFunctionalityTester'

// 运行所有测试
const results = await offlineFunctionalityTester.runAllTests()
```

### 4. 性能验证工具 (`performanceValidator.ts`)

综合验证所有性能优化效果。

**使用方法：**
```typescript
import performanceValidator from './utils/performanceValidator'

// 运行完整验证
const validation = await performanceValidator.runFullValidation()
```

## 开发环境自动测试

在开发环境中，这些工具会在页面加载后10秒自动运行。

## 性能预算

默认性能预算配置：
- Bundle大小: 500KB (警告: 400KB)
- 加载时间: 3000ms (警告: 2000ms)
- LCP: 4000ms (警告: 2500ms)
- FID: 300ms (警告: 100ms)
- CLS: 0.25 (警告: 0.1)

