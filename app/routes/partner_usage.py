"""
Partner Usage API routes.

Partners can view their own usage stats and history.
Endpoint prefix: /partner/usage
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_partner
from app.models.partner import ApiPartner
from app.services.usage import UsageService
from app.schemas.usage import UsageAktuell, UsageHistorieList

router = APIRouter(prefix="/partner/usage", tags=["Partner Usage"])


@router.get(
    "/aktuell",
    response_model=UsageAktuell,
    summary="Aktuelle Nutzung abrufen",
    description="Zeigt die eigene API-Nutzung des aktuellen Tages und Monats.",
)
async def get_usage_aktuell(
    partner: ApiPartner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Get current usage stats (today + current month)."""
    service = UsageService(db)
    return await service.get_partner_usage_aktuell(partner.id)


@router.get(
    "/historie",
    response_model=UsageHistorieList,
    summary="Nutzungshistorie abrufen",
    description="Zeigt die tägliche Nutzungshistorie (paginiert, neueste zuerst).",
)
async def get_usage_historie(
    skip: int = Query(0, ge=0, description="Pagination Offset"),
    limit: int = Query(30, ge=1, le=365, description="Max. Anzahl Tage (1-365)"),
    partner: ApiPartner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Get daily usage history (paginated)."""
    service = UsageService(db)
    return await service.get_partner_usage_historie(partner.id, skip=skip, limit=limit)
