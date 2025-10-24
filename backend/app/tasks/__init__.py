"""
Celery异步任务模块
处理后台数据采集、定时更新等任务
"""
from app.tasks.celery_app import celery_app

__all__ = ["celery_app"]
