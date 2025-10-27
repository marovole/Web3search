# 数据库维护指南

PostgreSQL数据库日常维护、备份和恢复指南。

## 日常维护

### VACUUM清理

```bash
# 1. 常规VACUUM（每周）
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# 2. VACUUM FULL（每月，需要停机）
# 会重建表，回收空间
psql $DATABASE_URL -c "VACUUM FULL;"

# 3. 自动VACUUM配置
psql $DATABASE_URL -c "
ALTER TABLE reports SET (
  autovacuum_vacuum_scale_factor = 0.1,
  autovacuum_analyze_scale_factor = 0.05
);"
```

### 重建索引

```bash
# 1. 查看索引膨胀
psql $DATABASE_URL -c "
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;"

# 2. 重建索引（每月）
psql $DATABASE_URL -c "REINDEX TABLE reports;"

# 3. 并发重建（不锁表）
psql $DATABASE_URL -c "REINDEX INDEX CONCURRENTLY idx_reports_symbol;"
```

### 统计信息更新

```bash
# 更新表统计信息
psql $DATABASE_URL -c "ANALYZE reports;"

# 查看统计信息时效
psql $DATABASE_URL -c "
SELECT schemaname, tablename, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY last_analyze DESC NULLS LAST;"
```

## 备份策略

### 备份类型

**1. 逻辑备份（pg_dump）**
```bash
# 备份整个数据库
pg_dump $DATABASE_URL -Fc > backup_$(date +%Y%m%d).dump

# 备份特定表
pg_dump $DATABASE_URL -t reports -Fc > reports_backup.dump

# 备份到S3
pg_dump $DATABASE_URL -Fc | aws s3 cp - s3://backups/db_$(date +%Y%m%d).dump
```

**2. 物理备份（pg_basebackup）**
```bash
# 完整物理备份
pg_basebackup -D /backup/base -Ft -z -P -h $DB_HOST -U $DB_USER

# 连续归档WAL（用于PITR）
# postgresql.conf:
# archive_mode = on
# archive_command = 'cp %p /archive/%f'
```

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
RETENTION_DAYS=30

# 执行备份
pg_dump $DATABASE_URL -Fc > "$BACKUP_DIR/backup_$DATE.dump"

# 上传到S3
aws s3 cp "$BACKUP_DIR/backup_$DATE.dump" "s3://web3search-backups/"

# 清理旧备份
find $BACKUP_DIR -name "backup_*.dump" -mtime +$RETENTION_DAYS -delete

# 验证备份
pg_restore --list "$BACKUP_DIR/backup_$DATE.dump" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backup successful: backup_$DATE.dump"
else
    echo "❌ Backup failed!"
    exit 1
fi
```

### 定时任务（cron）

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1

# 每周日凌晨3点执行VACUUM
0 3 * * 0 psql $DATABASE_URL -c "VACUUM ANALYZE;" >> /var/log/vacuum.log 2>&1
```

## 恢复流程

### 完整恢复

```bash
# 1. 创建新数据库（如需）
createdb -h $DB_HOST -U $DB_USER web3search_restore

# 2. 恢复备份
pg_restore -d web3search_restore -Fc backup_20250127.dump

# 3. 验证数据
psql web3search_restore -c "SELECT COUNT(*) FROM reports;"

# 4. 切换数据库（更新DATABASE_URL）
export DATABASE_URL="postgresql://...web3search_restore"
```

### 时间点恢复（PITR）

```bash
# 1. 恢复基础备份
pg_basebackup -D /data/pgdata

# 2. 配置recovery.conf
restore_command = 'cp /archive/%f %p'
recovery_target_time = '2025-01-27 10:00:00'

# 3. 启动PostgreSQL
pg_ctl start -D /data/pgdata

# 4. 验证恢复点
psql -c "SELECT pg_last_xact_replay_timestamp();"
```

### 表级恢复

```bash
# 1. 恢复单个表
pg_restore -d $DATABASE_URL -t reports backup.dump

# 2. 恢复到临时表
pg_restore -d $DATABASE_URL --schema=temp backup.dump

# 3. 对比数据
psql $DATABASE_URL -c "
SELECT COUNT(*) as prod_count FROM reports
UNION ALL
SELECT COUNT(*) as backup_count FROM temp.reports;"
```

## 性能优化

### 慢查询分析

```sql
-- 1. 启用pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 2. 查看Top 10慢查询
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 3. 分析查询计划
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM reports WHERE symbol = 'BTC';
```

### 索引优化

```sql
-- 1. 查找缺失索引
SELECT schemaname, tablename, attname
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.1;

-- 2. 创建必要索引
CREATE INDEX CONCURRENTLY idx_reports_created_at 
ON reports(created_at DESC);

CREATE INDEX CONCURRENTLY idx_reports_status 
ON reports(status) WHERE status = 'completed';

-- 3. 复合索引
CREATE INDEX CONCURRENTLY idx_reports_symbol_date 
ON reports(symbol, created_at DESC);
```

### 连接池优化

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # 最小连接数（从10增加）
    max_overflow=80,     # 最大溢出（从40增加）
    pool_pre_ping=True,  # 检测断开连接
    pool_recycle=3600,   # 1小时回收连接
    echo_pool=True,      # 记录连接池事件
)
```

## 监控和告警

### 关键指标

```sql
-- 1. 数据库大小
SELECT pg_size_pretty(pg_database_size(current_database()));

-- 2. 表大小
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 3. 活跃连接
SELECT count(*), state FROM pg_stat_activity 
GROUP BY state;

-- 4. 锁等待
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_locks blocking_locks 
  ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;

-- 5. 缓存命中率
SELECT 
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

### 告警配置

```python
# app/core/database_monitor.py
async def check_database_health():
    # 1. 连接数
    conn_count = await get_connection_count()
    if conn_count > 80:
        alert("Database connections > 80")
    
    # 2. 慢查询
    slow_queries = await get_slow_queries()
    if len(slow_queries) > 10:
        alert(f"Too many slow queries: {len(slow_queries)}")
    
    # 3. 锁等待
    locks = await get_lock_waits()
    if len(locks) > 0:
        alert(f"Deadlocks detected: {locks}")
```

## 数据清理

### 归档旧数据

```sql
-- 1. 归档90天前的报告
INSERT INTO reports_archive
SELECT * FROM reports
WHERE created_at < NOW() - INTERVAL '90 days';

-- 2. 删除已归档数据
DELETE FROM reports
WHERE created_at < NOW() - INTERVAL '90 days';

-- 3. VACUUM回收空间
VACUUM ANALYZE reports;
```

### 定期清理脚本

```python
# cleanup.py
import asyncio
from app.core.database import get_db

async def cleanup_old_data():
    async with get_db() as db:
        # 删除90天前的失败报告
        result = await db.execute(
            "DELETE FROM reports WHERE status='failed' "
            "AND created_at < NOW() - INTERVAL '90 days'"
        )
        print(f"Deleted {result.rowcount} failed reports")
        
        # 删除孤立的对话记录
        result = await db.execute(
            "DELETE FROM messages WHERE conversation_id NOT IN "
            "(SELECT id FROM conversations)"
        )
        print(f"Deleted {result.rowcount} orphaned messages")

if __name__ == "__main__":
    asyncio.run(cleanup_old_data())
```

---

**版本**: v1.0.0
**最后更新**: 2025-01-27
**维护者**: Web3Search DBA Team
