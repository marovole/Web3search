"""
API v1 router
"""
from fastapi import APIRouter
from app.api.v1 import chat, reports, search, trending, health, metrics, cache, auth, users, github, gitlab, code_review, sentiment, websocket, apm_dashboard, business_metrics, funnel_conversion_api, dashboard_segments_api, log_analysis_api, infrastructure_api, database_monitoring_api, network_storage_api, infrastructure_recovery_api, monitoring_validation_api

# Create v1 API router
api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(trending.router, prefix="/trending", tags=["Trending"])
api_router.include_router(github.router, prefix="/github", tags=["GitHub"])
api_router.include_router(gitlab.router, prefix="/gitlab", tags=["GitLab"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(cache.router, prefix="/cache", tags=["Cache"])
api_router.include_router(code_review.router, tags=["Code Review"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["Social Sentiment"])
api_router.include_router(websocket.websocket_router, tags=["WebSocket"])
api_router.include_router(apm_dashboard.router, tags=["APM Dashboard"])
api_router.include_router(business_metrics.router, tags=["Business Metrics"])
api_router.include_router(funnel_conversion_api.router, tags=["Funnel & Conversion Analytics"])
api_router.include_router(dashboard_segments_api.router, tags=["Real-time Dashboard & User Segments"])
api_router.include_router(log_analysis_api.router, tags=["Log Query & Analysis"])
api_router.include_router(infrastructure_api.router, tags=["Infrastructure Monitoring"])
api_router.include_router(database_monitoring_api.router, tags=["Database Monitoring"])
api_router.include_router(network_storage_api.router, tags=["Network & Storage Monitoring"])
api_router.include_router(infrastructure_recovery_api.router, tags=["Infrastructure Recovery"])
api_router.include_router(monitoring_validation_api.router, tags=["Monitoring Validation"])

__all__ = ["api_router"]
