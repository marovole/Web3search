# deployment Spec Delta

## MODIFIED Requirements

### Requirement: Railway后端部署
系统后端**SHALL**部署到Railway平台，包含FastAPI、PostgreSQL、Redis和Celery Worker。**集成缓存预热启动流程。**

#### Scenario: 启动时缓存预加载
- **WHEN** Railway后端服务启动
- **THEN** 在uvicorn启动后执行缓存预加载
- **AND** 预加载Top 10币种数据（< 5秒）
- **AND** 预加载日志输出到Railway Logs
- **AND** 预加载失败不阻塞服务启动
- **AND** 健康检查端点(/health)包含预加载状态

#### Scenario: 健康检查包含缓存状态
- **WHEN** 访问/health端点
- **THEN** 响应包含缓存预热信息：
  ```json
  {
    "status": "healthy",
    "cache": {
      "prewarming": {
        "status": "active",
        "last_run": "2025-01-27T12:00:00Z",
        "success_rate": 0.98,
        "cached_coins": 98
      },
      "l1_cache": {
        "size": 85,
        "capacity": 100,
        "hit_rate": 0.82
      },
      "l2_cache": {
        "size": 9850,
        "capacity": 10000,
        "hit_rate": 0.78
      }
    }
  }
  ```
- **AND** 健康检查响应时间< 100ms

#### Scenario: Celery Beat预热任务配置
- **WHEN** Celery Beat启动（Railway Cron Job）
- **THEN** 配置预热任务调度：
  - `prewarm_top10_coins`: schedule=crontab(minute='*/1')  # 每分钟
  - `prewarm_top100_coins`: schedule=crontab(minute='*/5')  # 每5分钟
  - `adjust_prewarming_list`: schedule=crontab(minute=0)  # 每小时
- **AND** 任务注册到Celery Beat scheduler
- **AND** 任务执行日志输出到Railway Logs
- **AND** 任务失败触发Sentry告警
