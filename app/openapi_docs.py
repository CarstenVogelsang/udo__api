"""
Custom OpenAPI documentation with role-based filtering.

Provides separate Swagger UI endpoints for different user roles:
- /docs         → Public (only System endpoints)
- /docs/partner → Partner (System + Partner Geodaten) - with Authorize button
- /docs/admin   → Superadmin (all endpoints) - with Authorize button

Authentication is done via the "Authorize" button in Swagger UI,
not by protecting the docs pages themselves.
"""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

# Tag-Konfiguration pro Rolle
ROLE_TAGS = {
    "public": ["System"],
    "partner": ["System", "Partner Geodaten"],
    "superadmin": ["System", "Partner Geodaten", "Geodaten", "Admin"],
}


def get_filtered_openapi(
    app: FastAPI,
    allowed_tags: list[str],
    include_security: bool = False
) -> dict:
    """
    Generiert gefiltertes OpenAPI-Schema basierend auf Tags.

    Args:
        app: FastAPI Anwendung
        allowed_tags: Liste der erlaubten Tags
        include_security: Ob Security-Schema für Authorize-Button hinzugefügt werden soll

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

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=filtered_routes,
    )

    # Security-Schema für Authorize-Button hinzufügen
    if include_security:
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API-Key für Authentifizierung. "
                               "Partner erhalten eingeschränkten Zugriff, "
                               "Superadmins haben Vollzugriff."
            }
        }
        # Globale Security-Anforderung setzen
        openapi_schema["security"] = [{"APIKeyHeader": []}]

    return openapi_schema


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
    async def docs_partner():
        """
        Partner API-Dokumentation (System + Partner Geodaten).

        Die Seite ist öffentlich zugänglich.
        Authentifizierung erfolgt über den "Authorize"-Button in Swagger UI.
        """
        return get_swagger_ui_html(
            openapi_url="/openapi-partner.json",
            title=f"{app.title} - Partner",
        )

    @app.get("/openapi-partner.json", include_in_schema=False)
    async def openapi_partner():
        """Partner OpenAPI-Schema mit Security-Definition."""
        return JSONResponse(
            get_filtered_openapi(app, ROLE_TAGS["partner"], include_security=True)
        )

    # ============ Admin-Dokumentation ============

    @app.get("/docs/admin", include_in_schema=False)
    async def docs_admin():
        """
        Admin API-Dokumentation (alle Endpunkte).

        Die Seite ist öffentlich zugänglich.
        Authentifizierung erfolgt über den "Authorize"-Button in Swagger UI.
        """
        return get_swagger_ui_html(
            openapi_url="/openapi-admin.json",
            title=f"{app.title} - Admin",
        )

    @app.get("/openapi-admin.json", include_in_schema=False)
    async def openapi_admin():
        """Vollständiges OpenAPI-Schema mit Security-Definition."""
        return JSONResponse(
            get_filtered_openapi(app, ROLE_TAGS["superadmin"], include_security=True)
        )

    # ============ ReDoc Varianten ============

    @app.get("/redoc", include_in_schema=False)
    async def redoc_public():
        """Öffentliche ReDoc-Dokumentation."""
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Dokumentation",
        )

    @app.get("/redoc/partner", include_in_schema=False)
    async def redoc_partner():
        """Partner ReDoc-Dokumentation."""
        return get_redoc_html(
            openapi_url="/openapi-partner.json",
            title=f"{app.title} - Partner",
        )

    @app.get("/redoc/admin", include_in_schema=False)
    async def redoc_admin():
        """Admin ReDoc-Dokumentation."""
        return get_redoc_html(
            openapi_url="/openapi-admin.json",
            title=f"{app.title} - Admin",
        )
