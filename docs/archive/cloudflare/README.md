# Cloudflare Pages 部署文档归档

**归档时间**: 2025-11-05
**状态**: 已废弃

---

## 说明

本目录包含早期尝试使用 Cloudflare Pages 部署前端应用时的文档和配置说明。

由于技术原因，项目最终选择了 **Vercel** 作为前端部署平台，因此这些文档仅作为历史记录保留。

---

## 归档文件

### 1. CLOUDFLARE_DEPLOYMENT.md
完整的 Cloudflare Pages 部署指南，包括：
- 账户配置
- 项目设置
- 环境变量配置
- 部署流程

### 2. CLOUDFLARE_522_ERROR.md
Cloudflare 522 错误的分析和解决方案

### 3. QUICKSTART_CLOUDFLARE.md
快速开始指南

### 4. CLOUDFLARE_ACCOUNT_ID_GUIDE.md
Cloudflare Account ID 获取指南

---

## 当前部署方案

项目当前使用 **Vercel** 进行前端部署：

- **平台**: Vercel
- **生产URL**: https://web3search.vercel.app
- **部署文档**: 参见项目根目录的 `README.md`

---

## 为什么切换到Vercel？

1. **部署稳定性**: Vercel 提供更稳定的部署体验
2. **集成度更好**: 与 GitHub Actions 集成更简单
3. **性能优秀**: Vercel Edge Network 提供出色的全球访问速度
4. **开发体验**: 更友好的开发者体验和调试工具

---

## 注意事项

- 本目录中的文档仅供参考，不应用于实际部署
- Workers 目录中的 Cloudflare Workers 代码也已废弃
- 所有当前的部署配置请参考项目根目录的文档

---

**文档创建**: 2025-11-05
**最后更新**: 2025-11-05
