# Advanced Load Testing Guide

使用Locust进行Web3 Search API的高级负载测试，支持1000+并发用户测试。

## 安装

```bash
cd backend
pip install locust==2.20.0 gevent==23.7.0
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

### 2. 使用配置文件运行

```bash
# 查看所有测试场景
python load_test_config.py

# 运行特定场景
python load_test_config.py --scenario load_test

# 批量运行所有测试
chmod +x run_load_tests.sh
./run_load_tests.sh
```

### 3. 高负载测试命令

```bash
# 1000并发用户，持续5分钟
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 300s \
  --html reports/load_test_report.html

# 1500并发用户，持续10分钟
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 1500 \
  --spawn-rate 100 \
  --run-time 600s \
  --html reports/high_load_report.html

# 2000并发用户峰值测试
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 2000 \
  --spawn-rate 200 \
  --run-time 180s \
  --html reports/peak_test_report.html
```

### 4. 生成详细报告

```bash
# 生成HTML报告和CSV数据
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 1000 \
  --spawn-rate 50 \
  --run-time 300s \
  --html reports/performance_report.html \
  --csv reports/performance_stats

# 报告文件：
# - reports/performance_report.html (可视化报告)
# - reports/performance_stats_stats.csv (统计数据)
# - reports/performance_stats_failures.csv (失败数据)
# - reports/performance_stats_history.csv (历史数据)
```

## 测试场景

### 预定义测试场景

| 场景名称 | 并发用户 | 启动速率 | 持续时间 | 说明 |
|----------|----------|----------|----------|------|
| dev_smoke | 50 | 5/s | 60s | 开发环境冒烟测试 |
| functional | 200 | 20/s | 120s | 功能完整性测试 |
| load_test | 1000 | 50/s | 300s | 1000并发负载测试 |
| high_load | 1500 | 100/s | 600s | 1500并发高负载测试 |
| peak_test | 2000 | 200/s | 180s | 2000并发峰值测试 |
| stress_test | 3000 | 300/s | 900s | 3000并发压力测试 |
| prod_validation | 100 | 10/s | 120s | 生产环境性能验证 |

### 用户行为模拟

负载测试模拟5种用户行为：

| 任务 | 权重 | 说明 | 目标响应时间 |
|------|------|------|-------------|
| Quick Chat | 8 | 快速问答 | < 3秒 (P95) |
| Get Hotspots | 4 | 获取市场热点列表 | < 1秒 (P95) |
| Search Autocomplete | 3 | 搜索自动补全 | < 500ms (P95) |
| Get Market Data | 1 | 获取实时市场数据 | < 800ms (P95) |
| Deep Research | 1 | 生成深度研究报告 | < 60秒 |

## 性能指标

### 目标指标

- **Quick Chat响应时间**: < 2秒 (P50), < 3秒 (P95), < 5秒 (P99)
- **Hotspots响应时间**: < 1秒 (P95)
- **Autocomplete响应时间**: < 500ms (P95)
- **Market Data响应时间**: < 800ms (P95)
- **Deep Research响应时间**: < 60秒
- **错误率**: < 0.1%
- **并发支持**: 1000+用户
- **吞吐量**: > 1000 RPS

### 观察指标

在Locust Web界面中关注：

1. **Requests/s (RPS)**: 每秒请求数
2. **Response Time (P50/P95/P99)**: 响应时间分位数
3. **Failure Rate**: 失败率
4. **Total Requests**: 总请求数

## 高并发优化

### 系统配置

为了支持1000+并发用户，需要优化系统配置：

#### 1. 文件描述符限制
```bash
# 查看当前限制
ulimit -n

# 临时提高限制
ulimit -n 65536

# 永久设置 (/etc/security/limits.conf)
* soft nofile 65536
* hard nofile 65536
```

#### 2. 网络配置
```bash
# 增加端口范围
echo 'net.ipv4.ip_local_port_range = 1024 65535' >> /etc/sysctl.conf

# 优化TCP连接
echo 'net.ipv4.tcp_tw_reuse = 1' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_fin_timeout = 30' >> /etc/sysctl.conf

# 应用配置
sysctl -p
```

#### 3. Locust配置优化
- 使用gevent协程提高并发
- 调整连接池大小
- 优化请求间隔时间
- 实现智能重试机制

### 负载测试环境

#### 本地环境
```bash
# 推荐配置
- CPU: 8核以上
- 内存: 16GB以上
- 网络: 千兆网络
- 磁盘: SSD
```

#### 云端环境
```bash
# AWS EC2 推荐实例
- m5.2xlarge (8 vCPU, 32GB RAM)
- c5.4xlarge (16 vCPU, 32GB RAM) 
- 或更高配置实例
```

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

### 基础测试
- [ ] 本地环境冒烟测试（50用户）
- [ ] 功能完整性测试（200用户）
- [ ] 检查响应时间是否符合目标
- [ ] 检查错误率是否 < 0.1%

### 负载测试
- [ ] 1000并发负载测试（5分钟）
- [ ] 1500并发高负载测试（10分钟）
- [ ] 2000并发峰值测试（3分钟）
- [ ] 3000并发压力测试（15分钟）

### 生产验证
- [ ] 生产环境性能验证（100用户）
- [ ] 记录性能基准数据
- [ ] 识别性能瓶颈
- [ ] 实施优化措施
- [ ] 重新测试验证改进
- [ ] 生成性能报告

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

### 1000并发测试结果

```
=====================================================================================================
 Name                                    # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
-----------------------------------------------------------------------------------------------------
 GET /api/v1/trending/hotspots             5241            2  |     142      38     892     125  |    87.4        0.0
 GET /api/v1/search/autocomplete           3420            1  |      78      28     456      68  |    57.0        0.0
 GET /api/v1/market/data                   1180            0  |      95      42     234      85  |    19.7        0.0
 POST /api/v1/chat/quick-chat             18567           15  |    1876     234    4567    1654  |   309.5        0.3
 POST /api/v1/chat/deep-research            1185            8  |   28456   19876   45234   26789  |    19.8        0.1
-----------------------------------------------------------------------------------------------------
 Aggregated                               29593           26  |    3234      28   45234    1432  |   493.2        0.4

Response time percentiles (approximated)
 Type     Name                                                           50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
--------|-----------------------------------------------------------|--------|------|------|------|------|------|------|------|------|------|------|------|
 GET      /api/v1/trending/hotspots                                      125    135    148    156    178    198    234    289    456    789    892   5241
 GET      /api/v1/search/autocomplete                                     68     75     82     89    102    118    134    156    234    389    456   3420
 GET      /api/v1/market/data                                             85     89     95    102    112    125    145    167    189    212    234   1180
 POST     /api/v1/chat/quick-chat                                       1654   1789   1923   2034   2245   2478   2789   3124   3456   3987   4567  18567
 POST     /api/v1/chat/deep-research                                   26789  28901  30123  31234  33456  35678  37890  39876  41234  43210  45234   1185
--------|-----------------------------------------------------------|--------|------|------|------|------|------|------|------|------|------|------|------|
         Aggregated                                                     1432   1678   1923   2134   2456   2789   3234   3789   4567  12345  45234  29593
```

### 性能指标总结

```
📊 Performance Summary:
========================
Total Requests: 29,593
Failed Requests: 26
Failure Rate: 0.09% ✅ (< 0.1%)
Avg Response Time: 3,234ms
RPS: 493.2
P95 Response Time: 2,789ms ✅ (< 3,000ms)
P99 Response Time: 3,789ms

✅ All performance targets met!
```

## 参考资料

- [Locust官方文档](https://docs.locust.io/)
- [API性能优化最佳实践](https://docs.locust.io/en/stable/best-practices.html)
- [高并发负载测试指南](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [性能监控和分析](https://docs.locust.io/en/stable/running-without-web-ui.html)

## 相关文件

- `locustfile.py` - 主要负载测试脚本
- `load_test_config.py` - 测试场景配置
- `run_load_tests.sh` - 批量测试脚本
- `reports/` - 测试报告目录
