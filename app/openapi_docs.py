"""
Custom OpenAPI documentation with role-based filtering.

Provides separate Swagger UI endpoints for different user roles:
- /docs         → Public (only System endpoints)
- /docs/partner → Partner (System + Partner Geodaten)
- /docs/admin   → Superadmin (all endpoints)
"""
from fastapi import FastAPI, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.auth import get_current_partner, require_superadmin

# Tag-Konfiguration pro Rolle
ROLE_TAGS = {
    "public": ["System"],
    "partner": ["System", "Partner Geodaten"],
    "superadmin": ["System", "Partner Geodaten", "Geodaten", "Admin"],
}


def get_filtered_openapi(app: FastAPI, allowed_tags: list[str]) -> dict:
    """
    Generiert gefiltertes OpenAPI-Schema basierend auf Tags.

    Args:
        app: FastAPI Anwendung
        allowed_tags: Liste der erlaubten Tags

    Returns:
        Gefilterte OpenAPI-Spezifikation als Dictionary
    """
    # Routen nach Tags filtern
    filtered_routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            route_tags = route.tags or []
            # Route einschließen, wenn mindestens ein Tag übereinstimmt
            if any(tag in allowed_tags for tag in route_tags):
                filtered_routes.append(route)
        else:
            # Non-API routes (Mount, static files, etc.) einschließen
            filtered_routes.append(route)

    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=filtered_routes,
    )


def setup_docs(app: FastAPI):
    """
    Registriert die Dokumentations-Endpunkte für verschiedene Rollen.

    Args:
        app: FastAPI Anwendung
    """

    # ============ Öffentliche Dokumentation ============

    @app.get("/docs", include_in_schema=False)
    async def docs_public():
        """Öffentliche API-Dokumentation (nur System-Endpunkte)."""
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Dokumentation",
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def openapi_public():
        """Öffentliches OpenAPI-Schema (nur System-Endpunkte)."""
        return JSONResponse(get_filtered_openapi(app, ROLE_TAGS["public"]))

    # ============ Partner-Dokumentation ============

    @app.get("/docs/partner", include_in_schema=False)
    async def docs_partner(partner=Depends(get_current_partner)):
        """Partner API-Dokumentation (System + Partner Geodaten)."""
        return get_swagger_ui_html(
            openapi_url="/openapi-partner.json",
            title=f"{app.title} - Partner",
        )

    @app.get("/openapi-partner.json", include_in_schema=False)
    async def openapi_partner(partner=Depends(get_current_partner)):
        """Partner OpenAPI-Schema."""
        return JSONResponse(get_filtered_openapi(app, ROLE_TAGS["partner"]))

    # ============ Admin-Dokumentation ============

    @app.get("/docs/admin", include_in_schema=False)
    async def docs_admin(admin=Depends(require_superadmin)):
        """Admin API-Dokumentation (alle Endpunkte)."""
        return get_swagger_ui_html(
            openapi_url="/openapi-admin.json",
            title=f"{app.title} - Admin",
        )

    @app.get("/openapi-admin.json", include_in_schema=False)
    async def openapi_admin(admin=Depends(require_superadmin)):
        """Vollständiges OpenAPI-Schema (alle Endpunkte)."""
        return JSONResponse(get_filtered_openapi(app, ROLE_TAGS["superadmin"]))

    # ============ ReDoc Varianten ============

    @app.get("/redoc", include_in_schema=False)
    async def redoc_public():
        """Öffentliche ReDoc-Dokumentation."""
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Dokumentation",
        )

    @app.get("/redoc/partner", include_in_schema=False)
    async def redoc_partner(partner=Depends(get_current_partner)):
        """Partner ReDoc-Dokumentation."""
        return get_redoc_html(
            openapi_url="/openapi-partner.json",
            title=f"{app.title} - Partner",
        )

    @app.get("/redoc/admin", include_in_schema=False)
    async def redoc_admin(admin=Depends(require_superadmin)):
        """Admin ReDoc-Dokumentation."""
        return get_redoc_html(
            openapi_url="/openapi-admin.json",
            title=f"{app.title} - Admin",
        )
