# GitHub Actions Workflows - Disabled

## 禁用原因

这些工作流已被禁用，以避免 GitHub Actions 的使用限制和潜在账单问题。

## 替代方案

我们现在使用以下**免费**的 CI/CD 解决方案：

### 1. Cloudflare Workers & Pages (推荐)

**Workers API 部署**:
```bash
cd workers-api
npx wrangler deploy
```

**Frontend 部署**:
- 自动部署: 在 Cloudflare Dashboard 配置 Git 集成
- 手动部署: `cd frontend && npx wrangler pages deploy dist`

### 2. Render (Backend)

Backend 使用 Render 的 Git 自动部署（免费层）:
- 每次 push 到 main 分支自动部署
- Dashboard: https://dashboard.render.com

## 已备份的工作流

- `ci.yml` - CI/CD Pipeline
- `deploy.yml` - Multi-Environment Deployment
- `integration-tests.yml` - Integration Tests
- `performance.yml` - Performance Testing
- `smoke-tests.yml` - Smoke Tests

## 如需恢复

如果将来需要重新启用 GitHub Actions:

```bash
mv .github/workflows-disabled/*.yml .github/workflows/
git add .github/workflows/
git commit -m "chore: 重新启用 GitHub Actions"
git push
```

## 部署文档

详见项目根目录的部署文档和 OpenSpec 变更提案。

---

**禁用日期**: 2025-11-14
**原因**: 避免 GitHub Actions 使用限制
**替代方案**: Cloudflare 原生部署 + Render Git 集成
