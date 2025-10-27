"""
Celery应用配置
定义Celery实例和任务调度
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


# ================================
# 创建Celery实例
# ================================

celery_app = Celery(
    "web3search",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.data_collection",
        "app.tasks.quality_check",
    ],
)

# ================================
# Celery配置
# ================================

celery_app.conf.update(
    # 时区
    timezone="UTC",
    enable_utc=True,

    # 任务结果配置
    result_expires=3600,  # 结果过期时间（秒）
    result_serializer="json",
    task_serializer="json",
    accept_content=["json"],

    # 任务执行配置
    task_track_started=True,
    task_time_limit=1800,  # 30分钟超时
    task_soft_time_limit=1500,  # 25分钟软超时
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # 日志配置
    worker_hijack_root_logger=False,
)

# ================================
# 定时任务调度
# ================================

celery_app.conf.beat_schedule = {
    # ================================
    # 价格数据更新（每分钟）
    # ================================
    "update-trending-prices": {
        "task": "app.tasks.data_collection.update_trending_coin_prices",
        "schedule": crontab(minute="*/1"),  # 每分钟
        "options": {"queue": "high_priority"},
    },

    # ================================
    # 项目快照（每小时）
    # ================================
    "snapshot-trending-projects": {
        "task": "app.tasks.data_collection.snapshot_trending_projects",
        "schedule": crontab(minute=0),  # 每小时整点
        "options": {"queue": "default"},
    },

    # ================================
    # 社交数据更新（每6小时）
    # ================================
    "update-social-data": {
        "task": "app.tasks.data_collection.update_social_data",
        "schedule": crontab(hour="*/6", minute=0),  # 每6小时
        "options": {"queue": "low_priority"},
    },

    # ================================
    # 链上数据更新（每天）
    # ================================
    "update-onchain-data": {
        "task": "app.tasks.data_collection.update_onchain_data",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点
        "options": {"queue": "low_priority"},
    },

    # ================================
    # 新闻数据采集（每30分钟）
    # ================================
    "collect-crypto-news": {
        "task": "app.tasks.data_collection.collect_crypto_news",
        "schedule": crontab(minute="*/30"),  # 每30分钟
        "options": {"queue": "default"},
    },

    # ================================
    # 清理过期缓存（每天）
    # ================================
    "cleanup-expired-cache": {
        "task": "app.tasks.data_collection.cleanup_expired_cache",
        "schedule": crontab(hour=3, minute=0),  # 每天凌晨3点
        "options": {"queue": "low_priority"},
    },

    # ================================
    # 热点识别更新（每小时）
    # ================================
    "update-hotspots": {
        "task": "app.tasks.data_collection.update_hotspots",
        "schedule": crontab(minute=15),  # 每小时的第15分钟
        "options": {"queue": "default"},
    },

    # ================================
    # 数据质量报告生成（每小时）- 任务6.7
    # ================================
    "generate-data-quality-report": {
        "task": "app.tasks.quality_check.generate_data_quality_report",
        "schedule": crontab(minute=30),  # 每小时的第30分钟
        "options": {"queue": "default"},
    },
}

# ================================
# 队列路由配置
# ================================

celery_app.conf.task_routes = {
    "app.tasks.data_collection.update_trending_coin_prices": {"queue": "high_priority"},
    "app.tasks.data_collection.snapshot_trending_projects": {"queue": "default"},
    "app.tasks.data_collection.update_social_data": {"queue": "low_priority"},
    "app.tasks.data_collection.update_onchain_data": {"queue": "low_priority"},
    "app.tasks.data_collection.collect_crypto_news": {"queue": "default"},
    "app.tasks.data_collection.cleanup_expired_cache": {"queue": "low_priority"},
    "app.tasks.data_collection.update_hotspots": {"queue": "default"},
    "app.tasks.quality_check.generate_data_quality_report": {"queue": "default"},
}
