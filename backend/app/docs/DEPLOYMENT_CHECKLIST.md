# 生产环境部署清单

Web3 Search AI引擎生产环境部署完整清单

**版本**: v1.0.0
**最后更新**: 2025-01-27
**适用阶段**: Phase 14完成后

---

## 📋 部署前检查清单

### 1. 代码准备 ✅

#### 1.1 代码质量
- [ ] 所有测试通过（pytest, E2E测试）
- [ ] 代码格式化完成（black, isort）
- [ ] 代码质量检查通过（flake8, pylint）
- [ ] OpenSpec验证通过（openspec validate --strict）
- [ ] 无未解决的TODO/FIXME标记
- [ ] 代码审查完成并通过

#### 1.2 版本控制
- [ ] 所有更改已提交到Git
- [ ] 创建了release分支（release/v1.0.0）
- [ ] 打上版本标签（git tag v1.0.0）
- [ ] CHANGELOG.md已更新
- [ ] README.md反映最新功能

#### 1.3 依赖管理
- [ ] requirements.txt已更新
- [ ] 无已知安全漏洞（pip install safety; safety check）
- [ ] 依赖版本已锁定
- [ ] 无不必要的依赖

**验证命令**:
```bash
# 运行所有测试
pytest tests/ -v --cov=app --cov-report=html

# 代码格式化
black app/ tests/
isort app/ tests/

# 代码质量检查
flake8 app/

# OpenSpec验证
openspec validate --strict

# 安全检查
pip install safety
safety check

# Git标签
git tag v1.0.0
git push origin v1.0.0
```

---

### 2. 环境配置 ⚙️

#### 2.1 必需环境变量

**数据库**:
- [ ] `DATABASE_URL` - PostgreSQL连接字符串（含sslmode=require）
- [ ] `REDIS_URL` - Redis连接字符串

**LLM API**:
- [ ] `OPENROUTER_API_KEY` - OpenRouter API密钥（已验证）

**数据源API**:
- [ ] `COINGECKO_API_KEY` - CoinGecko API密钥（可选）
- [ ] `ETHERSCAN_API_KEY` - Etherscan API密钥
- [ ] `TWITTER_BEARER_TOKEN` - Twitter API令牌
- [ ] `REDDIT_CLIENT_ID` - Reddit客户端ID
- [ ] `REDDIT_CLIENT_SECRET` - Reddit客户端密钥
- [ ] `CRYPTOPANIC_API_KEY` - CryptoPanic API密钥

**应用配置**:
- [ ] `ENVIRONMENT=production` - 环境标识
- [ ] `DEBUG=false` - 关闭调试模式
- [ ] `LOG_LEVEL=INFO` - 日志级别
- [ ] `CORS_ORIGINS` - 允许的前端域名

**Celery**:
- [ ] `CELERY_BROKER_URL` - Redis broker URL
- [ ] `CELERY_RESULT_BACKEND` - Redis result backend

**监控**:
- [ ] `SENTRY_DSN` - Sentry项目DSN
- [ ] `SENTRY_ENVIRONMENT=production` - Sentry环境标识

#### 2.2 环境变量验证
```bash
# 检查必需环境变量
python3 -c "
from app.core.config import settings
print(f'Database: {settings.DATABASE_URL[:20]}...')
print(f'Redis: {settings.REDIS_URL[:20]}...')
print(f'OpenRouter: {settings.OPENROUTER_API_KEY[:15]}...')
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Sentry: {settings.SENTRY_DSN[:30] if settings.SENTRY_DSN else \"Not configured\"}...')
"
```

---

### 3. 数据库准备 🗄️

#### 3.1 数据库创建
- [ ] PostgreSQL 17实例已创建
- [ ] 数据库名称: `web3search_production`
- [ ] 连接加密已启用（sslmode=require）
- [ ] 备份策略已配置（每天自动备份）

#### 3.2 数据库初始化
- [ ] 表结构已创建（Alembic迁移）
- [ ] 索引已创建（7个关键索引）
- [ ] 外键约束已设置
- [ ] 分区策略已配置（如需要）

#### 3.3 数据库性能
- [ ] 连接池已配置（max=50, min=10）
- [ ] 慢查询日志已启用（>500ms）
- [ ] 查询超时已设置（30s）
- [ ] 连接超时已设置（10s）

**初始化命令**:
```bash
# 方法1：通过API端点（推荐）
curl -X POST https://your-api.onrender.com/admin/init-db

# 方法2：通过Alembic
alembic upgrade head

# 验证表创建
psql $DATABASE_URL -c "\dt"

# 验证索引
psql $DATABASE_URL -c "\di"
```

---

### 4. Redis配置 📦

#### 4.1 Redis实例
- [ ] Redis 7实例已创建
- [ ] 最大内存: 256MB（Free tier）或更高
- [ ] 驱逐策略: allkeys-lru
- [ ] 持久化: RDB + AOF

#### 4.2 缓存策略
- [ ] 价格数据TTL: 5分钟
- [ ] Quick Chat查询TTL: 10分钟
- [ ] Hotspots TTL: 5分钟
- [ ] Autocomplete TTL: 30分钟

**验证命令**:
```bash
# 连接测试
redis-cli -u $REDIS_URL ping

# 检查内存
redis-cli -u $REDIS_URL INFO memory

# 检查驱逐策略
redis-cli -u $REDIS_URL CONFIG GET maxmemory-policy
```

---

### 5. Web服务部署 🌐

#### 5.1 Render Web Service

**配置**:
- [ ] 服务名称: `web3search-api`
- [ ] 环境: `Production`
- [ ] 实例类型: `Standard` (推荐) 或 `Starter`
- [ ] 区域: `Oregon` 或距离用户最近
- [ ] 构建命令: `pip install -r requirements.txt`
- [ ] 启动命令: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**健康检查**:
- [ ] 健康检查路径: `/health`
- [ ] 健康检查间隔: 30秒
- [ ] 健康检查超时: 10秒

**自动部署**:
- [ ] 已连接GitHub仓库
- [ ] 自动部署已启用（推送到main分支）
- [ ] 部署通知已配置（Slack或邮件）

**验证**:
```bash
# 健康检查
curl https://web3search-api.onrender.com/health

# API文档
curl https://web3search-api.onrender.com/docs

# Quick Chat测试
curl -X POST https://web3search-api.onrender.com/api/v1/chat/quick-chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}'
```

---

### 6. Worker部署 ⚙️

#### 6.1 Celery Worker（Background Worker）

**配置**:
- [ ] 服务名称: `web3search-worker`
- [ ] 环境: `Production`
- [ ] 实例类型: `Standard` (推荐)
- [ ] 构建命令: `pip install -r requirements.txt`
- [ ] 启动命令: `celery -A app.tasks.celery_app worker -l info -Q high_priority,default,low_priority --concurrency 2`

**队列配置**:
- [ ] high_priority队列（价格更新）
- [ ] default队列（常规任务）
- [ ] low_priority队列（清理任务）

**并发配置**:
- [ ] 并发数: 2（512MB RAM）或4（1GB RAM）
- [ ] Worker池: prefork
- [ ] 任务超时: 300秒

**验证**:
```bash
# 检查Worker状态
celery -A app.tasks.celery_app inspect active

# 检查队列
celery -A app.tasks.celery_app inspect registered

# 查看统计
celery -A app.tasks.celery_app inspect stats
```

---

### 7. Beat部署 ⏰

#### 7.1 Celery Beat（Cron Job）

**配置**:
- [ ] 服务名称: `web3search-beat`
- [ ] 环境: `Production`
- [ ] 实例类型: `Starter`（足够）
- [ ] 构建命令: `pip install -r requirements.txt`
- [ ] 启动命令: `celery -A app.tasks.celery_app beat -l info`
- [ ] 计划: `@hourly`（Render的最小间隔）

**定时任务验证**:
- [ ] 每1分钟: 更新热门币种价格
- [ ] 每1小时: 项目快照、热点识别
- [ ] 每6小时: 社交数据更新
- [ ] 每天凌晨2点: 链上数据更新
- [ ] 每30分钟: 新闻采集
- [ ] 每天凌晨3点: 清理过期缓存

**验证**:
```bash
# 查看定时任务
celery -A app.tasks.celery_app inspect scheduled

# 手动触发任务测试
python3 -c "
from app.tasks.price_tasks import update_trending_prices
result = update_trending_prices.apply_async()
print(f'Task ID: {result.id}')
"
```

---

### 8. 前端部署 🎨

#### 8.1 Vercel部署

**配置**:
- [ ] 项目名称: `web3search-frontend`
- [ ] 框架: `React` 或 `Next.js`
- [ ] 构建命令: `npm run build`
- [ ] 输出目录: `dist` 或 `.next`
- [ ] 环境变量: `VITE_API_BASE_URL=https://web3search-api.onrender.com`

**域名配置**:
- [ ] 自定义域名已添加（如果有）
- [ ] SSL证书已配置（自动）
- [ ] DNS记录已验证

**验证**:
```bash
# 访问前端
curl https://web3search.vercel.app

# 检查API连接
# 浏览器控制台检查网络请求
```

---

### 9. 监控配置 📊

#### 9.1 Sentry监控

**后端配置**:
- [ ] Sentry项目已创建: `web3search-backend`
- [ ] DSN已配置到环境变量
- [ ] Environment: `production`
- [ ] Release tracking已启用
- [ ] Source maps已上传（如果适用）

**前端配置**:
- [ ] Sentry项目已创建: `web3search-frontend`
- [ ] DSN已配置
- [ ] Environment: `production`
- [ ] Error boundary已实现

**告警规则**:
- [ ] 错误率>5% → 立即告警
- [ ] P95延迟>3s → 5分钟内告警
- [ ] 数据源失败率>20% → 立即告警
- [ ] 内存使用>90% → 警告
- [ ] CPU使用>80% → 警告

**Slack集成**:
- [ ] Slack Webhook已配置
- [ ] 告警频道: #alerts
- [ ] 测试消息已发送成功

**验证**:
```bash
# 触发测试错误
curl -X GET https://web3search-api.onrender.com/sentry-test-error

# 检查Sentry Dashboard
# https://sentry.io/organizations/your-org/projects/web3search-backend/
```

---

### 10. 安全检查 🔒

#### 10.1 API安全
- [ ] CORS配置正确（仅允许特定域名）
- [ ] Rate limiting已启用
- [ ] 敏感端点已保护（如/admin）
- [ ] SQL注入防护已验证
- [ ] XSS防护已验证

#### 10.2 密钥管理
- [ ] API密钥已轮换（如果是旧密钥）
- [ ] 环境变量仅在平台设置，不提交到Git
- [ ] 敏感日志已脱敏
- [ ] 数据库连接使用SSL

#### 10.3 依赖安全
- [ ] 无已知CVE漏洞
- [ ] 依赖版本已锁定
- [ ] Dependabot已启用（GitHub）

**验证命令**:
```bash
# 安全漏洞扫描
pip install safety
safety check

# 检查CORS
curl -H "Origin: https://malicious.com" \
  https://web3search-api.onrender.com/health

# 检查Rate Limiting
for i in {1..20}; do
  curl https://web3search-api.onrender.com/api/v1/chat/quick-chat \
    -X POST -H "Content-Type: application/json" \
    -d '{"query": "test"}' &
done
```

---

### 11. 性能验证 🚀

#### 11.1 基准测试
- [ ] Quick Chat P95延迟 <3秒
- [ ] Deep Research响应时间 <60秒
- [ ] Hotspots响应时间 <1秒
- [ ] Autocomplete响应时间 <500ms
- [ ] 缓存命中率 >70%

#### 11.2 负载测试
- [ ] 100并发用户测试通过
- [ ] 无内存泄漏
- [ ] 无数据库连接泄漏
- [ ] CPU使用率合理（<80%平均）

**测试命令**:
```bash
# Quick Chat负载测试
ab -n 100 -c 10 -T application/json \
  -p request.json \
  https://web3search-api.onrender.com/api/v1/chat/quick-chat

# Hotspots负载测试
ab -n 1000 -c 50 \
  https://web3search-api.onrender.com/api/v1/trending/hotspots?limit=10
```

---

### 12. 数据验证 📊

#### 12.1 数据采集
- [ ] 价格数据正常更新（每1分钟）
- [ ] 社交数据正常更新（每6小时）
- [ ] 链上数据正常更新（每天凌晨2点）
- [ ] 新闻数据正常更新（每30分钟）

#### 12.2 数据质量
- [ ] 数据完整度 >95%
- [ ] 数据准确度 >95%
- [ ] 无异常价格波动（±50%）
- [ ] 数据时效性合格（<10分钟延迟）

**验证命令**:
```bash
# 检查最新价格数据
curl https://web3search-api.onrender.com/api/v1/search/autocomplete?q=BTC

# 检查热点数据
curl https://web3search-api.onrender.com/api/v1/trending/hotspots?limit=10

# 检查Celery任务执行
celery -A app.tasks.celery_app inspect active
```

---

### 13. 备份策略 💾

#### 13.1 数据库备份
- [ ] 自动备份已配置（每天）
- [ ] 备份保留: 7天（生产环境）
- [ ] 备份验证: 每周测试恢复
- [ ] 异地备份: S3或其他云存储

#### 13.2 配置备份
- [ ] 环境变量已记录（安全位置）
- [ ] Render配置已导出
- [ ] Vercel配置已导出

**备份脚本**:
```bash
# 数据库备份
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 上传到S3
aws s3 cp backup_$(date +%Y%m%d).sql \
  s3://your-bucket/backups/

# 验证备份
pg_restore --list backup_$(date +%Y%m%d).sql
```

---

### 14. 回滚计划 🔄

#### 14.1 回滚准备
- [ ] 上一个稳定版本标签: v0.9.0
- [ ] 回滚命令已文档化
- [ ] 数据库迁移回滚脚本已准备
- [ ] 团队成员已培训

#### 14.2 回滚触发条件
- [ ] 错误率>10%持续5分钟
- [ ] P95延迟>10秒持续5分钟
- [ ] 系统可用性<95%
- [ ] 关键功能完全失效

**回滚命令**:
```bash
# Git回滚
git revert HEAD
git push origin main

# 或者回到上一个稳定版本
git checkout v0.9.0
git push origin main --force

# 数据库回滚
alembic downgrade -1
```

---

### 15. 文档完整性 📖

#### 15.1 用户文档
- [ ] README.md已更新
- [ ] API文档已完善（/docs）
- [ ] API_TUTORIAL.md已创建
- [ ] API_CHANGELOG.md已更新

#### 15.2 运维文档
- [ ] DEPLOYMENT.md已更新
- [ ] TROUBLESHOOTING.md已创建
- [ ] METRICS.md已创建
- [ ] SCALING.md已创建
- [ ] DATABASE_MAINTENANCE.md已创建
- [ ] SECURITY.md已创建
- [ ] MONITORING_GUIDE.md已创建

#### 15.3 开发文档
- [ ] DEV_SETUP.md已创建
- [ ] CODE_REVIEW.md已创建
- [ ] CONTRIBUTING.md已更新

---

### 16. 团队准备 👥

#### 16.1 On-call轮值
- [ ] On-call日程已安排
- [ ] 联系方式已更新
- [ ] 升级流程已文档化

#### 16.2 培训
- [ ] 团队成员已熟悉监控Dashboard
- [ ] 故障排查指南已分享
- [ ] 回滚流程已演练

#### 16.3 沟通渠道
- [ ] #prod-alerts Slack频道已创建
- [ ] Sentry告警已配置到Slack
- [ ] 邮件通知已配置

---

### 17. 发布流程 🚀

#### 17.1 部署步骤
1. [ ] 确认所有检查项已完成
2. [ ] 创建部署公告（Slack #general）
3. [ ] 执行部署（推送到main分支）
4. [ ] 监控部署过程（Render Dashboard）
5. [ ] 验证部署成功（健康检查、测试请求）
6. [ ] 监控5分钟无错误
7. [ ] 发布成功公告

#### 17.2 部署时间
- [ ] 选择低流量时段（凌晨2-6点，当地时间）
- [ ] 避开周五和假期前一天
- [ ] 提前24小时通知用户（如果有用户）

#### 17.3 发布公告模板
```markdown
## 🚀 Web3 Search API v1.0.0 发布公告

**发布时间**: 2025-01-27 03:00 UTC
**预计停机时间**: 5分钟

### 新功能
- ✨ 性能提升：响应时间降低40-94%
- ✨ 监控增强：Sentry全链路追踪
- ✨ 可靠性提升：数据源Fallback机制

### 改进
- 🔧 缓存优化（命中率78%）
- 🔧 数据质量验证
- 🔧 错误处理增强

### 文档
- 📖 14个专业文档上线

如有问题，请联系 support@web3search.com
```

---

### 18. 部署后验证 ✅

#### 18.1 立即验证（部署后5分钟内）
- [ ] 所有健康检查通过
- [ ] API端点响应正常
- [ ] 无5xx错误
- [ ] Celery任务正常执行
- [ ] 数据库连接正常
- [ ] Redis连接正常

#### 18.2 短期监控（部署后1小时内）
- [ ] 错误率 <1%
- [ ] P95延迟 <3秒
- [ ] 缓存命中率 >70%
- [ ] CPU使用率 <80%
- [ ] 内存使用率 <80%
- [ ] 数据采集正常

#### 18.3 中期监控（部署后24小时内）
- [ ] 系统可用性 >99.5%
- [ ] 无数据丢失
- [ ] 无内存泄漏
- [ ] 定时任务全部执行
- [ ] 用户反馈正常

**验证脚本**:
```bash
#!/bin/bash
# post_deployment_check.sh

echo "=== 健康检查 ==="
curl -s https://web3search-api.onrender.com/health | jq

echo "\n=== API测试 ==="
curl -s -X POST https://web3search-api.onrender.com/api/v1/chat/quick-chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Bitcoin?"}' | jq '.content' | head -c 100

echo "\n=== Sentry检查 ==="
echo "请访问: https://sentry.io/organizations/your-org/projects/web3search-backend/"
echo "检查最近5分钟是否有新错误"

echo "\n=== Celery检查 ==="
celery -A app.tasks.celery_app inspect active

echo "\n=== 数据库检查 ==="
psql $DATABASE_URL -c "SELECT COUNT(*) FROM coins;"

echo "\n=== Redis检查 ==="
redis-cli -u $REDIS_URL INFO stats | grep total_connections_received

echo "\n✅ 部署后验证完成！"
```

---

## 🎯 最终检查

### 关键指标目标

| 指标 | 目标值 | 实际值 | 状态 |
|------|--------|--------|------|
| **部署成功率** | 100% | ___ | ☐ |
| **健康检查通过** | 100% | ___ | ☐ |
| **API响应时间（P95）** | <3s | ___ | ☐ |
| **错误率** | <1% | ___ | ☐ |
| **系统可用性** | >99.5% | ___ | ☐ |
| **缓存命中率** | >70% | ___ | ☐ |
| **数据完整度** | >95% | ___ | ☐ |

### 部署签署

- [ ] **技术负责人**: _____________ 日期: _______
- [ ] **测试负责人**: _____________ 日期: _______
- [ ] **运维负责人**: _____________ 日期: _______

---

## 📞 紧急联系方式

- **On-call工程师**: [姓名] - [电话] - [邮箱]
- **备用工程师**: [姓名] - [电话] - [邮箱]
- **数据库管理员**: [姓名] - [电话] - [邮箱]
- **Render支持**: support@render.com
- **Sentry支持**: support@sentry.io

---

## 📚 相关文档

- [部署指南](DEPLOYMENT.md)
- [故障排查](TROUBLESHOOTING.md)
- [监控指南](MONITORING_GUIDE.md)
- [数据库维护](DATABASE_MAINTENANCE.md)
- [性能基准](PERFORMANCE_BENCHMARK.md)

---

**清单版本**: v1.0.0
**最后更新**: 2025-01-27
**下次审查**: 2025-02-27
