"""
Business logic for Billing & Credit System.

Manages billing accounts, credit transactions, and access control
based on billing type (credits/invoice/internal).
"""
import logging
import math
from datetime import datetime, date

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import ApiBillingAccount, ApiCreditTransaction, ApiInvoice
from app.models.usage import ApiUsage
from app.models.partner import ApiPartner

logger = logging.getLogger(__name__)


class BillingService:
    """Service class for billing operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_account(self, partner_id: str) -> ApiBillingAccount:
        """
        Get billing account for partner, creating one if it doesn't exist.

        New accounts default to billing_typ='internal' (no credit check).
        """
        result = await self.db.execute(
            select(ApiBillingAccount).where(
                ApiBillingAccount.partner_id == partner_id
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            account = ApiBillingAccount(
                partner_id=partner_id,
                billing_typ="internal",
            )
            self.db.add(account)
            await self.db.flush()
            logger.info(f"Created billing account for partner {partner_id} (internal)")

        return account

    async def check_billing_access(self, partner_id: str) -> ApiBillingAccount:
        """
        Check if partner has billing access. Raises 402 if not.

        Rules:
        - ist_gesperrt=True → always blocked (any billing_typ)
        - credits: guthaben_cents <= 0 → blocked
        - invoice: monthly spend >= rechnungs_limit_cents → blocked
        - internal: always allowed
        """
        account = await self.get_or_create_account(partner_id)

        # Manual block check first
        if account.ist_gesperrt:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=account.gesperrt_grund or "API-Zugang gesperrt.",
                headers={"X-Billing-Status": "blocked"},
            )

        if account.billing_typ == "credits":
            if account.guthaben_cents <= 0:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Kein ausreichendes Guthaben. Bitte laden Sie Ihr Konto auf.",
                    headers={"X-Billing-Status": "no-credits"},
                )

        elif account.billing_typ == "invoice":
            if account.rechnungs_limit_cents > 0:
                monthly_spend = await self._get_monthly_spend_cents(partner_id)
                if monthly_spend >= account.rechnungs_limit_cents:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail="Monatliches Rechnungslimit erreicht.",
                        headers={"X-Billing-Status": "limit-reached"},
                    )

        # internal: always OK
        return account

    async def deduct_credits(
        self,
        partner_id: str,
        kosten: float,
        usage_id: str,
        beschreibung: str,
    ) -> ApiCreditTransaction | None:
        """
        Deduct credits after a successful API call.

        For 'credits': actually deducts from guthaben_cents.
        For 'invoice'/'internal': logs the transaction but doesn't touch guthaben.
        """
        if kosten <= 0:
            return None

        account = await self.get_or_create_account(partner_id)
        kosten_cents = math.ceil(kosten * 100)  # Round up to full cents

        if account.billing_typ == "credits":
            account.guthaben_cents -= kosten_cents
            saldo = account.guthaben_cents
        else:
            # invoice/internal: log transaction, don't deduct
            saldo = account.guthaben_cents  # unchanged

        transaction = ApiCreditTransaction(
            billing_account_id=account.id,
            typ="usage",
            betrag_cents=-kosten_cents,
            saldo_danach_cents=saldo,
            beschreibung=beschreibung,
            referenz_typ="api_usage",
            referenz_id=usage_id,
            erstellt_von="system",
        )
        self.db.add(transaction)
        await self.db.flush()

        # Check low-credit warning
        if (
            account.billing_typ == "credits"
            and account.guthaben_cents <= account.warnung_bei_cents
            and account.guthaben_cents > 0
        ):
            await self._handle_low_credit_warning(account)

        return transaction

    async def topup_credits(
        self,
        partner_id: str,
        betrag_cents: int,
        beschreibung: str | None = None,
        erstellt_von: str = "admin",
    ) -> ApiCreditTransaction:
        """Top up credits for a partner (admin action)."""
        account = await self.get_or_create_account(partner_id)

        account.guthaben_cents += betrag_cents
        account.warnung_gesendet_am = None  # Reset warning flag

        transaction = ApiCreditTransaction(
            billing_account_id=account.id,
            typ="topup",
            betrag_cents=betrag_cents,
            saldo_danach_cents=account.guthaben_cents,
            beschreibung=beschreibung or f"Aufladung: {betrag_cents / 100:.2f} EUR",
            referenz_typ="manual",
            erstellt_von=erstellt_von,
        )
        self.db.add(transaction)
        await self.db.flush()

        logger.info(
            f"Credits topped up: partner={partner_id} amount={betrag_cents}ct "
            f"new_balance={account.guthaben_cents}ct"
        )
        return transaction

    async def sperren(self, partner_id: str, grund: str) -> ApiBillingAccount | None:
        """Block a partner's API access (admin action)."""
        account = await self.get_or_create_account(partner_id)

        # Verify partner exists
        partner = (await self.db.execute(
            select(ApiPartner).where(ApiPartner.id == partner_id)
        )).scalar_one_or_none()
        if not partner:
            return None

        account.ist_gesperrt = True
        account.gesperrt_grund = grund
        account.gesperrt_am = datetime.utcnow()
        await self.db.flush()

        logger.warning(f"Partner blocked: {partner_id} reason={grund}")
        return account

    async def entsperren(self, partner_id: str) -> ApiBillingAccount | None:
        """Unblock a partner's API access (admin action)."""
        account = await self.get_or_create_account(partner_id)

        partner = (await self.db.execute(
            select(ApiPartner).where(ApiPartner.id == partner_id)
        )).scalar_one_or_none()
        if not partner:
            return None

        account.ist_gesperrt = False
        account.gesperrt_grund = None
        account.gesperrt_am = None
        await self.db.flush()

        logger.info(f"Partner unblocked: {partner_id}")
        return account

    async def get_billing_account(self, partner_id: str) -> ApiBillingAccount | None:
        """Get billing account without auto-creation (for admin views)."""
        result = await self.db.execute(
            select(ApiBillingAccount).where(
                ApiBillingAccount.partner_id == partner_id
            )
        )
        return result.scalar_one_or_none()

    async def set_billing_typ(
        self,
        partner_id: str,
        billing_typ: str,
        rechnungs_limit_cents: int = 0,
    ) -> ApiBillingAccount:
        """Change billing type for a partner (admin action)."""
        account = await self.get_or_create_account(partner_id)
        account.billing_typ = billing_typ
        account.rechnungs_limit_cents = rechnungs_limit_cents
        await self.db.flush()
        return account

    async def get_transaktionen(
        self,
        partner_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """Get paginated credit transactions for a partner."""
        account = await self.get_or_create_account(partner_id)

        # Count
        count_q = select(func.count(ApiCreditTransaction.id)).where(
            ApiCreditTransaction.billing_account_id == account.id
        )
        total = (await self.db.execute(count_q)).scalar() or 0

        # Items
        items_q = (
            select(ApiCreditTransaction)
            .where(ApiCreditTransaction.billing_account_id == account.id)
            .order_by(ApiCreditTransaction.erstellt_am.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(items_q)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_rechnungen(
        self,
        partner_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """Get paginated invoices, optionally filtered by partner."""
        base_filter = []
        if partner_id:
            base_filter.append(ApiInvoice.partner_id == partner_id)

        count_q = select(func.count(ApiInvoice.id))
        if base_filter:
            count_q = count_q.where(*base_filter)
        total = (await self.db.execute(count_q)).scalar() or 0

        items_q = (
            select(ApiInvoice)
            .order_by(ApiInvoice.erstellt_am.desc())
            .offset(skip)
            .limit(limit)
        )
        if base_filter:
            items_q = items_q.where(*base_filter)
        result = await self.db.execute(items_q)
        items = result.scalars().all()

        return {"items": items, "total": total}

    # ---- Internal helpers ----

    async def _get_monthly_spend_cents(self, partner_id: str) -> int:
        """Sum of all usage costs in current month (from api_usage table)."""
        monat_start = date.today().replace(day=1)

        result = await self.db.execute(
            select(
                func.coalesce(func.sum(ApiUsage.kosten), 0.0)
            ).where(
                and_(
                    ApiUsage.partner_id == partner_id,
                    func.date(ApiUsage.erstellt_am) >= monat_start,
                )
            )
        )
        kosten_float = result.scalar() or 0.0
        return math.ceil(kosten_float * 100)

    async def _handle_low_credit_warning(self, account: ApiBillingAccount) -> None:
        """
        Handle low credit warning.

        Currently: logs warning + sets flag.
        TODO: Send email via vrs-core BrevoService when integration is ready.
        """
        if account.warnung_gesendet_am is None:
            account.warnung_gesendet_am = datetime.utcnow()
            logger.warning(
                f"Low credit warning: partner={account.partner_id} "
                f"balance={account.guthaben_cents}ct threshold={account.warnung_bei_cents}ct"
            )
