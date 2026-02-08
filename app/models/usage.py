"""
SQLAlchemy Models for API Usage Tracking.

Logs every partner API call with calculated costs.
Provides daily aggregation for dashboard and billing.
"""
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, JSON, UniqueConstraint,
)

from app.models.geo import Base, UUID, generate_uuid


class ApiUsage(Base):
    """Individual API usage record for a partner request."""
    __tablename__ = "api_usage"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    partner_id = Column(UUID, ForeignKey("api_partner.id"), nullable=False)
    endpoint = Column(String(100), nullable=False)
    methode = Column(String(10), nullable=False, default="GET")
    parameter = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=False, default=200)
    anzahl_ergebnisse = Column(Integer, nullable=False, default=0)
    kosten = Column(Float, nullable=False, default=0.0)
    antwortzeit_ms = Column(Integer, nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_usage_partner_date", "partner_id", "erstellt_am"),
        Index("idx_usage_endpoint", "endpoint"),
        Index("idx_usage_erstellt_am", "erstellt_am"),
    )

    def __repr__(self):
        return f"<ApiUsage {self.endpoint} partner={self.partner_id} cost={self.kosten}>"


class ApiUsageDaily(Base):
    """Daily aggregated usage per partner and endpoint."""
    __tablename__ = "api_usage_daily"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    partner_id = Column(UUID, ForeignKey("api_partner.id"), nullable=False)
    datum = Column(Date, nullable=False)
    endpoint = Column(String(100), nullable=False)
    anzahl_abrufe = Column(Integer, nullable=False, default=0)
    anzahl_ergebnisse_gesamt = Column(Integer, nullable=False, default=0)
    kosten_gesamt = Column(Float, nullable=False, default=0.0)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("partner_id", "datum", "endpoint", name="uq_daily_partner_datum_endpoint"),
        Index("idx_daily_datum", "datum"),
    )

    def __repr__(self):
        return f"<ApiUsageDaily {self.datum} {self.endpoint} partner={self.partner_id}>"
