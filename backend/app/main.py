"""
FastAPI Application Entrypoint
Initializes the application, registers middleware, and mounts route modules
"""

import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.request_size_limiter import RequestSizeLimiterMiddleware
from app.middleware.sql_injection_protection import SQLInjectionProtectionMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.logging_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance

    Returns:
        FastAPI: Configured application instance
    """
    # Initialize FastAPI app
    app = FastAPI(
        title=settings.project_name,
        version=settings.version,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        debug=settings.debug,
    )

    # Register middleware in correct order (outermost to innermost)
    # Order matters: Request Size Limiter → SQL Injection Protection → CORS

    # 1. Request Size Limiter (outermost - reject oversized requests first)
    if settings.request_size_limit_enabled:
        logger.info(f"Enabling RequestSizeLimiterMiddleware (max: {settings.request_max_size} bytes)")
        app.add_middleware(
            RequestSizeLimiterMiddleware,
            max_size=settings.request_max_size,
            max_upload_size=settings.request_max_upload_size,
            enabled=settings.request_size_limit_enabled,
            ip_block_duration=settings.ip_block_duration,
        )
    else:
        logger.warning("RequestSizeLimiterMiddleware is DISABLED")

    # 2. SQL Injection Protection (validate input before processing)
    if settings.sql_injection_protection_enabled:
        mode = "log-only" if settings.sql_injection_log_only else "blocking"
        logger.info(f"Enabling SQLInjectionProtectionMiddleware (mode: {mode})")
        app.add_middleware(
            SQLInjectionProtectionMiddleware,
            enabled=settings.sql_injection_protection_enabled,
            log_only=settings.sql_injection_log_only,
        )
    else:
        logger.warning("SQLInjectionProtectionMiddleware is DISABLED")

    # 3. CORS (innermost - handle cross-origin policies)
    logger.info(f"Enabling CORS for origins: {settings.cors_allow_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        allow_credentials=settings.cors_allow_credentials,
        max_age=settings.cors_max_age,
    )

    # Register route modules
    try:
        from app.api.v1.analytics import router as analytics_router
        from app.api.v1.reports import router as reports_router

        app.include_router(analytics_router, prefix=f"{settings.api_prefix}/analytics", tags=["Analytics"])
        app.include_router(reports_router, prefix=f"{settings.api_prefix}/reports", tags=["Reports"])
        logger.info("Successfully registered route modules: analytics, reports")
    except ImportError as e:
        logger.error(f"Failed to import route modules: {e}")
        logger.warning("Analytics/Reports routes disabled; continuing startup with core health endpoints only")

    # Health check endpoint (no authentication required)
    @app.get("/health", tags=["System"])
    async def health_check():
        """
        Health check endpoint to verify service status

        Returns:
            dict: Service health status and metadata
        """
        return {
            "status": "healthy",
            "service": settings.project_name,
            "version": settings.version,
            "middleware": {
                "request_size_limiter": settings.request_size_limit_enabled,
                "sql_injection_protection": settings.sql_injection_protection_enabled,
            },
        }

    # Root endpoint
    @app.get("/", tags=["System"])
    async def root():
        """
        Root endpoint with API information

        Returns:
            dict: API metadata and links
        """
        return {
            "service": settings.project_name,
            "version": settings.version,
            "docs": f"{settings.api_prefix}/docs",
            "openapi": f"{settings.api_prefix}/openapi.json",
        }

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Log application startup"""
        logger.info(f"🚀 {settings.project_name} v{settings.version} starting up")
        logger.info(f"   API prefix: {settings.api_prefix}")
        logger.info(f"   Debug mode: {settings.debug}")
        logger.info(f"   Docs: http://{settings.host}:{settings.port}{settings.api_prefix}/docs")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Log application shutdown"""
        logger.info(f"🛑 {settings.project_name} shutting down")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unhandled errors

        Args:
            request: The incoming request
            exc: The exception that was raised

        Returns:
            JSONResponse: Error response with 500 status code
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal server error occurred",
                    "status": 500,
                }
            },
        )

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.logging_level.lower(),
    )
