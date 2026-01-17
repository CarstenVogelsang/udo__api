"""
API Routes for License management.

Provides:
- Admin CRUD for licenses
- License lifecycle operations (activate, cancel, etc.)
- License check endpoint for satellites
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.lizenz import LizenzService
from app.services.plugin import ProjektService
from app.schemas.plugin import (
    PlgLizenzBase,
    PlgLizenzDetail,
    PlgLizenzList,
    PlgLizenzCreate,
    PlgLizenzUpdate,
    PlgLizenzKuendigung,
    PlgLizenzHistorieBase,
    PlgLizenzHistorieList,
    PlgLizenzCheck,
)


# =============================================================================
# Admin Routes
# =============================================================================

admin_router = APIRouter(prefix="/lizenzen", tags=["Lizenzen (Admin)"])


@admin_router.get("", response_model=PlgLizenzList)
async def list_lizenzen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    projekt_id: str | None = Query(None, description="Filter nach Projekt"),
    plugin_id: str | None = Query(None, description="Filter nach Plugin"),
    status: str | None = Query(None, description="Filter nach Status"),
    nur_aktiv: bool = Query(False, description="Nur aktive Lizenzen"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Liste aller Lizenzen (nur Superadmin)."""
    service = LizenzService(db)
    return await service.get_list(
        projekt_id=projekt_id,
        plugin_id=plugin_id,
        status=status,
        nur_aktiv=nur_aktiv,
        skip=skip,
        limit=limit,
    )


@admin_router.get("/{lizenz_id}", response_model=PlgLizenzDetail)
async def get_lizenz(
    lizenz_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Einzelne Lizenz abrufen (nur Superadmin)."""
    service = LizenzService(db)
    lizenz = await service.get_by_id(lizenz_id)
    if not lizenz:
        raise HTTPException(status_code=404, detail="Lizenz nicht gefunden")
    return lizenz


@admin_router.post("", response_model=PlgLizenzDetail, status_code=status.HTTP_201_CREATED)
async def create_lizenz(
    data: PlgLizenzCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neue Lizenz erstellen (nur Superadmin).

    Wenn `ist_testphase=true`, wird die Testdauer automatisch
    basierend auf dem Projekttyp berechnet.
    """
    service = LizenzService(db)
    lizenz = await service.create(
        projekt_id=data.projekt_id,
        plugin_id=data.plugin_id,
        preis_id=data.preis_id,
        ist_testphase=data.ist_testphase,
        lizenz_ende=data.lizenz_ende,
        notizen=data.notizen,
    )
    if not lizenz:
        raise HTTPException(
            status_code=400,
            detail="Lizenz konnte nicht erstellt werden (Projekt/Plugin nicht gefunden oder bereits lizenziert)"
        )
    return lizenz


@admin_router.put("/{lizenz_id}", response_model=PlgLizenzDetail)
async def update_lizenz(
    lizenz_id: str,
    data: PlgLizenzUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Lizenz aktualisieren (nur Superadmin)."""
    service = LizenzService(db)
    lizenz = await service.update(lizenz_id, **data.model_dump(exclude_unset=True))
    if not lizenz:
        raise HTTPException(status_code=404, detail="Lizenz nicht gefunden")
    return lizenz


# =============================================================================
# Lifecycle Operations
# =============================================================================

@admin_router.post("/{lizenz_id}/aktivieren", response_model=PlgLizenzDetail)
async def aktivieren_lizenz(
    lizenz_id: str,
    preis_id: str | None = Query(None, description="Preis-ID für die Aktivierung"),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Testphase in Vollversion umwandeln (nur Superadmin).

    Kann nur auf Lizenzen mit Status 'testphase' angewendet werden.
    """
    service = LizenzService(db)
    lizenz = await service.aktivieren(lizenz_id, preis_id=preis_id)
    if not lizenz:
        raise HTTPException(
            status_code=400,
            detail="Lizenz nicht gefunden oder nicht im Testphasen-Status"
        )
    return lizenz


@admin_router.post("/{lizenz_id}/kuendigen", response_model=PlgLizenzDetail)
async def kuendigen_lizenz(
    lizenz_id: str,
    data: PlgLizenzKuendigung,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lizenz kündigen (nur Superadmin).

    Die Lizenz bleibt bis zum effektiven Kündigungsdatum aktiv.
    """
    service = LizenzService(db)
    lizenz = await service.kuendigen(
        lizenz_id,
        grund=data.grund,
        zum=data.zum,
    )
    if not lizenz:
        raise HTTPException(
            status_code=400,
            detail="Lizenz nicht gefunden oder nicht kündigbar"
        )
    return lizenz


@admin_router.post("/{lizenz_id}/stornieren", response_model=PlgLizenzDetail)
async def stornieren_lizenz(
    lizenz_id: str,
    grund: str | None = Query(None, description="Stornierungsgrund"),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lizenz sofort stornieren (nur Superadmin).

    **VORSICHT:** Die Lizenz wird sofort ungültig!
    Nur für Vertragsverletzungen oder Betrug verwenden.
    """
    service = LizenzService(db)
    lizenz = await service.stornieren(lizenz_id, grund=grund)
    if not lizenz:
        raise HTTPException(status_code=404, detail="Lizenz nicht gefunden")
    return lizenz


@admin_router.post("/{lizenz_id}/pausieren", response_model=PlgLizenzDetail)
async def pausieren_lizenz(
    lizenz_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lizenz temporär pausieren (nur Superadmin).

    Kann nur auf aktive Lizenzen angewendet werden.
    """
    service = LizenzService(db)
    lizenz = await service.pausieren(lizenz_id)
    if not lizenz:
        raise HTTPException(
            status_code=400,
            detail="Lizenz nicht gefunden oder nicht pausierbar"
        )
    return lizenz


@admin_router.post("/{lizenz_id}/fortsetzen", response_model=PlgLizenzDetail)
async def fortsetzen_lizenz(
    lizenz_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Pausierte Lizenz fortsetzen (nur Superadmin).

    Kann nur auf pausierte Lizenzen angewendet werden.
    """
    service = LizenzService(db)
    lizenz = await service.fortsetzen(lizenz_id)
    if not lizenz:
        raise HTTPException(
            status_code=400,
            detail="Lizenz nicht gefunden oder nicht fortsetzbar"
        )
    return lizenz


# =============================================================================
# History
# =============================================================================

@admin_router.get("/{lizenz_id}/historie", response_model=PlgLizenzHistorieList)
async def get_lizenz_historie(
    lizenz_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Lizenz-Historie abrufen (nur Superadmin)."""
    service = LizenzService(db)

    # Verify license exists
    lizenz = await service.get_by_id(lizenz_id)
    if not lizenz:
        raise HTTPException(status_code=404, detail="Lizenz nicht gefunden")

    historie = await service.get_historie(lizenz_id)
    return {"items": historie}


# =============================================================================
# Maintenance
# =============================================================================

@admin_router.post("/maintenance/expire-trials")
async def expire_trials(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Abgelaufene Testphasen markieren (nur Superadmin).

    Sollte täglich als Cron-Job aufgerufen werden.
    """
    service = LizenzService(db)
    count = await service.expire_trials()
    return {"expired_trials": count}


@admin_router.post("/maintenance/expire-cancelled")
async def expire_cancelled(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Gekündigte Lizenzen nach Ablauf markieren (nur Superadmin).

    Sollte täglich als Cron-Job aufgerufen werden.
    """
    service = LizenzService(db)
    count = await service.expire_cancelled()
    return {"expired_cancelled": count}


# =============================================================================
# Satellite License Check (Public/API-Key Auth)
# =============================================================================

check_router = APIRouter(prefix="/lizenz-check", tags=["Lizenz-Check (Satelliten)"])


@check_router.get("/{plugin_slug}", response_model=PlgLizenzCheck)
async def check_lizenz(
    plugin_slug: str,
    db: AsyncSession = Depends(get_db),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """
    Lizenz für ein Plugin prüfen (für Satelliten-Projekte).

    **Authentifizierung:**
    - Header `X-API-Key` mit dem API-Key des Projekts

    **Response:**
    - `lizenziert`: true/false
    - `status`: aktueller Lizenz-Status
    - `lizenz_ende`: Ablaufdatum
    - `plugin_version`: aktuelle Plugin-Version
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API-Key erforderlich (Header: X-API-Key)"
        )

    # Get project by API key
    projekt_service = ProjektService(db)
    projekt = await projekt_service.get_by_api_key(x_api_key)

    if not projekt:
        raise HTTPException(
            status_code=401,
            detail="Ungültiger API-Key oder Projekt deaktiviert"
        )

    # Check license
    lizenz_service = LizenzService(db)
    return await lizenz_service.check_lizenz(
        projekt_id=str(projekt.id),
        plugin_slug=plugin_slug,
    )
