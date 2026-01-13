"""
Partner Company (Unternehmen) API routes.

Filtered company access based on partner's assigned countries.
Endpoint prefix: /partner/unternehmen
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_partner
from app.models.partner import ApiPartner
from app.services.partner_com import PartnerComService
from app.schemas.com import (
    ComUnternehmenPartner,
    ComUnternehmenPartnerList,
    ComUnternehmenPartnerCount,
)

router = APIRouter(prefix="/partner/unternehmen", tags=["Partner Unternehmen"])


@router.get(
    "/",
    response_model=ComUnternehmenPartnerList,
    summary="Unternehmen abrufen",
    description="Paginierte Liste von Unternehmen, gefiltert nach zugelassenen Ländern des Partners.",
)
async def list_unternehmen(
    suche: str | None = Query(
        None,
        min_length=2,
        description="Suche in Kurzname/Firmierung (min. 2 Zeichen)"
    ),
    geo_ort_id: str | None = Query(None, description="Filter nach Ort-UUID"),
    skip: int = Query(0, ge=0, description="Pagination Offset"),
    limit: int = Query(100, ge=1, le=1000, description="Max. Anzahl (1-1000)"),
    partner: ApiPartner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    Get companies filtered by partner's allowed countries.

    Partners can only see companies in countries assigned to them.
    If no countries are assigned, all companies are visible.
    """
    service = PartnerComService(db, partner)
    result = await service.get_unternehmen_list(
        geo_ort_id=geo_ort_id,
        suche=suche,
        skip=skip,
        limit=limit
    )
    return result


@router.get(
    "/stats/count",
    response_model=ComUnternehmenPartnerCount,
    summary="Anzahl Unternehmen",
    description="Gibt die Gesamtzahl der für den Partner verfügbaren Unternehmen zurück.",
)
async def get_unternehmen_count(
    partner: ApiPartner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    Get total count of companies the partner can access.

    Count is filtered by partner's allowed countries.
    """
    service = PartnerComService(db, partner)
    total = await service.get_unternehmen_count()
    return {"total": total}


@router.get(
    "/{id}",
    response_model=ComUnternehmenPartner,
    summary="Einzelnes Unternehmen",
    description="Gibt ein einzelnes Unternehmen mit vollständiger Geo-Hierarchie zurück.",
)
async def get_unternehmen(
    id: str,
    partner: ApiPartner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single company by UUID.

    Returns 404 if company doesn't exist or is not in partner's allowed countries.
    """
    service = PartnerComService(db, partner)
    unternehmen = await service.get_unternehmen_by_id(id)

    if not unternehmen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unternehmen nicht gefunden oder nicht im zugelassenen Bereich."
        )

    return unternehmen
