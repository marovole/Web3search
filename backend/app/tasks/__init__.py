"""
Celery Async Tasks Module
Handles background data collection and scheduled updates
"""
from app.tasks.celery_app import celery_app

__all__ = ["celery_app"]
