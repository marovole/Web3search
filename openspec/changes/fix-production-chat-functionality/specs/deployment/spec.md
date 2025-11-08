## MODIFIED Requirements

### Requirement: 生产环境部署验证
系统 **SHALL** 提供生产环境部署状态验证机制，确保前端应用可正常访问和功能完整，**并修复Cloudflare Pages部署配置**。

#### Scenario: 部署状态健康检查
- **WHEN** 用户访问前端应用（https://web3search.pages.dev）
- **THEN** 应用应返回200状态码
- **AND** 所有静态资源（JS, CSS, images）应正确加载
- **AND** JavaScript应用应正常初始化，无控制台错误
- **AND** API代理应正确转发请求到后端（https://web3search-api.onrender.com）
- **AND** React Router路由应正常工作（/history, /watchlist无404）
- **AND** Quick Chat和Deep Research功能完全可用
- **AND** 用户体验应流畅无错误

#### Scenario: Cloudflare Pages部署配置修复
- **WHEN** 部署到Cloudflare Pages生产环境
- **THEN** _redirects 文件应正确配置：
  ```
  # API代理到后端（必须放在最前面）
  /api/v1/*  https://web3search-api.onrender.com/api/v1/:splat  200
  /api/health  https://web3search-api.onrender.com/api/health  200
  /api/docs  https://web3search-api.onrender.com/api/docs  200

  # SPA路由支持（必须放在最后）
  /*  /index.html  200
  ```
- **AND** API代理规则优先级高于SPA路由
- **AND** 代理响应时间开销< 100ms
- **AND** CORS头正确转发到前端
- **AND** 生产环境API请求无404错误

**Rationale**: 修复Cloudflare Pages部署配置，确保API代理和SPA路由都正常工作。

#### Scenario: 生产环境API代理验证
- **WHEN** 访问 https://web3search.pages.dev/api/v1/chat/quick
- **THEN** 请求应代理到 https://web3search-api.onrender.com/api/v1/chat/quick
- **AND** 响应状态码为200或422（取决于请求格式）
- **AND** 响应时间< 3秒
- **AND** CORS头允许web3search.pages.dev域名
- **AND** 响应包含正确的Content-Type（application/json）

#### Scenario: 页面路由SPA支持验证
- **WHEN** 直接访问 https://web3search.pages.dev/history 或刷新页面
- **THEN** Cloudflare Pages应返回 /index.html（200状态）而非404
- **AND** React Router应正确解析路由并渲染History组件
- **AND** 页面应在2秒内完成初始渲染
- **AND** 浏览器后退/前进按钮应正常工作
- **AND** 控制台无"Failed to fetch"或"Chunk load error"

### Requirement: Configuration Error Prevention
The system **SHALL** implement safeguards to prevent API configuration errors in production, **with specific fixes for path duplication issues**.

#### Scenario: Configuration Validation at Startup
- **WHEN** application initializes in production environment
- **THEN** environment configuration shall be validated
- **AND** API_BASE_URL format shall be checked (must be complete URL starting with https://)
- **AND** path duplication patterns shall be detected and prevented
- **AND** validation errors shall be logged with actionable messages
- **AND** validation failures shall block application startup with clear error message

**Rationale**: 建立配置验证机制，在应用启动时检测并防止常见配置错误，特别是路径重复问题。

#### Scenario: Development vs Production Configuration Distinction
- **WHEN** different environments require different API configurations
- **THEN** development environment may use relative paths with proxy (e.g., `/api/v1`)
- **AND** production environment shall always use complete URLs (e.g., `https://api.example.com/api/v1`)
- **AND** configuration logic shall be clear and well-documented
- **AND** examples shall be provided for each environment in documentation
- **AND** a utility function shall detect environment and return appropriate configuration

**Rationale**: 明确不同环境的配置要求，避免开发环境配置模式错误应用到生产环境。

#### Scenario: Production URL Construction Validation
- **WHEN** building API URLs in production environment
- **THEN** API_BASE_URL shall be complete backend URL (https://web3search-api.onrender.com)
- **AND** API endpoints shall be appended without additional path prefixes
- **AND** final URL pattern shall be: `https://web3search-api.onrender.com/api/v1/...`
- **AND** validation shall check for `/api/api` duplication pattern
- **AND** error shall be thrown if duplication is detected

**Rationale**: 明确生产环境URL构建规则，防止路径重复错误。

#### Scenario: Environment Detection Logic
- **WHEN** application loads environment configuration
- **THEN** production environment shall be detected by hostname check (pages.dev, vercel.app, or custom domain)
- **AND** localhost or 127.0.0.1 shall be detected as development environment
- **AND** staging domain shall be detected as staging environment
- **AND** environment detection shall be tested in CI/CD pipeline

### Requirement: Environment Variable Management
The system **SHALL** support deployment across development, staging, and production environments with proper configuration management and **explicit production URL configuration**.

#### Scenario: Production Environment Variable Configuration
- **WHEN** deploying frontend to production environment (Cloudflare Pages)
- **THEN** VITE_API_BASE_URL shall be configured with complete backend URL
- **AND** value shall be explicitly set to `https://web3search-api.onrender.com`
- **AND** VITE_ENVIRONMENT shall be set to `production`
- **AND** configuration shall prevent API path duplication errors
- **AND** build process shall validate environment variables
- **AND** misconfiguration shall fail the build with clear error message

**Rationale**: 修复环境变量配置，确保生产环境使用正确的完整后端URL，而非相对路径或错误的构建逻辑。

#### Scenario: Environment-Specific Configuration Files
- **WHEN** building application for different environments
- **THEN** use appropriate environment file:
  - `.env.development` for local development (API_URL=http://localhost:8000)
  - `.env.staging` for staging (API_URL=https://staging-api.web3search.com)
  - `.env.production` for production (API_URL=https://web3search-api.onrender.com)
- **AND** environment files shall be version controlled (excluding secrets)
- **AND** secrets shall be managed through platform environment variables
- **AND** build process shall explicitly select correct environment file

#### Scenario: Configuration Validation in CI/CD
- **WHEN** CI/CD pipeline runs
- **THEN** validate environment configuration before deployment
- **AND** check API_BASE_URL format in production build
- **AND** verify URL accessibility (smoke test)
- **AND** fail deployment if configuration validation fails
- **AND** provide detailed validation error messages

### Requirement: API Configuration Documentation
The system **SHALL** provide clear documentation for API configuration to prevent future configuration errors.

#### Scenario: API Configuration Documentation
- **WHEN** developers configure deployment environment
- **THEN** clear documentation shall explain API_BASE_URL requirements
- **AND** examples shall show correct vs incorrect configurations
- **AND** common pitfalls shall be highlighted with solutions
- **AND** troubleshooting guide shall cover 404 error scenarios
- **AND** documentation shall include Cloudflare Pages specific configuration

**Rationale**: 通过完善的文档防止类似配置错误再次发生，降低开发者配置难度。

### Requirement: Multi-Platform Deployment Support
The system **SHALL** support deployment across multiple platforms (Vercel, Cloudflare Pages, Netlify) with proper configuration for each platform.

#### Scenario: Cloudflare Pages Deployment Configuration
- **WHEN** deploying to Cloudflare Pages
- **THEN** configuration shall use environment variables from Cloudflare Pages Dashboard
- **AND** build command shall be `npm run build`
- **AND** output directory shall be `dist`
- **AND** _redirects file shall be included in build output
- **AND** environment variables shall be accessible at build time
- **AND** API_BASE_URL shall be set to backend URL

#### Scenario: Vercel Deployment Configuration
- **WHEN** deploying to Vercel
- **THEN** configuration shall use Vercel environment variables
- **AND** build command shall be `npm run build`
- **AND** output directory shall be `dist`
- **AND** rewrites shall proxy `/api` to backend URL
- **AND** API_BASE_URL shall be set to `/api` (for proxy)

#### Scenario: Netlify Deployment Configuration
- **WHEN** deploying to Netlify
- **THEN** configuration shall use Netlify environment variables
- **AND** build command shall be `npm run build`
- **AND** output directory shall be `dist`
- **AND** redirects file shall proxy API requests
- **AND** API_BASE_URL shall be set to backend URL

### Requirement: Monitoring and Observability
The system **SHALL** provide comprehensive monitoring capabilities for the frontend application in production with focus on API connectivity and routing errors.

#### Scenario: API Error Monitoring
- **WHEN** runtime API errors occur in the frontend
- **THEN** errors shall be automatically captured and reported to monitoring service (Sentry)
- **AND** error context shall include: request URL, method, status code, timestamp
- **AND** API error rates shall be tracked by endpoint and error type
- **AND** alerts shall trigger when API error rate exceeds 5% in 5-minute window
- **AND** development team shall be notified of critical API failures

#### Scenario: Routing Error Tracking
- **WHEN** React Router encounters routing errors or page fails to load
- **THEN** error shall be captured with route information
- **AND** 404 errors shall be specifically tracked and alerted
- **AND** failed route loads shall be logged with stack traces
- **AND** routing performance metrics shall be collected

#### Scenario: Performance Degradation Detection
- **WHEN** application performance degrades
- **THEN** monitoring system shall detect increased API response times
- **AND** alerts shall trigger when API latency exceeds 3 seconds
- **AND** slow page loads (>5 seconds) shall be reported
- **AND** bundle size increases shall trigger warnings

### Requirement: Deployment Rollback and Recovery
The system **SHALL** provide automatic rollback capabilities when deployment failures or critical errors are detected.

#### Scenario: Critical Error Detection and Rollback
- **WHEN** smoke tests detect critical failures after deployment (API errors, navigation failures, 404 errors)
- **THEN** deployment shall be automatically flagged as failed
- **AND** previous stable version shall be automatically restored
- **AND** development team shall be notified with failure details
- **AND** incident report shall be generated with logs and error information
- **AND** deployment shall be blocked from proceeding until issues are fixed

#### Scenario: Gradual Rollout with Validation
- **WHEN** deploying new version to production
- **THEN** deploy to small percentage of traffic (10%) initially
- **AND** run comprehensive smoke tests against canary deployment
- **AND** monitor error rates, API response times, and user feedback
- **AND** automatically roll back if error rate exceeds threshold
- **AND** gradually increase traffic if all tests pass (10% → 50% → 100%)
