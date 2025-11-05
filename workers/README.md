# Cloudflare Workers - 已废弃

⚠️ **重要提示：此目录已废弃，不再维护**

---

## 状态

- **当前状态**: 已废弃
- **废弃时间**: 2025-11-05
- **原因**: 项目改用 Vercel 部署，不再需要 Cloudflare Workers 作为 API 代理

---

## 背景

此目录原本包含用于 Cloudflare Workers 的 API 代理代码，主要功能包括：

1. **API 代理**: 将前端请求代理到后端 API
2. **边缘缓存**: 在 Cloudflare Edge 节点缓存 API 响应
3. **速率限制**: 实现基本的速率限制功能

---

## 为什么废弃？

项目最终选择使用 **Vercel** 进行前端部署，原因包括：

1. **简化架构**: Vercel 可以直接配置 API 代理，无需额外的 Workers 层
2. **开发体验**: Vercel 提供更好的开发者体验和调试工具
3. **部署稳定性**: Vercel 的部署流程更稳定可靠
4. **成本效益**: 免费计划已满足需求

---

## 当前方案

### 前端部署
- **平台**: Vercel
- **URL**: https://web3search.vercel.app
- **API代理**: 通过 `vercel.json` 配置

### 后端API
- **平台**: Render
- **URL**: https://web3search-api.onrender.com
- **CORS**: 直接配置支持前端域名

---

## 相关文档

- Cloudflare 相关文档已归档至: `docs/archive/cloudflare/`
- 当前部署文档请参考项目根目录的 `README.md`

---

## 代码保留原因

此目录的代码被保留仅用于：
- 历史参考
- 学习 Cloudflare Workers 的示例
- 未来可能的技术评估

**请勿在生产环境使用此代码。**

---

**废弃时间**: 2025-11-05
**最后更新**: 2025-11-05
