"""
API Routes for Projekt (Satellite) administration.

Provides CRUD operations for satellite projects and their licenses.
All endpoints require superadmin authentication.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.plugin import ProjektService
from app.services.lizenz import LizenzService
from app.schemas.plugin import (
    PlgProjektBase,
    PlgProjektDetail,
    PlgProjektList,
    PlgProjektCreate,
    PlgProjektUpdate,
    PlgProjektApiKeyResponse,
    PlgLizenzBase,
    PlgLizenzDetail,
    PlgLizenzList,
    PlgLizenzCreate,
    PlgLizenzKuendigung,
    PlgLizenzHistorieBase,
    PlgLizenzHistorieList,
)

router = APIRouter(prefix="/projekte", tags=["Projekte (Admin)"])


# =============================================================================
# Projekt Routes
# =============================================================================

@router.get("", response_model=PlgProjektList)
async def list_projekte(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    projekttyp_id: str | None = Query(None, description="Filter nach Projekttyp"),
    nur_aktiv: bool = Query(True, description="Nur aktive Projekte"),
    suche: str | None = Query(None, min_length=2, description="Textsuche"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Liste aller Projekte (nur Superadmin)."""
    service = ProjektService(db)
    return await service.get_list(
        projekttyp_id=projekttyp_id,
        nur_aktiv=nur_aktiv,
        suche=suche,
        skip=skip,
        limit=limit,
    )


@router.get("/{projekt_id}", response_model=PlgProjektDetail)
async def get_projekt(
    projekt_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Einzelnes Projekt abrufen (nur Superadmin)."""
    service = ProjektService(db)
    projekt = await service.get_by_id(projekt_id)
    if not projekt:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return projekt


@router.post("", response_model=PlgProjektDetail, status_code=status.HTTP_201_CREATED)
async def create_projekt(
    data: PlgProjektCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neues Projekt erstellen (nur Superadmin)."""
    service = ProjektService(db)

    # Check if slug already exists
    existing = await service.get_by_slug(data.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Slug bereits vergeben")

    return await service.create(**data.model_dump())


@router.put("/{projekt_id}", response_model=PlgProjektDetail)
async def update_projekt(
    projekt_id: str,
    data: PlgProjektUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Projekt aktualisieren (nur Superadmin)."""
    service = ProjektService(db)
    projekt = await service.update(projekt_id, **data.model_dump(exclude_unset=True))
    if not projekt:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return projekt


@router.delete("/{projekt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_projekt(
    projekt_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Projekt deaktivieren (nur Superadmin)."""
    service = ProjektService(db)
    if not await service.deactivate(projekt_id):
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")


@router.post("/{projekt_id}/api-key", response_model=PlgProjektApiKeyResponse)
async def generate_api_key(
    projekt_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neuen API-Key für Projekt generieren (nur Superadmin).

    **WICHTIG:** Der API-Key wird nur einmal angezeigt!
    Er wird gehasht in der Datenbank gespeichert und kann nicht wiederhergestellt werden.
    """
    service = ProjektService(db)
    api_key = await service.generate_api_key(projekt_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    return PlgProjektApiKeyResponse(api_key=api_key)


# =============================================================================
# Projekt-Lizenzen Routes
# =============================================================================

@router.get("/{projekt_id}/lizenzen", response_model=PlgLizenzList)
async def list_projekt_lizenzen(
    projekt_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None, description="Filter nach Status"),
    nur_aktiv: bool = Query(False, description="Nur aktive Lizenzen"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Alle Lizenzen eines Projekts abrufen (nur Superadmin)."""
    # Verify project exists
    projekt_service = ProjektService(db)
    projekt = await projekt_service.get_by_id(projekt_id)
    if not projekt:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    lizenz_service = LizenzService(db)
    return await lizenz_service.get_list(
        projekt_id=projekt_id,
        status=status,
        nur_aktiv=nur_aktiv,
        skip=skip,
        limit=limit,
    )


@router.post("/{projekt_id}/lizenzen", response_model=PlgLizenzDetail, status_code=status.HTTP_201_CREATED)
async def create_projekt_lizenz(
    projekt_id: str,
    data: PlgLizenzCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neue Lizenz für Projekt erstellen (nur Superadmin).

    Wenn `ist_testphase=true`, wird die Testdauer automatisch
    basierend auf dem Projekttyp berechnet.
    """
    # Override projekt_id from path
    lizenz_service = LizenzService(db)
    lizenz = await lizenz_service.create(
        projekt_id=projekt_id,
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
