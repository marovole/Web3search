# 安全最佳实践

Web3 Search API 安全指南和最佳实践。

## API安全

### 环境变量保护

```bash
# ❌ 错误：硬编码密钥
OPENROUTER_API_KEY = "sk-or-v1-12345"

# ✅ 正确：使用环境变量
from app.core.config import settings
api_key = settings.OPENROUTER_API_KEY

# ✅ 正确：使用密钥管理服务
# Railway/Render自动加密环境变量
```

### 速率限制

```python
# app/api/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/chat/quick-chat")
@limiter.limit("10/minute")  # 每分钟10次
async def quick_chat():
    pass
```

### CORS配置

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web3search.com",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 输入验证

```python
from pydantic import BaseModel, validator, Field

class QuickChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    
    @validator('query')
    def sanitize_query(cls, v):
        # 移除危险字符
        return v.replace(';', '').replace('--', '')
```

## 数据库安全

### SQL注入防护

```python
# ❌ 错误：字符串拼接
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ✅ 正确：参数化查询
from sqlalchemy import select
stmt = select(User).where(User.name == user_input)
```

### 最小权限原则

```sql
-- 1. 创建只读用户
CREATE USER app_readonly WITH PASSWORD 'xxx';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- 2. 创建应用用户（有限权限）
CREATE USER app_user WITH PASSWORD 'xxx';
GRANT SELECT, INSERT, UPDATE ON reports TO app_user;
GRANT SELECT, INSERT, UPDATE ON conversations TO app_user;

-- 3. 禁止DELETE权限（使用软删除）
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM app_user;
```

### 连接加密

```python
# 强制SSL连接
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"

# 验证证书
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=verify-full&sslrootcert=/path/to/ca.crt"
```

## 密钥管理

### API Key轮换

```bash
# 定期轮换API密钥（每3个月）
# 1. 生成新密钥
# 2. 更新环境变量
railway variables set OPENROUTER_API_KEY=新密钥
# 3. 重启服务
railway restart
# 4. 撤销旧密钥
```

### 敏感数据处理

```python
# 日志脱敏
import logging

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        # 隐藏API密钥
        message = re.sub(r'sk-or-v1-\w+', 'sk-or-v1-***', message)
        # 隐藏邮箱
        message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.com', message)
        record.msg = message
        return True

logger = logging.getLogger()
logger.addFilter(SensitiveDataFilter())
```

## 认证授权（未来v2.0）

### API Key认证

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    # 验证API Key
    if not is_valid_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
```

### JWT Token

```python
import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

## 依赖安全

### 定期更新

```bash
# 1. 检查过期依赖
pip list --outdated

# 2. 更新依赖
pip install --upgrade fastapi sqlalchemy

# 3. 检查安全漏洞
pip install safety
safety check

# 4. 锁定版本
pip freeze > requirements.txt
```

### 依赖审计

```bash
# 使用Snyk扫描
npm install -g snyk
snyk test

# 使用GitHub Dependabot
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
```

## 监控安全事件

### 异常登录检测

```python
from app.core.monitoring import metrics

async def track_suspicious_activity(ip: str, endpoint: str):
    # 检测异常模式
    if is_suspicious(ip, endpoint):
        metrics.record_security_event(
            event_type="suspicious_activity",
            ip=ip,
            endpoint=endpoint
        )
        # 发送告警
        await send_alert(f"Suspicious activity from {ip}")
```

### 错误日志监控

```python
# 监控401/403错误
@app.middleware("http")
async def log_unauthorized_requests(request: Request, call_next):
    response = await call_next(request)
    if response.status_code in [401, 403]:
        logger.warning(f"Unauthorized access attempt from {request.client.host}")
    return response
```

## 合规性

### GDPR/隐私保护

```python
# 1. 数据最小化
class UserData(BaseModel):
    # 只收集必要信息
    query: str  # 不收集email、phone等

# 2. 数据保留政策
async def cleanup_old_data():
    # 90天后删除个人数据
    await db.execute(
        "DELETE FROM conversations WHERE created_at < NOW() - INTERVAL '90 days'"
    )

# 3. 数据导出（用户请求）
async def export_user_data(user_id: str):
    data = await db.fetchall(
        "SELECT * FROM conversations WHERE user_id = ?", user_id
    )
    return {"data": data, "format": "json"}
```

### 日志审计

```python
# 记录所有敏感操作
@audit_log
async def delete_report(report_id: int, user: User):
    logger.info(f"User {user.id} deleted report {report_id}")
    await db.delete(Report, report_id)
```

---

**版本**: v1.0.0
**最后更新**: 2025-01-27
