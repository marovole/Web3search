# Load Testing Guide

使用Locust进行Web3 Search API的负载测试。

## 安装

```bash
cd backend
pip install locust==2.20.0
```

## 运行测试

### 1. Web UI模式（推荐）

启动Locust Web界面：

```bash
cd tests/load
locust -f locustfile.py --host=http://localhost:8000
```

然后打开浏览器访问：http://localhost:8089

在Web界面中设置：
- **Number of users**: 100（并发用户数）
- **Spawn rate**: 10（每秒启动10个用户）
- **Host**: http://localhost:8000（或生产环境URL）

点击"Start swarming"开始测试。

### 2. 无头模式（命令行）

不使用Web界面，直接运行：

```bash
# 本地测试：100用户，持续60秒
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s

# 生产环境测试：50用户，持续120秒
locust -f locustfile.py \
  --host=https://web3search-api.onrender.com \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 120s
```

### 3. 生成HTML报告

```bash
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --html=report.html
```

## 测试场景

负载测试模拟4种用户行为：

| 任务 | 权重 | 说明 |
|------|------|------|
| Quick Chat | 10 | 快速问答（目标响应时间 < 3秒） |
| Get Hotspots | 3 | 获取市场热点列表 |
| Search Autocomplete | 2 | 搜索自动补全 |
| Deep Research | 1 | 生成深度研究报告（30-60秒，有速率限制） |

## 性能指标

### 目标指标

- **Quick Chat响应时间**: < 3秒（P95）
- **Hotspots响应时间**: < 1秒（P95）
- **Autocomplete响应时间**: < 500ms（P95）
- **Deep Research响应时间**: < 60秒
- **错误率**: < 1%
- **并发支持**: 100用户

### 观察指标

在Locust Web界面中关注：

1. **Requests/s (RPS)**: 每秒请求数
2. **Response Time (P50/P95/P99)**: 响应时间分位数
3. **Failure Rate**: 失败率
4. **Total Requests**: 总请求数

## 瓶颈分析

### 常见性能瓶颈

1. **数据库连接池不足**
   - 症状：数据库查询响应时间增加
   - 解决：增加连接池大小

2. **Redis连接不足**
   - 症状：缓存操作超时
   - 解决：调整Redis连接池配置

3. **LLM API限流**
   - 症状：LLM调用失败率上升
   - 解决：实现请求队列，平滑请求

4. **Celery Worker不足**
   - 症状：任务堆积
   - 解决：增加Worker数量

### 优化建议

1. **启用缓存**: 确保Redis缓存正常工作
2. **数据库索引**: 优化慢查询
3. **连接池**: 调整数据库和Redis连接池大小
4. **并发控制**: 使用asyncio.Semaphore限制并发
5. **降级策略**: 实现数据源和LLM的fallback机制

## 测试清单

- [ ] 本地环境测试（100用户）
- [ ] 检查响应时间是否符合目标
- [ ] 检查错误率是否 < 1%
- [ ] 生产环境测试（50用户）
- [ ] 记录性能基准数据
- [ ] 识别性能瓶颈
- [ ] 实施优化措施
- [ ] 重新测试验证改进

## 故障排查

### 连接错误

```
ConnectionError: Connection refused
```

**解决方法**: 确保API服务正在运行

```bash
# 检查API是否运行
curl http://localhost:8000/health
```

### 速率限制

```
429 Too Many Requests
```

**说明**: 这是正常的速率限制保护，不视为失败。可以调整测试参数：

```bash
# 减少并发用户数
--users 20 --spawn-rate 2
```

### 超时错误

```
ReadTimeout: Request timed out
```

**解决方法**:
1. 增加超时时间
2. 优化API响应速度
3. 降低并发用户数

## 示例输出

```
=====================================================================================================
 Name                                    # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
-----------------------------------------------------------------------------------------------------
 GET /api/v1/trending/hotspots             1245            0  |     158      45    1234     120  |    20.8        0.0
 GET /api/v1/search/autocomplete            823            1  |      89      32     678      75  |    13.7        0.0
 POST /api/v1/chat/quick-chat              4156           12  |    2145     567    5678    1890  |    69.3        0.2
 POST /api/v1/chat/deep-research            415            8  |   35678   28901   62345   34567  |     6.9        0.1
-----------------------------------------------------------------------------------------------------
 Aggregated                                6639           21  |    4567      32   62345    1234  |   110.7        0.4

Response time percentiles (approximated)
 Type     Name                                                           50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
--------|-----------------------------------------------------------|--------|------|------|------|------|------|------|------|------|------|------|------|
 GET      /api/v1/trending/hotspots                                      120    145    178    201    267    345    456    567    987   1234   1234   1245
 GET      /api/v1/search/autocomplete                                     75     89    102    123    156    198    234    289    567    678    678    823
 POST     /api/v1/chat/quick-chat                                       1890   2134   2456   2678   3456   4123   4789   5234   5567   5678   5678   4156
 POST     /api/v1/chat/deep-research                                   34567  36789  39012  41234  47890  53456  57891  60123  61890  62345  62345    415
--------|-----------------------------------------------------------|--------|------|------|------|------|------|------|------|------|------|------|------|
         Aggregated                                                     1234   2345   3456   4567   6789   8901  12345  15678  34567  62345  62345   6639
```

## 参考资料

- [Locust官方文档](https://docs.locust.io/)
- [API性能优化最佳实践](https://docs.locust.io/en/stable/best-practices.html)
