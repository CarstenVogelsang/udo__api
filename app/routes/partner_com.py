"""
Partner Company (Unternehmen) API routes.

Filtered company access based on partner's assigned countries.
Endpoint prefix: /partner/unternehmen
"""
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_partner_with_billing
from app.models.partner import ApiPartner
from app.services.partner_com import PartnerComService
from app.services.usage import UsageService
from app.services.billing import BillingService
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
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """
    Get companies filtered by partner's allowed countries.

    Partners can only see companies in countries assigned to them.
    If no countries are assigned, all companies are visible.
    """
    t_start = time.monotonic()

    service = PartnerComService(db, partner)
    result = await service.get_unternehmen_list(
        geo_ort_id=geo_ort_id,
        suche=suche,
        skip=skip,
        limit=limit
    )

    # Calculate costs and log usage
    anzahl = len(result["items"])
    kosten = anzahl * partner.kosten_unternehmen_pro_abfrage
    antwortzeit_ms = int((time.monotonic() - t_start) * 1000)

    usage_service = UsageService(db)
    usage = await usage_service.log_usage(
        partner_id=partner.id,
        endpoint="/partner/unternehmen/",
        methode="GET",
        status_code=200,
        anzahl_ergebnisse=anzahl,
        kosten=kosten,
        antwortzeit_ms=antwortzeit_ms,
        parameter={"suche": suche, "geo_ort_id": geo_ort_id, "skip": skip, "limit": limit},
    )

    # Deduct credits
    billing_service = BillingService(db)
    await billing_service.deduct_credits(
        partner_id=partner.id,
        kosten=kosten,
        usage_id=str(usage.id),
        beschreibung=f"{anzahl} Unternehmen abgerufen",
    )

    result["meta"] = await usage_service.get_usage_meta(partner.id, kosten)
    return result


@router.get(
    "/stats/count",
    response_model=ComUnternehmenPartnerCount,
    summary="Anzahl Unternehmen",
    description="Gibt die Gesamtzahl der für den Partner verfügbaren Unternehmen zurück.",
)
async def get_unternehmen_count(
    partner: ApiPartner = Depends(get_current_partner_with_billing),
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
    partner: ApiPartner = Depends(get_current_partner_with_billing),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single company by UUID.

    Returns 404 if company doesn't exist or is not in partner's allowed countries.
    """
    t_start = time.monotonic()

    service = PartnerComService(db, partner)
    unternehmen = await service.get_unternehmen_by_id(id)

    if not unternehmen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unternehmen nicht gefunden oder nicht im zugelassenen Bereich."
        )

    # Log usage (single result = 1)
    kosten = partner.kosten_unternehmen_pro_abfrage
    antwortzeit_ms = int((time.monotonic() - t_start) * 1000)

    usage_service = UsageService(db)
    usage = await usage_service.log_usage(
        partner_id=partner.id,
        endpoint=f"/partner/unternehmen/{id}",
        methode="GET",
        status_code=200,
        anzahl_ergebnisse=1,
        kosten=kosten,
        antwortzeit_ms=antwortzeit_ms,
    )

    # Deduct credits
    billing_service = BillingService(db)
    await billing_service.deduct_credits(
        partner_id=partner.id,
        kosten=kosten,
        usage_id=str(usage.id),
        beschreibung="1 Unternehmen abgerufen",
    )

    return unternehmen
