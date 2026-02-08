"""
Admin API routes for partner management and usage monitoring.

Only accessible by superadmin users.
Endpoint prefix: /admin
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.partner import PartnerService
from app.services.usage import UsageService
from app.schemas.partner import (
    ApiPartnerCreate,
    ApiPartnerUpdate,
    ApiPartnerResponse,
    ApiPartnerWithKey,
    ApiPartnerList,
)
from app.schemas.usage import (
    UsageAdminUebersichtList,
    UsageAdminPartnerDetail,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/partners",
    response_model=ApiPartnerList,
    summary="Alle Partner auflisten",
    description="Gibt eine Liste aller registrierten API-Partner zurück.",
)
async def list_partners(
    skip: int = Query(0, ge=0, description="Anzahl zu überspringender Einträge"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Einträge"),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List all partners (superadmin only)."""
    service = PartnerService(db)
    result = await service.get_partners(skip=skip, limit=limit)
    return result


@router.post(
    "/partners",
    response_model=ApiPartnerWithKey,
    status_code=status.HTTP_201_CREATED,
    summary="Neuen Partner erstellen",
    description="Erstellt einen neuen API-Partner und gibt den API-Key **einmalig** zurück.",
)
async def create_partner(
    data: ApiPartnerCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new partner (superadmin only).

    **IMPORTANT**: The API key is only shown once in this response!
    Store it securely, as it cannot be retrieved later.
    """
    service = PartnerService(db)
    partner, api_key = await service.create_partner(data)

    # Return partner with the plain API key (only this once!)
    return ApiPartnerWithKey(
        id=partner.id,
        name=partner.name,
        email=partner.email,
        role=partner.role,
        kosten_geoapi_pro_einwohner=partner.kosten_geoapi_pro_einwohner,
        is_active=partner.is_active,
        erstellt_am=partner.erstellt_am,
        aktualisiert_am=partner.aktualisiert_am,
        api_key=api_key,
    )


@router.get(
    "/partners/{partner_id}",
    response_model=ApiPartnerResponse,
    summary="Partner-Details abrufen",
    description="Gibt Details eines bestimmten Partners zurück.",
)
async def get_partner(
    partner_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get partner details (superadmin only)."""
    service = PartnerService(db)
    partner = await service.get_partner_by_id(partner_id)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner mit ID '{partner_id}' nicht gefunden.",
        )

    return partner


@router.patch(
    "/partners/{partner_id}",
    response_model=ApiPartnerResponse,
    summary="Partner aktualisieren",
    description="Aktualisiert einen bestehenden Partner (partielle Aktualisierung).",
)
async def update_partner(
    partner_id: str,
    data: ApiPartnerUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Update partner (superadmin only)."""
    service = PartnerService(db)
    partner = await service.update_partner(partner_id, data)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner mit ID '{partner_id}' nicht gefunden.",
        )

    return partner


@router.delete(
    "/partners/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Partner löschen",
    description="Löscht einen Partner dauerhaft.",
)
async def delete_partner(
    partner_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Delete partner (superadmin only)."""
    service = PartnerService(db)
    deleted = await service.delete_partner(partner_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner mit ID '{partner_id}' nicht gefunden.",
        )

    return None


@router.post(
    "/partners/{partner_id}/regenerate-key",
    response_model=ApiPartnerWithKey,
    summary="API-Key neu generieren",
    description="Generiert einen neuen API-Key für einen Partner. Der alte Key wird ungültig.",
)
async def regenerate_api_key(
    partner_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate API key for a partner (superadmin only).

    **IMPORTANT**: The new API key is only shown once!
    The old key will be invalidated immediately.
    """
    service = PartnerService(db)
    result = await service.regenerate_api_key(partner_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner mit ID '{partner_id}' nicht gefunden.",
        )

    partner, api_key = result

    return ApiPartnerWithKey(
        id=partner.id,
        name=partner.name,
        email=partner.email,
        role=partner.role,
        kosten_geoapi_pro_einwohner=partner.kosten_geoapi_pro_einwohner,
        is_active=partner.is_active,
        erstellt_am=partner.erstellt_am,
        aktualisiert_am=partner.aktualisiert_am,
        api_key=api_key,
    )


# ============ Usage Monitoring ============

@router.get(
    "/usage/uebersicht",
    response_model=UsageAdminUebersichtList,
    summary="Usage-Übersicht aller Partner",
    description="Zeigt die API-Nutzung aller aktiven Partner (heute + aktueller Monat).",
)
async def get_usage_uebersicht(
    skip: int = Query(0, ge=0, description="Pagination Offset"),
    limit: int = Query(100, ge=1, le=1000, description="Max. Anzahl"),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get usage overview for all partners (superadmin only)."""
    service = UsageService(db)
    return await service.get_admin_usage_uebersicht(skip=skip, limit=limit)


@router.get(
    "/usage/partner/{partner_id}",
    response_model=UsageAdminPartnerDetail,
    summary="Usage eines Partners",
    description="Zeigt die detaillierte API-Nutzung eines bestimmten Partners.",
)
async def get_partner_usage(
    partner_id: str,
    von: date | None = Query(None, description="Startdatum (YYYY-MM-DD)"),
    bis: date | None = Query(None, description="Enddatum (YYYY-MM-DD)"),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed usage for a specific partner (superadmin only)."""
    service = UsageService(db)
    result = await service.get_admin_partner_usage(partner_id, von=von, bis=bis)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner mit ID '{partner_id}' nicht gefunden.",
        )

    return result
