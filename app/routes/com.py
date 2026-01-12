"""
API Routes for Company (Unternehmen) data.

All endpoints return the full GeoOrt hierarchy (Ort → Kreis → Bundesland → Land).
These endpoints are only accessible by superadmin users.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.com import ComService
from app.schemas.com import (
    ComUnternehmenWithGeo,
    ComUnternehmenDetail,
    ComUnternehmenList,
)

router = APIRouter(prefix="/unternehmen", tags=["Unternehmen"])


@router.get("", response_model=ComUnternehmenList)
async def list_unternehmen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    geo_ort_id: str | None = Query(None, description="Filter nach Ort-UUID"),
    suche: str | None = Query(
        None,
        min_length=2,
        description="Suche nach Kurzname oder Firmierung"
    ),
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
):
    """
    Liste aller Unternehmen mit vollständiger Geo-Hierarchie (nur Superadmin).

    **Filter:**
    - `geo_ort_id`: Nur Unternehmen aus diesem Ort
    - `suche`: Textsuche in Kurzname und Firmierung

    **Response:**
    Jedes Unternehmen enthält die vollständige Geo-Hierarchie:
    Ort → Kreis → Bundesland → Land
    """
    service = ComService(db)
    return await service.get_unternehmen_list(
        geo_ort_id=geo_ort_id,
        suche=suche,
        skip=skip,
        limit=limit
    )


@router.get("/{unternehmen_id}", response_model=ComUnternehmenDetail)
async def get_unternehmen(
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelnes Unternehmen mit vollständiger Geo-Hierarchie (nur Superadmin).

    - **unternehmen_id**: UUID des Unternehmens
    """
    service = ComService(db)
    unternehmen = await service.get_unternehmen_by_id(unternehmen_id)
    if not unternehmen:
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")
    return unternehmen


@router.get("/legacy/{legacy_id}", response_model=ComUnternehmenDetail)
async def get_unternehmen_by_legacy_id(
    legacy_id: int,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unternehmen nach Legacy-ID (kStore) abrufen (nur Superadmin).

    Die Legacy-ID entspricht dem Primary Key `kStore` aus der
    ursprünglichen spi_tStore Tabelle.

    - **legacy_id**: kStore aus der Legacy-Datenbank
    """
    service = ComService(db)
    unternehmen = await service.get_unternehmen_by_legacy_id(legacy_id)
    if not unternehmen:
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")
    return unternehmen


@router.get("/stats/count")
async def get_unternehmen_count(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Gesamtanzahl der Unternehmen (nur Superadmin).
    """
    service = ComService(db)
    count = await service.get_unternehmen_count()
    return {"total": count}
