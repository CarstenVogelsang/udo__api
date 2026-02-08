"""
Partner Billing API routes.

Partners can view their own billing account and transactions.
Endpoint prefix: /partner/billing
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_partner_with_rate_limit
from app.models.partner import ApiPartner
from app.services.billing import BillingService
from app.schemas.billing import (
    BillingAccountResponse,
    CreditTransactionList,
    InvoiceList,
)

router = APIRouter(prefix="/partner/billing", tags=["Partner Billing"])


@router.get(
    "",
    response_model=BillingAccountResponse,
    summary="Eigenes Abrechnungskonto",
    description="Zeigt das eigene Abrechnungskonto mit Guthaben und Billing-Typ.",
)
async def get_billing_account(
    partner: ApiPartner = Depends(get_current_partner_with_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """Get own billing account (works even when blocked)."""
    service = BillingService(db)
    account = await service.get_or_create_account(partner.id)
    return account


@router.get(
    "/transaktionen",
    response_model=CreditTransactionList,
    summary="Credit-Transaktionen",
    description="Zeigt alle Transaktionen (Aufladungen, Abbuchungen, etc.) paginiert.",
)
async def get_transaktionen(
    skip: int = Query(0, ge=0, description="Pagination Offset"),
    limit: int = Query(50, ge=1, le=500, description="Max. Anzahl (1-500)"),
    partner: ApiPartner = Depends(get_current_partner_with_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """Get credit transactions for own account."""
    service = BillingService(db)
    return await service.get_transaktionen(partner.id, skip=skip, limit=limit)


@router.get(
    "/rechnungen",
    response_model=InvoiceList,
    summary="Eigene Rechnungen",
    description="Zeigt alle Rechnungen des Partners.",
)
async def get_rechnungen(
    skip: int = Query(0, ge=0, description="Pagination Offset"),
    limit: int = Query(50, ge=1, le=500, description="Max. Anzahl"),
    partner: ApiPartner = Depends(get_current_partner_with_rate_limit),
    db: AsyncSession = Depends(get_db),
):
    """Get invoices for own account."""
    service = BillingService(db)
    return await service.get_rechnungen(partner_id=partner.id, skip=skip, limit=limit)
