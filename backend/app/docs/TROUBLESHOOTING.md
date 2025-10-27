# 故障排查指南

Web3 Search API 常见问题诊断和解决方案。

## 目录

1. [快速诊断](#快速诊断)
2. [服务启动问题](#服务启动问题)
3. [数据库问题](#数据库问题)
4. [Redis问题](#redis问题)
5. [API响应问题](#api响应问题)
6. [数据采集问题](#数据采集问题)
7. [LLM调用问题](#llm调用问题)
8. [性能问题](#性能问题)
9. [部署问题](#部署问题)
10. [监控告警](#监控告警)

---

## 快速诊断

### 健康检查

```bash
# 检查服务状态
curl https://web3search-api.onrender.com/health

# 预期响应
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:00:00",
  "version": "1.0.0",
  "environment": "production",
  "database": "connected",
  "redis": "connected",
  "celery": {
    "broker": "connected",
    "workers": 1,
    "status": "running"
  }
}
```

### 快速诊断命令

```bash
# 1. 检查进程
ps aux | grep uvicorn

# 2. 检查端口占用
lsof -i :8000

# 3. 查看最近日志
tail -f logs/app.log

# 4. 检查磁盘空间
df -h

# 5. 检查内存使用
free -h

# 6. 测试数据库连接
psql $DATABASE_URL -c "SELECT 1"

# 7. 测试Redis连接
redis-cli -u $REDIS_URL ping
```

---

## 服务启动问题

### 问题1：服务无法启动 - 端口被占用

**现象**：
```
ERROR: [Errno 48] Address already in use
```

**原因**：端口8000已被其他进程占用

**解决方案**：
```bash
# 1. 查找占用端口的进程
lsof -ti:8000

# 2. 杀死占用进程
kill -9 $(lsof -ti:8000)

# 3. 或使用其他端口启动
uvicorn app.main:app --port 8001
```

### 问题2：服务启动后立即退出

**现象**：
```
uvicorn启动后立即退出，无错误信息
```

**诊断步骤**：
```bash
# 1. 检查Python版本（需要3.11+）
python3 --version

# 2. 检查依赖是否完整
pip list | grep -E "(fastapi|sqlalchemy|redis)"

# 3. 尝试直接运行main.py查看错误
python3 -m app.main

# 4. 检查环境变量
env | grep -E "(DATABASE_URL|REDIS_URL|OPENROUTER_API_KEY)"
```

**常见原因**：
1. 缺少必需的环境变量
2. 依赖版本不兼容
3. 数据库连接失败

**解决方案**：
```bash
# 1. 创建.env文件并配置必需变量
cp .env.example .env
# 编辑.env文件

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 检查数据库连接
psql $DATABASE_URL -c "\dt"
```

### 问题3：ModuleNotFoundError

**现象**：
```
ModuleNotFoundError: No module named 'app.xxx'
```

**原因**：Python路径或依赖问题

**解决方案**：
```bash
# 1. 确认工作目录
pwd  # 应该在backend/目录

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 检查PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 4. 使用-m标志运行
python3 -m uvicorn app.main:app --reload
```

### 问题4：数据库表不存在

**现象**：
```
ProgrammingError: relation "reports" does not exist
```

**原因**：数据库表未创建

**解决方案**：
```bash
# 方法1：使用管理端点（首次部署）
curl -X POST "https://web3search-api.onrender.com/admin/init-db"

# 方法2：使用Alembic迁移（推荐）
alembic upgrade head

# 方法3：手动创建（开发环境）
# 在app/main.py中，lifespan函数会自动创建表（DEBUG=true）
```

---

## 数据库问题

### 问题5：数据库连接超时

**现象**：
```
TimeoutError: Connection pool timeout after 30s
```

**原因**：
1. 数据库服务不可用
2. 连接池耗尽
3. 慢查询阻塞连接

**诊断**：
```bash
# 1. 测试数据库连接
psql $DATABASE_URL -c "SELECT version();"

# 2. 查看活跃连接数
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# 3. 查看慢查询
psql $DATABASE_URL -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds'
ORDER BY duration DESC;
"

# 4. 查看锁等待
psql $DATABASE_URL -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;
"
```

**解决方案**：
```bash
# 1. 重启API服务（重置连接池）
systemctl restart web3search-api

# 2. 增加连接池大小（临时）
# 修改app/core/database.py中的pool_size和max_overflow

# 3. 杀死阻塞查询
psql $DATABASE_URL -c "SELECT pg_terminate_backend(<blocking_pid>);"

# 4. 优化慢查询（添加索引）
# 查看缺失的索引
psql $DATABASE_URL -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY abs(correlation) DESC
LIMIT 10;
"
```

### 问题6：数据库磁盘空间不足

**现象**：
```
ERROR: could not write to file: No space left on device
```

**诊断**：
```bash
# 1. 检查磁盘使用
df -h

# 2. 查看数据库大小
psql $DATABASE_URL -c "
SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
"

# 3. 查看各表大小
psql $DATABASE_URL -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

**解决方案**：
```bash
# 1. 清理旧数据
psql $DATABASE_URL -c "DELETE FROM reports WHERE created_at < NOW() - INTERVAL '90 days';"

# 2. VACUUM清理空间
psql $DATABASE_URL -c "VACUUM FULL;"

# 3. 升级数据库存储（生产环境）
# 登录Render/Railway Dashboard增加磁盘容量

# 4. 实施数据归档策略
# 定期导出旧数据到S3/备份存储
```

---

## Redis问题

### 问题7：Redis连接失败

**现象**：
```
ConnectionError: Error connecting to Redis
```

**诊断**：
```bash
# 1. 测试Redis连接
redis-cli -u $REDIS_URL ping

# 2. 检查Redis服务状态
redis-cli -u $REDIS_URL INFO server

# 3. 查看内存使用
redis-cli -u $REDIS_URL INFO memory
```

**解决方案**：
```bash
# 1. 检查REDIS_URL环境变量
echo $REDIS_URL

# 2. 重启Redis服务（如果自托管）
systemctl restart redis

# 3. 清理Redis缓存（如果内存满）
redis-cli -u $REDIS_URL FLUSHDB

# 4. 检查网络连接
telnet <redis-host> 6379
```

### 问题8：Redis内存不足

**现象**：
```
OOM command not allowed when used memory > 'maxmemory'
```

**诊断**：
```bash
# 查看内存使用情况
redis-cli -u $REDIS_URL INFO memory | grep used_memory_human
```

**解决方案**：
```bash
# 1. 立即清理（临时）
redis-cli -u $REDIS_URL FLUSHDB

# 2. 设置驱逐策略
redis-cli -u $REDIS_URL CONFIG SET maxmemory-policy allkeys-lru

# 3. 增加Redis内存限制
# 修改redis.conf: maxmemory 2gb

# 4. 优化缓存TTL（减少缓存时间）
# 修改app/services/cache.py中的TTL配置

# 5. 升级Redis实例（生产环境）
# 登录Render/Railway Dashboard升级Redis plan
```

---

## API响应问题

### 问题9：API返回500错误

**现象**：
```json
{
  "detail": "Internal Server Error"
}
```

**诊断步骤**：
```bash
# 1. 查看最近错误日志
tail -100 logs/app.log | grep ERROR

# 2. 检查Sentry
# 登录Sentry查看错误详情

# 3. 重现问题
curl -X POST "https://web3search-api.onrender.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "测试查询"}'

# 4. 查看堆栈追踪
# 在日志或Sentry中查看完整堆栈
```

**常见原因和解决方案**：

1. **数据库连接失败**
   ```bash
   # 检查DATABASE_URL
   echo $DATABASE_URL

   # 测试连接
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **Redis连接失败**
   ```bash
   # 检查REDIS_URL
   redis-cli -u $REDIS_URL ping
   ```

3. **外部API超时**
   ```bash
   # 检查CoinGecko API
   curl "https://api.coingecko.com/api/v3/ping"

   # 检查OpenRouter API
   curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     "https://openrouter.ai/api/v1/models"
   ```

4. **代码错误**
   ```bash
   # 查看Sentry错误详情
   # 修复代码并重新部署
   ```

### 问题10：API响应缓慢（>5s）

**现象**：API请求超过5秒才返回

**诊断**：
```bash
# 1. 使用time命令测量
time curl -X POST "https://web3search-api.onrender.com/api/v1/chat/quick-chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'

# 2. 查看Sentry Performance
# 登录Sentry → Performance → 查看慢事务

# 3. 检查数据库慢查询
psql $DATABASE_URL -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# 4. 查看Redis响应时间
redis-cli -u $REDIS_URL --latency

# 5. 检查外部API延迟
curl -w "@curl-format.txt" -o /dev/null -s "https://api.coingecko.com/api/v3/ping"
```

**解决方案**：
```bash
# 1. 启用缓存（如未启用）
# 确保Redis正常工作

# 2. 优化数据库查询
# 添加索引、减少JOIN

# 3. 增加API超时设置
# 修改app/services/collectors中的timeout参数

# 4. 扩容服务器（CPU/内存）
# 登录Render/Railway Dashboard升级plan

# 5. 启用CDN（静态资源）
# 配置Cloudflare CDN
```

### 问题11：429 - 速率限制

**现象**：
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超限，请45秒后重试"
  }
}
```

**原因**：超过了速率限制

**解决方案**：

**客户端侧**：
```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

session = create_session()
response = session.post(API_URL, json=data)
```

**服务端侧**：
```bash
# 1. 检查IP是否被误判
# 查看Redis中的速率限制记录
redis-cli -u $REDIS_URL KEYS "ratelimit:*"

# 2. 调整速率限制（如需）
# 修改app/api/middleware/rate_limit.py中的限制配置

# 3. 清除特定IP的限制（紧急情况）
redis-cli -u $REDIS_URL DEL "ratelimit:<ip>:<endpoint>"
```

---

## 数据采集问题

### 问题12：CoinGecko API返回429

**现象**：
```
CoinGecko API rate limit exceeded (429)
```

**原因**：超过CoinGecko免费API限额（10-50次/分钟）

**解决方案**：
```bash
# 1. 启用fallback到CoinMarketCap
# 确保COINMARKETCAP_API_KEY已配置
echo $COINMARKETCAP_API_KEY

# 2. 增加缓存时间
# 修改app/services/cache.py: PRICE_CACHE_TTL从300增加到600

# 3. 实施请求队列
# 在app/services/collectors/coingecko.py中添加rate limiter

# 4. 升级CoinGecko Pro
# 访问https://www.coingecko.com/en/api/pricing
```

### 问题13：链上数据获取失败

**现象**：
```
Etherscan API error: Max rate limit reached
```

**解决方案**：
```bash
# 1. 使用fallback - Blockchair
# 确保环境变量配置
echo $BLOCKCHAIR_API_KEY

# 2. 申请Etherscan API Key
# 访问https://etherscan.io/apis
# 添加到环境变量：ETHERSCAN_API_KEY

# 3. 减少调用频率
# 修改app/tasks/data_collection.py中的定时任务间隔
```

---

## LLM调用问题

### 问题14：OpenRouter API调用失败

**现象**：
```
OpenRouter API error: Invalid API key
```

**诊断**：
```bash
# 1. 检查API Key
echo $OPENROUTER_API_KEY

# 2. 测试API Key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  "https://openrouter.ai/api/v1/models"

# 3. 查看配额使用情况
# 登录https://openrouter.ai/account查看credit余额
```

**解决方案**：
```bash
# 1. 重新获取API Key
# 访问https://openrouter.ai/keys

# 2. 更新环境变量
export OPENROUTER_API_KEY="sk-or-v1-..."

# 3. 重启服务
systemctl restart web3search-api
```

### 问题15：LLM响应超时

**现象**：
```
TimeoutError: LLM request timeout after 30s
```

**原因**：
1. OpenRouter服务慢
2. 模型负载高
3. Prompt过长

**解决方案**：
```bash
# 1. 增加超时设置
# 修改app/services/llm_client.py: timeout=60

# 2. 切换到更快的模型
# 修改app/core/config.py:
# PRIMARY_LLM_MODEL = "anthropic/claude-3-haiku"  # 更快

# 3. 简化Prompt
# 减少few-shot示例数量
# 删除不必要的上下文

# 4. 启用流式响应
# 使用/quick-chat/stream端点
```

---

## 性能问题

### 问题16：CPU使用率持续>80%

**诊断**：
```bash
# 1. 查看进程CPU使用
top -o %CPU

# 2. 查看API请求量
# 检查Sentry Metrics或日志

# 3. 分析慢函数
# 使用cProfile
python3 -m cProfile -o output.prof app/main.py
```

**解决方案**：
```bash
# 1. 扩容服务器
# 升级到更高CPU配置

# 2. 优化代码
# 使用异步函数
# 减少计算密集型操作

# 3. 启用负载均衡
# 部署多个实例

# 4. 缓存计算结果
# 使用Redis缓存
```

### 问题17：内存泄漏

**现象**：内存使用持续增长，最终OOM

**诊断**：
```bash
# 1. 监控内存使用
free -h

# 2. 查看进程内存
ps aux | grep uvicorn | awk '{print $6}'

# 3. 使用memory_profiler
pip install memory_profiler
python3 -m memory_profiler app/main.py
```

**解决方案**：
```bash
# 1. 重启服务（临时）
systemctl restart web3search-api

# 2. 检查循环引用
# 使用gc.get_referrers()查找

# 3. 限制缓存大小
# 使用LRU cache with maxsize

# 4. 定期重启worker
# 配置uvicorn --max-requests 1000
```

---

## 部署问题

### 问题18：Render部署失败

**现象**：
```
Build failed: exit code 1
```

**诊断步骤**：
```bash
# 1. 查看Build Logs
# 登录Render Dashboard → Service → Events → 查看日志

# 2. 常见错误：
# - requirements.txt依赖安装失败
# - 环境变量缺失
# - build命令错误
```

**解决方案**：
```bash
# 1. 固定依赖版本
# 在requirements.txt中指定确切版本
fastapi==0.109.0

# 2. 配置Build Command
# Render Dashboard → Settings → Build Command
pip install -r requirements.txt

# 3. 配置Start Command
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# 4. 添加环境变量
# Settings → Environment → Add Variable
```

### 问题19：Railway自动部署失败

**现象**：
```
Deployment failed: health check timeout
```

**解决方案**：
```bash
# 1. 检查健康检查端点
curl https://your-app.railway.app/health

# 2. 增加健康检查超时
# railway.toml:
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300

# 3. 查看部署日志
railway logs

# 4. 手动重试部署
railway up --yes
```

---

## 监控告警

### 问题20：Sentry告警过多

**现象**：每分钟收到多个Sentry告警

**原因**：
1. 真实错误率高
2. 告警阈值设置过低
3. 重复错误未归并

**解决方案**：
```bash
# 1. 分析错误类型
# Sentry → Issues → 按频率排序

# 2. 归并重复错误
# 在Issue页面点击"Merge"合并相同错误

# 3. 调整告警规则
# 修改app/config/sentry_alerts.json中的阈值

# 4. 添加过滤规则
# 修改app/core/monitoring.py中的before_send_filter

# 5. 静默非关键告警
# Sentry → Settings → Alerts → Mute
```

---

## 紧急联系

### 运维团队
- **Slack**: #engineering, #on-call
- **Email**: support@web3search.com
- **PagerDuty**: 查看轮值表

### 外部服务支持
- **Render**: https://render.com/support
- **Railway**: https://railway.app/help
- **Sentry**: https://sentry.io/support
- **OpenRouter**: https://openrouter.ai/support

---

## 参考资源

- [监控运维指南](./MONITORING_GUIDE.md)
- [部署指南](./DEPLOYMENT.md)
- [数据库维护指南](./DATABASE_MAINTENANCE.md)
- [API错误码参考](./API_ERRORS.md)

---

**版本**: v1.0.0
**最后更新**: 2025-01-27
**维护者**: Web3Search SRE Team
