"""
SQLAlchemy Models for Billing & Credit System.

Manages billing accounts (credits/invoice/internal),
credit transactions, and invoices per partner.
"""
import logging
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, JSON, UniqueConstraint,
)

from app.models.geo import Base, UUID, generate_uuid

logger = logging.getLogger(__name__)


class ApiBillingAccount(Base):
    """Billing account for a partner (1:1 relationship)."""
    __tablename__ = "api_billing_account"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    partner_id = Column(UUID, ForeignKey("api_partner.id"), unique=True, nullable=False)
    billing_typ = Column(String(20), nullable=False, default="internal")
    guthaben_cents = Column(Integer, nullable=False, default=0)
    rechnungs_limit_cents = Column(Integer, nullable=False, default=0)
    warnung_bei_cents = Column(Integer, nullable=False, default=1000)
    warnung_gesendet_am = Column(DateTime, nullable=True)
    ist_gesperrt = Column(Boolean, nullable=False, default=False)
    gesperrt_grund = Column(String(255), nullable=True)
    gesperrt_am = Column(DateTime, nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_billing_typ", "billing_typ"),
    )

    def __repr__(self):
        return f"<ApiBillingAccount {self.billing_typ} partner={self.partner_id} guthaben={self.guthaben_cents}>"


class ApiCreditTransaction(Base):
    """Individual credit movement (topup, usage deduction, refund, adjustment)."""
    __tablename__ = "api_credit_transaction"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    billing_account_id = Column(UUID, ForeignKey("api_billing_account.id"), nullable=False)
    typ = Column(String(20), nullable=False)
    betrag_cents = Column(Integer, nullable=False)
    saldo_danach_cents = Column(Integer, nullable=False)
    beschreibung = Column(String(255), nullable=True)
    referenz_typ = Column(String(50), nullable=True)
    referenz_id = Column(String(100), nullable=True)
    erstellt_von = Column(String(100), nullable=False, default="system")
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_credit_billing_id", "billing_account_id"),
        Index("idx_credit_erstellt_am", "erstellt_am"),
        Index("idx_credit_typ", "typ"),
    )

    def __repr__(self):
        return f"<ApiCreditTransaction {self.typ} {self.betrag_cents}ct>"


class ApiInvoice(Base):
    """Monthly invoice for a partner."""
    __tablename__ = "api_invoice"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    partner_id = Column(UUID, ForeignKey("api_partner.id"), nullable=False)
    rechnungsnummer = Column(String(50), unique=True, nullable=False)
    zeitraum_von = Column(Date, nullable=False)
    zeitraum_bis = Column(Date, nullable=False)
    summe_netto_cents = Column(Integer, nullable=False, default=0)
    summe_brutto_cents = Column(Integer, nullable=False, default=0)
    mwst_satz = Column(Float, nullable=False, default=19.0)
    status = Column(String(20), nullable=False, default="entwurf")
    positionen = Column(JSON, nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_invoice_partner_zeitraum", "partner_id", "zeitraum_von"),
    )

    def __repr__(self):
        return f"<ApiInvoice {self.rechnungsnummer} {self.status}>"
