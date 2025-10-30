# 安全配置指南

Web3Search 前端应用的安全配置和维护指南。

## 目录

1. [安全系统概览](#安全系统概览)
2. [CSP 策略配置](#csp-策略配置)
3. [安全头部配置](#安全头部配置)
4. [XSS 防护](#xss-防护)
5. [依赖安全管理](#依赖安全管理)
6. [安全更新和维护](#安全更新和维护)

---

## 安全系统概览

### 安全架构

```
┌─────────────────────┐
│   Frontend App      │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼────────┐
│  CSP   │   │  Security  │
│Manager │   │  Headers   │
└───┬────┘   └───┬────────┘
    │            │
┌───▼────────────▼───┐
│  XSS Protection    │
│  & Input Sanitize  │
└──────────┬─────────┘
           │
    ┌──────▼──────┐
    │ Dependency  │
    │  Security   │
    └─────────────┘
```

### 安全组件

| 组件 | 功能 | 防护范围 |
|------|------|----------|
| **CSP** | 内容安全策略 | XSS、数据注入、代码注入 |
| **安全头部** | HTTP 安全头部 | 点击劫持、MIME 嗅探、HTTPS 强制 |
| **XSS 防护** | 输入验证和清理 | DOM XSS、存储型 XSS、反射型 XSS |
| **依赖安全** | 依赖漏洞扫描 | 已知漏洞、许可证合规 |

---

## CSP 策略配置

### 1. 默认 CSP 策略

应用使用以下默认 CSP 策略：

```javascript
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data: https:;
connect-src 'self' https://web3search-api.onrender.com;
frame-src 'none';
object-src 'none';
base-uri 'self';
form-action 'self';
frame-ancestors 'none';
upgrade-insecure-requests;
block-all-mixed-content;
```

### 2. CSP 配置方式

#### 方式 1: Meta 标签（当前使用）

CSP 通过 `<meta>` 标签注入到 HTML：

```html
<meta http-equiv="Content-Security-Policy" content="...">
```

#### 方式 2: HTTP 响应头（推荐）

在生产环境中，建议通过服务器设置 CSP 响应头：

```nginx
# Nginx 配置示例
add_header Content-Security-Policy "default-src 'self'; ..." always;
```

```javascript
// Vercel 配置 (vercel.json)
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; ..."
        }
      ]
    }
  ]
}
```

### 3. CSP 指令说明

| 指令 | 说明 | 示例值 |
|------|------|--------|
| `default-src` | 默认资源源 | `'self'` |
| `script-src` | JavaScript 源 | `'self' 'unsafe-inline'` |
| `style-src` | CSS 源 | `'self' 'unsafe-inline'` |
| `img-src` | 图片源 | `'self' data: https:` |
| `connect-src` | 网络请求源 | `'self' https://api.example.com` |
| `font-src` | 字体源 | `'self' data: https:` |
| `frame-src` | iframe 源 | `'none'` |
| `object-src` | object/embed 源 | `'none'` |
| `base-uri` | base 标签 URI | `'self'` |
| `form-action` | 表单提交目标 | `'self'` |
| `frame-ancestors` | 嵌入父页面 | `'none'` |

### 4. Nonce-based CSP（推荐）

为了更严格的安全，建议使用 nonce：

```javascript
// 生成 nonce
const nonce = crypto.randomUUID()

// 设置 CSP（包含 nonce）
const csp = `script-src 'self' 'nonce-${nonce}'; style-src 'self' 'nonce-${nonce}';`

// 在脚本标签中使用
<script nonce={nonce}>
  // 内联脚本
</script>
```

### 5. CSP 违规监控

系统自动监控 CSP 违规：

```javascript
// 监听违规事件
document.addEventListener('securitypolicyviolation', (event) => {
  // 上报到监控系统
  reportViolation({
    blockedURI: event.blockedURI,
    violatedDirective: event.violatedDirective,
    // ...
  })
})
```

### 6. 渐进式 CSP 实施

1. **报告模式**: 先使用 `Content-Security-Policy-Report-Only`
2. **监控违规**: 收集和分析违规报告
3. **逐步收紧**: 收紧策略并修复问题
4. **强制执行**: 切换到 `Content-Security-Policy`

---

## 安全头部配置

### 1. 必需的安全头部

#### Strict-Transport-Security (HSTS)

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

- 强制使用 HTTPS
- 有效期 1 年
- 包含子域名
- 支持浏览器预加载列表

#### X-Frame-Options

```http
X-Frame-Options: DENY
```

- 防止点击劫持
- 不允许在任何框架中嵌入

#### X-Content-Type-Options

```http
X-Content-Type-Options: nosniff
```

- 防止 MIME 类型嗅探
- 强制浏览器使用 Content-Type 头部

#### Referrer-Policy

```http
Referrer-Policy: strict-origin-when-cross-origin
```

- 控制引用信息泄露
- 同源时发送完整 URL，跨域时仅发送源

#### Permissions-Policy

```http
Permissions-Policy: geolocation=(), microphone=(), camera=(), ...
```

- 控制浏览器功能权限
- 禁用不需要的功能

### 2. Vercel 配置

在 `vercel.json` 中配置：

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains; preload"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Permissions-Policy",
          "value": "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()"
        }
      ]
    }
  ]
}
```

### 3. 安全头部验证

使用在线工具验证：

- [SecurityHeaders.com](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)

---

## XSS 防护

### 1. 输入验证

#### 文本输入

```typescript
import { sanitizeInput } from '@/services/xssProtection'

// 清理用户输入
const cleanInput = sanitizeInput(userInput)
```

#### HTML 输入

```typescript
import { sanitizeHTML } from '@/services/xssProtection'

// 清理 HTML 内容
const cleanHTML = sanitizeHTML(dirtyHTML)
```

### 2. 输出编码

#### React 自动转义

React 默认转义所有内容：

```tsx
// ✅ 安全 - React 自动转义
<div>{userInput}</div>

// ❌ 危险 - 直接使用 innerHTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

#### 安全渲染 HTML

如果必须渲染 HTML，使用清理函数：

```tsx
import { sanitizeHTML } from '@/services/xssProtection'

const cleanHTML = sanitizeHTML(userContent)
<div dangerouslySetInnerHTML={{ __html: cleanHTML }} />
```

### 3. DOM 操作安全

```typescript
// ❌ 不安全
element.innerHTML = userInput

// ✅ 安全
element.textContent = userInput

// ✅ 安全（使用清理）
element.innerHTML = sanitizeHTML(userInput)
```

### 4. URL 验证

```typescript
// 验证 URL
function isValidURL(url: string): boolean {
  try {
    const parsed = new URL(url)
    return ['http:', 'https:'].includes(parsed.protocol)
  } catch {
    return false
  }
}
```

---

## 依赖安全管理

### 1. 依赖扫描

#### 自动扫描

运行安全审计脚本：

```bash
npm run security:audit
```

#### 手动扫描

```bash
npm audit
npm audit --json > audit-report.json
```

### 2. 漏洞修复

#### 自动修复

```bash
npm audit fix
```

#### 手动修复

1. 查看漏洞详情：`npm audit`
2. 更新受影响包：`npm update package-name`
3. 验证修复：`npm audit`

### 3. 许可证检查

检查依赖许可证：

```bash
# 使用 license-checker
npx license-checker --summary
```

### 4. CI/CD 集成

在 CI/CD 流程中添加安全检查：

```yaml
# GitHub Actions 示例
- name: Security Audit
  run: |
    npm audit --audit-level=high
    npm run security:audit
```

---

## 安全更新和维护

### 1. 定期更新

#### 依赖更新

```bash
# 检查过时包
npm outdated

# 更新到最新版本
npm update

# 更新主要版本（谨慎）
npm install package@latest
```

#### 安全补丁

```bash
# 自动应用安全补丁
npm audit fix

# 强制更新（谨慎）
npm audit fix --force
```

### 2. 安全监控

#### 监控工具

- **Snyk**: 持续监控依赖漏洞
- **Dependabot**: GitHub 自动更新依赖
- **npm audit**: npm 内置安全审计

#### 告警配置

配置自动告警：

- 发现高风险漏洞时通知
- 依赖更新时通知
- 许可证变更时通知

### 3. 安全审查清单

定期检查：

- [ ] 依赖是否有已知漏洞
- [ ] CSP 策略是否有效
- [ ] 安全头部是否配置正确
- [ ] XSS 防护是否到位
- [ ] 输入验证是否完整
- [ ] 权限控制是否合理

### 4. 应急响应

发现安全漏洞时：

1. **立即评估**: 确定漏洞严重性
2. **临时修复**: 应用临时缓解措施
3. **永久修复**: 更新依赖或修复代码
4. **验证**: 确认修复有效
5. **部署**: 部署修复到生产环境
6. **监控**: 持续监控异常

---

## 最佳实践

### 1. 安全编码

- ✅ 始终验证和清理用户输入
- ✅ 使用参数化查询（后端）
- ✅ 避免使用 `eval()` 和 `innerHTML`
- ✅ 使用 HTTPS 传输敏感数据
- ✅ 实施最小权限原则

### 2. 安全配置

- ✅ 使用严格的 CSP 策略
- ✅ 配置所有安全头部
- ✅ 启用 HTTPS 强制
- ✅ 定期更新依赖
- ✅ 监控安全事件

### 3. 安全测试

- ✅ 定期进行安全审计
- ✅ 使用安全扫描工具
- ✅ 进行渗透测试
- ✅ 代码安全审查

---

## 参考资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Snyk 安全资源](https://snyk.io/learn/)

---

**最后更新**: 2025-01-27

