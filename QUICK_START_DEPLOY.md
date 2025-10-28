# 🚀 快速部署指南 - 5 分钟概览

**目标**: 在 45 分钟内将系统部署到 Render.com Staging

**最推荐的文档**: `STAGING_DEPLOYMENT_CHECKLIST.md` ← 直接使用此文件

---

## ⚡ 极速导航

### 我是谁? 选择你的路径

#### 路径 1️⃣: "我只想快速部署"
```
打开并跟随: STAGING_DEPLOYMENT_CHECKLIST.md
时间: 45 分钟
```

#### 路径 2️⃣: "我想了解部署的细节"
```
1. 先读: PHASE_4_3_SUMMARY.md (了解背景)
2. 再读: RENDER_DEPLOYMENT_GUIDE.md (详细步骤)
3. 最后: STAGING_DEPLOYMENT_CHECKLIST.md (执行)
时间: 90 分钟
```

#### 路径 3️⃣: "出现了错误，我需要帮助"
```
1. 打开: STAGING_DEPLOYMENT_CHECKLIST.md 的"故障排查"部分
2. 参考: RENDER_DEPLOYMENT_GUIDE.md 的"常见问题解决"部分
```

---

## 📋 30 秒快速检查

**部署前，确保你有:**

- [ ] Render.com 账户 (https://render.com)
- [ ] OpenRouter API Key (https://openrouter.ai)
- [ ] GitHub 账户已连接到 Render
- [ ] 本地代码已推送到 GitHub main 分支

✅ 都有了? 开始部署!

---

## 🎬 5 步快速部署流程

### 步骤 1: 创建 Blueprint (5 分钟)
```
Render 仪表板 → New → Blueprint → GitHub
连接 "Web3search" 仓库 → 点击 "Create Resource"
```

### 步骤 2: 监控部署 (10 分钟)
```
查看 "Deployments" 标签
等待状态变为 "Live" (绿色)
```

### 步骤 3: 配置环境变量 (5 分钟)
```
找到 "web3search-api" 服务
Environment 标签 → Add Environment Variable:
  - OPENROUTER_API_KEY: (你的 API key)
```

### 步骤 4: 快速验证 (10 分钟)
```
访问: https://web3search-xxx.onrender.com/health
应该返回: {"status": "healthy"}
```

### 步骤 5: PDF 测试 (15 分钟) 🔑
```
导出 PDF 报告
打开 PDF 验证中文字体是否正确显示
```

✅ 全部完成!

---

## 📚 文档速查表

| 需求 | 文档 | 时间 |
|------|------|------|
| 快速行动 | STAGING_DEPLOYMENT_CHECKLIST.md | 45 分钟 |
| 完整指南 | RENDER_DEPLOYMENT_GUIDE.md | 60 分钟 |
| 背景信息 | PHASE_4_3_SUMMARY.md | 30 分钟 |
| 资源清单 | PHASE_4_3_COMPLETE.md | 20 分钟 |
| 项目概述 | README.md | 15 分钟 |
| API 文档 | docs/API.md | 30 分钟 |

---

## ⚠️ 3 个关键点

### 1. 不要跳过环境变量配置
```
❌ 错误: 创建了 Blueprint 但没有设置 OPENROUTER_API_KEY
✅ 正确: 立即添加此环境变量
```

### 2. PDF 中文字体是关键验证
```
❌ 错误: PDF 导出成功了，但没验证中文显示
✅ 正确: 打开 PDF 确认中文字体正确显示（不是方块）
```

### 3. 部署需要 15-20 分钟
```
❌ 错误: 创建 Blueprint 后立即检查状态
✅ 正确: 耐心等待 Docker 构建和依赖安装完成
```

---

## 🆘 常见问题秒答

**Q**: 部署失败，显示 "Dockerfile error"?
**A**: 检查 Render 日志，最可能是 WeasyPrint 依赖问题。参考故障排查部分。

**Q**: PDF 中文显示为方块 □?
**A**: 字体未正确加载。检查 Dockerfile 中的 `fc-cache` 命令是否执行。可能需要重新部署。

**Q**: 需要多长时间部署?
**A**: 首次 15-20 分钟（Docker 构建），后续部署更快。

**Q**: 可以用 free 计划吗?
**A**: 可以用于 Staging 验证，但生产建议升级到 starter/standard。

**Q**: 部署失败能回滚吗?
**A**: 可以。在 Render 仪表板的 "Deployments" 中找到之前的版本并点击 "Rollback"。

---

## 🎯 部署成功的样子

### 部署完成
```
✅ web3search-postgres: Available (绿色)
✅ web3search-redis: Available (绿色)
✅ web3search-api: Live (绿色)
```

### 验证通过
```
✅ /health 端点返回 200 OK
✅ Swagger UI 可访问
✅ Quick Chat 在 5 秒内响应
✅ PDF 导出成功
✅ 中文字体正确显示 ← 最关键
✅ 性能指标在目标范围
```

---

## 🚀 开始部署

**现在就开始:**

1. 打开 `STAGING_DEPLOYMENT_CHECKLIST.md`
2. 按照步骤逐一执行
3. 遇到问题查阅详细指南
4. 完成验证后标记完成

**预计时间**: 45 分钟

**祝部署顺利！** 🎉

---

## 📞 需要帮助?

### 问题类型 → 查看文档

| 问题 | 文档 |
|------|------|
| 部署步骤不清楚 | STAGING_DEPLOYMENT_CHECKLIST.md |
| 遇到错误 | RENDER_DEPLOYMENT_GUIDE.md 故障排查 |
| 想了解更多背景 | PHASE_4_3_SUMMARY.md |
| 想看完整资源清单 | PHASE_4_3_COMPLETE.md |
| API 使用问题 | docs/API.md |

---

**最后更新**: 2025-01-28
**作者**: Claude Code
**准备状态**: ✅ 完成
