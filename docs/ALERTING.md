# 告警配置指南

本文档描述如何为 Web3search 生产环境配置监控告警。

## 概述

Web3search 使用以下监控和告警工具:
- **Sentry**: 错误监控和性能追踪
- **Cloudflare Workers Analytics**: API 性能和使用情况监控
- **Google Analytics**: 用户行为分析

## Sentry 告警配置

### 前提条件

1. 创建 Sentry 项目（如果尚未创建）
2. 获取 SENTRY_DSN
3. 配置环境变量

### 后端配置步骤

1. **启用 Sentry**
   ```bash
   # 在 Render Dashboard 中设置环境变量
   SENTRY_DSN=<your-sentry-dsn>
   ```

2. **配置告警规则**
   - 登录 [Sentry Dashboard](https://sentry.io)
   - 导航到 Project Settings > Alerts
   - 创建以下告警规则:

#### 错误率告警

- **名称**: High Error Rate
- **条件**: 错误率 > 5% (过去 1 小时)
- **操作**: 发送 Slack 通知 / Email
- **严重程度**: Critical

#### 性能降级告警

- **名称**: API Response Time Degradation
- **条件**: P95 响应时间 > 2 秒 (过去 15 分钟)
- **操作**: 发送 Slack 通知
- **严重程度**: Warning

#### 新错误告警

- **名称**: New Error Detected
- **条件**: 首次出现的错误
- **操作**: 发送 Slack 通知
- **严重程度**: Info

### 前端配置步骤

1. **启用 Sentry**
   ```bash
   # frontend/.env.production
   VITE_ENABLE_SENTRY=true
   VITE_SENTRY_DSN=<your-frontend-sentry-dsn>
   ```

2. **配置告警规则** (同后端)

## Cloudflare Workers 告警

### 配置步骤

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 导航到 Workers & Pages > 你的 Worker
3. 点击 "Metrics" tab
4. 点击 "Configure Alerts"

### 推荐告警规则

#### API 延迟告警

- **指标**: CPU Time
- **条件**: P95 > 50ms
- **周期**: 5 分钟
- **操作**: Email notification

#### 错误率告警

- **指标**: Error Rate
- **条件**: > 5%
- **周期**: 5 分钟
- **操作**: Email notification

#### 请求量异常

- **指标**: Request Count
- **条件**: 下降 > 50% 或 上升 > 200%
- **周期**: 15 分钟
- **操作**: Email notification

## Google Analytics 告警

### 配置步骤

1. 登录 [Google Analytics](https://analytics.google.com)
2. 导航到 Admin > Custom Alerts
3. 创建以下告警:

### 推荐告警

#### 流量异常

- **条件**: 日访问量下降 > 30%
- **对比**: 前一周同期
- **通知**: Email

#### 错误页面访问

- **条件**: 404/500 页面访问量上升
- **阈值**: > 100 次/天
- **通知**: Email

## 告警响应流程

### On-Call 通知

1. **Critical 级别**: 立即通知 on-call 工程师
2. **Warning 级别**: 在工作时间内处理
3. **Info 级别**: 记录日志，定期回顾

### 响应步骤

1. **确认告警**
   - 检查 Sentry/Cloudflare Dashboard
   - 验证问题是否真实存在

2. **初步诊断**
   - 查看最近的部署记录
   - 检查相关日志和错误堆栈
   - 确定影响范围

3. **缓解措施**
   - 如果是新部署导致,考虑回滚
   - 如果是外部依赖问题,启用降级模式
   - 通知用户(如果影响严重)

4. **根本原因分析**
   - 问题解决后,进行 RCA (Root Cause Analysis)
   - 更新文档和 runbook
   - 实施预防措施

## 告警配置检查清单

- [ ] Sentry 项目已创建
- [ ] Sentry DSN 已配置(前端 + 后端)
- [ ] Sentry 告警规则已设置
- [ ] Cloudflare Workers 告警已配置
- [ ] Google Analytics 告警已设置
- [ ] Slack/Email 通知已测试
- [ ] On-call 流程已文档化
- [ ] 响应 runbook 已创建

## 注意事项

1. **避免告警疲劳**: 只配置有意义的告警,避免过多噪音
2. **定期回顾**: 每月回顾告警配置,调整阈值
3. **测试告警**: 定期测试告警是否正常触发
4. **文档更新**: 配置变更后及时更新本文档

## 相关文档

- [部署文档](./DEPLOYMENT.md)
- [运维手册](./OPERATIONS.md)
- [故障排查指南](./TROUBLESHOOTING.md)
