# 修复生产环境关键问题提案

## Why
基于生产环境功能测试报告，发现了4个关键问题阻碍产品正常发布：
1. 前端部署失败 (P0) - Vercel返回404错误，用户无法访问前端界面
2. Deep Research代码错误 (P1) - TLDRGenerator函数参数不匹配导致功能失效
3. 数据库查询兼容性问题 (P1) - SQLAlchemy版本升级导致查询语法不兼容
4. 外部API依赖问题 (P2) - CoinGecko API访问失败影响Quick Chat功能

这些问题阻止了产品的正常发布，需要立即修复以确保用户体验和系统稳定性。

## What Changes
- **修复前端部署问题**: 检查并修复Vercel部署配置，确保前端可正常访问
- **修复Deep Research功能**: 更新TLDRGenerator调用以匹配正确的函数签名
- **修复数据库查询**: 更新SQL查询语法以兼容新版本SQLAlchemy
- **改进外部API错误处理**: 增强CoinGecko API的错误处理和重试机制

**Impact**: 
- 修复后系统将具备完整的用户访问和核心功能
- 解决P0/P1级阻塞问题，使产品具备发布条件
- 提升系统稳定性和用户体验

## Affected Specs
- deployment (前端部署修复)
- ai-analysis (Deep Research功能修复)
- analytics (数据库查询修复)
- security (外部API错误处理改进)
