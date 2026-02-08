"""
Pydantic Schemas for Billing & Credit System.

Response models for billing accounts, transactions, and invoices.
"""
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


# ============ Billing Account ============

class BillingAccountResponse(BaseModel):
    """Billing account info (for partner self-service)."""
    id: str
    partner_id: str
    billing_typ: str
    guthaben_cents: int
    rechnungs_limit_cents: int
    warnung_bei_cents: int
    ist_gesperrt: bool
    gesperrt_grund: str | None = None
    erstellt_am: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BillingAccountAdmin(BillingAccountResponse):
    """Extended billing account info (for admin)."""
    warnung_gesendet_am: datetime | None = None
    gesperrt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


# ============ Credit Transactions ============

class CreditTransactionResponse(BaseModel):
    """Single credit transaction."""
    id: str
    typ: str
    betrag_cents: int
    saldo_danach_cents: int
    beschreibung: str | None = None
    referenz_typ: str | None = None
    referenz_id: str | None = None
    erstellt_von: str
    erstellt_am: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CreditTransactionList(BaseModel):
    """Paginated list of credit transactions."""
    items: list[CreditTransactionResponse]
    total: int


# ============ Admin Actions ============

class CreditTopupRequest(BaseModel):
    """Request to top up credits for a partner."""
    betrag_cents: int
    beschreibung: str | None = None


class SperrenRequest(BaseModel):
    """Request to block a partner's API access."""
    grund: str


# ============ Invoices ============

class InvoiceResponse(BaseModel):
    """Invoice info."""
    id: str
    partner_id: str
    rechnungsnummer: str
    zeitraum_von: date
    zeitraum_bis: date
    summe_netto_cents: int
    summe_brutto_cents: int
    mwst_satz: float
    status: str
    positionen: dict | list | None = None
    erstellt_am: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceList(BaseModel):
    """Paginated list of invoices."""
    items: list[InvoiceResponse]
    total: int
