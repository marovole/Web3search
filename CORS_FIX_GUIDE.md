# CORS 问题修复指南

**问题**: 前端无法调用后端 API，被 CORS 策略阻止  
**时间**: 2025-11-08  
**状态**: 🔴 待修复

---

## 🔍 问题诊断

### 测试结果

**OPTIONS 预检请求**:
```bash
curl -X OPTIONS -H "Origin: https://web3search.pages.dev" \
  -I https://web3search-api.onrender.com/api/v1/trending/hotspots
```

**返回的头部**:
```
HTTP/2 400
access-control-allow-credentials: true
access-control-allow-headers: Accept, Accept-Language, Authorization...
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
access-control-max-age: 600
```

**关键发现**: ❌ **缺少 `Access-Control-Allow-Origin` 头部**

---

## 🎯 根本原因

CORS 中间件正在工作，但**没有返回 `Access-Control-Allow-Origin` 头部**。

这意味着：**请求的 Origin (`https://web3search.pages.dev`) 不在后端的 CORS 白名单中！**

虽然代码中已经添加了域名，但**运行时的环境变量可能没有更新**。

---

## ✅ 解决方案

### 步骤 1: 更新 Render 环境变量

这是**最关键的步骤**！

1. **登录 Render Dashboard**
   - URL: https://dashboard.render.com/
   - 选择服务: `web3search-api`

2. **进入环境变量设置**
   - 点击左侧菜单 "Environment"
   - 或者 Settings → Environment Variables

3. **查找 `CORS_ORIGINS` 变量**
   
   **情况 A: 变量已存在**
   - 点击 "Edit" 编辑
   - 检查当前值
   
   **情况 B: 变量不存在**
   - 点击 "Add Environment Variable"
   - Key: `CORS_ORIGINS`

4. **设置正确的值**
   
   **推荐配置** (包含所有部署平台):
   ```
   https://web3search.pages.dev,https://web3-search.netlify.app,https://web3search.vercel.app,https://web3search.ai,https://www.web3search.ai
   ```
   
   **最小配置** (仅 Cloudflare Pages):
   ```
   https://web3search.pages.dev
   ```

5. **保存并重启**
   - 点击 "Save Changes"
   - Render 会自动重启服务 (等待 2-3 分钟)

---

### 步骤 2: 验证修复

**等待服务重启后 (约 2-3 分钟)**，运行以下测试：

**测试 1: OPTIONS 预检请求**
```bash
curl -X OPTIONS \
  -H "Origin: https://web3search.pages.dev" \
  -H "Access-Control-Request-Method: GET" \
  -I https://web3search-api.onrender.com/api/v1/trending/hotspots
```

**预期结果** (必须包含):
```
Access-Control-Allow-Origin: https://web3search.pages.dev  ← 必须有这个！
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

**测试 2: 实际 GET 请求**
```bash
curl -X GET \
  -H "Origin: https://web3search.pages.dev" \
  -I https://web3search-api.onrender.com/api/v1/trending/hotspots?limit=10
```

**预期结果** (必须包含):
```
HTTP/2 200  ← 或者其他非 404 的状态码
Access-Control-Allow-Origin: https://web3search.pages.dev  ← 必须有这个！
```

**测试 3: 浏览器测试**
1. 打开 https://web3search.pages.dev/
2. 打开浏览器开发者工具 (F12)
3. 查看 Console 标签
4. 应该**不再有** CORS 错误
5. 查看 Network 标签
6. API 请求应该返回 200 状态码

---

### 步骤 3: 检查部署日志

如果修复后仍有问题：

1. **在 Render Dashboard 查看日志**
   - 点击 "Logs" 标签
   - 搜索 "CORS"
   - 查找配置加载信息

2. **查找配置日志**
   ```
   应该看到类似:
   CORS origins: ['https://web3search.pages.dev', ...]
   ```

3. **查找错误**
   ```
   如果有错误会显示:
   ValueError: 生产环境必须配置具体的生产域名
   ```

---

## 🔧 替代方案

### 方案 A: 手动重启服务

如果更新环境变量后服务没有自动重启：

1. 在 Render Dashboard 中点击 "Manual Deploy"
2. 选择 "Clear build cache & deploy"
3. 等待部署完成 (约 3-5 分钟)

### 方案 B: 使用 Cloudflare Pages Functions

如果后端 CORS 无法修复，可以使用我们已经创建的代理：

文件 `frontend/functions/_middleware.ts` 已经配置为代理 `/api/*` 请求到后端。

确认 Cloudflare Pages 已部署此文件。

### 方案 C: 临时禁用 CORS 验证（仅用于测试）

**⚠️ 不推荐用于生产环境**

可以临时设置 `CORS_ORIGINS=*` 来测试是否是 CORS 配置问题。

---

## 📊 当前配置状态

### 代码层面 ✅

**文件**: `backend/app/core/config.py` (第 109-116 行)

```python
production_domains = [
    'web3search.ai',           # 主域名
    'www.web3search.ai',       # WWW 子域名
    'api.web3search.ai',       # API 子域名
    'web3search.vercel.app',   # Vercel 前端部署域名
    'web3search.pages.dev',    # Cloudflare Pages 前端部署域名 ✅
    'web3-search.netlify.app'  # Netlify 前端部署域名
]
```

**文件**: `backend/app/main.py` (第 501-526 行)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # ✅ 使用配置的白名单
    allow_origin_regex=None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[...],
    expose_headers=["X-Total-Count", "X-Page-Count"],
    max_age=600,
)
```

✅ 代码配置正确

### 运行时配置 ❌

**问题**: Render 环境变量 `CORS_ORIGINS` 可能：
- 不存在
- 值为空
- 不包含 `https://web3search.pages.dev`
- 包含旧的配置

❌ 需要手动更新

---

## 🎯 验证清单

修复后检查以下项目：

- [ ] Render 环境变量 `CORS_ORIGINS` 已更新
- [ ] 值包含 `https://web3search.pages.dev`
- [ ] 服务已重启 (检查 Logs 中的启动时间)
- [ ] OPTIONS 请求返回 `Access-Control-Allow-Origin` 头部
- [ ] GET 请求返回 `Access-Control-Allow-Origin` 头部
- [ ] 浏览器控制台无 CORS 错误
- [ ] 前端市场热点可以加载
- [ ] 前端搜索自动完成可以工作

---

## 📝 常见问题

### Q1: 更新环境变量后仍然有 CORS 错误？

**A**: 
1. 等待 2-3 分钟让服务完全重启
2. 清除浏览器缓存 (Cmd+Shift+R / Ctrl+Shift+R)
3. 检查 Render 日志确认新配置已加载
4. 手动触发重新部署

### Q2: 为什么代码中已经添加了域名，但还需要设置环境变量？

**A**: 
代码中的 `production_domains` 列表用于**验证**环境变量中的域名是否安全。

实际的 CORS 白名单来自环境变量 `CORS_ORIGINS`。

流程：
1. 读取环境变量 `CORS_ORIGINS`
2. 验证是否包含 `production_domains` 中的域名
3. 如果验证通过，使用环境变量的值作为白名单
4. 如果验证失败，服务启动失败

### Q3: 如何确认环境变量已生效？

**A**:
查看 Render 日志，应该看到：
```
INFO:     Application startup complete.
```

如果有错误会显示：
```
ValueError: 生产环境必须配置具体的生产域名，当前配置: [...]
```

### Q4: 能否直接修改代码而不用环境变量？

**A**:
可以，但**不推荐**。环境变量的好处：
- 不同环境可以有不同配置
- 不需要重新构建代码
- 更安全（不暴露在代码仓库中）

如果一定要硬编码，可以修改 `config.py`:
```python
CORS_ORIGINS: str = Field(
    default="https://web3search.pages.dev,https://web3search.ai",  # 硬编码
    description="允许的CORS来源"
)
```

---

## 🎊 预期结果

修复成功后：

1. **后端响应包含 CORS 头部**
   ```
   Access-Control-Allow-Origin: https://web3search.pages.dev
   Access-Control-Allow-Credentials: true
   ```

2. **前端可以成功调用 API**
   - 市场热点数据正常加载
   - 搜索自动完成正常工作
   - 聊天功能可以使用

3. **浏览器控制台清爽**
   - 无 CORS 错误
   - 无 Network Error
   - API 请求返回 200

---

## 📞 需要帮助？

如果按照本指南操作后仍有问题，请提供：

1. Render 环境变量 `CORS_ORIGINS` 的当前值
2. Render 日志中的相关错误信息
3. curl 测试的完整输出
4. 浏览器控制台的错误截图

---

**最后更新**: 2025-11-08  
**下一步**: 在 Render Dashboard 中更新 `CORS_ORIGINS` 环境变量
