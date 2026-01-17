"""
FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes.geo import router as geo_router
from app.routes.partner_geo import router as partner_geo_router
from app.routes.partner_com import router as partner_com_router
from app.routes.admin import router as admin_router
from app.routes.etl import router as etl_router
from app.routes.com import router as com_router
from app.routes.organisation import router as organisation_router
from app.routes.auth import router as auth_router
from app.routes.plugin import router as plugin_router
from app.routes.projekt import router as projekt_router
from app.routes.lizenz import admin_router as lizenz_admin_router
from app.routes.lizenz import check_router as lizenz_check_router
from app.openapi_docs import setup_docs

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        title=settings.api_title,
        description="Unternehmensdaten API - Geodaten Service für deutsche Verwaltungseinheiten",
        version=settings.api_version,
        lifespan=lifespan,
        # Default docs deaktivieren - wir nutzen custom role-based docs
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(auth_router, prefix=settings.api_prefix)  # Auth first (no auth required for login)
    app.include_router(geo_router, prefix=settings.api_prefix)
    app.include_router(partner_geo_router, prefix=settings.api_prefix)
    app.include_router(partner_com_router, prefix=settings.api_prefix)
    app.include_router(admin_router, prefix=settings.api_prefix)
    app.include_router(etl_router, prefix=settings.api_prefix)
    app.include_router(com_router, prefix=settings.api_prefix)
    app.include_router(organisation_router, prefix=settings.api_prefix)
    # Plugin Marketplace routers
    app.include_router(plugin_router, prefix=settings.api_prefix)
    app.include_router(projekt_router, prefix=settings.api_prefix)
    app.include_router(lizenz_admin_router, prefix=settings.api_prefix)
    app.include_router(lizenz_check_router, prefix=settings.api_prefix)

    # Setup custom role-based documentation
    setup_docs(app)

    # Root endpoints
    @app.get("/", tags=["System"])
    async def root():
        """Welcome endpoint."""
        return {
            "message": "Welcome to UDO API",
            "version": settings.api_version,
            "docs": {
                "public": "/docs",
                "partner": "/docs/partner (API-Key erforderlich)",
                "admin": "/docs/admin (Superadmin erforderlich)",
            },
        }

    @app.get("/health", tags=["System"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "udo-api",
            "version": settings.api_version,
        }

    return app


# Create the application instance
app = create_app()
