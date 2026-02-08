"""
Pydantic Schemas for API Usage Tracking.

Provides response models for usage metadata, current usage stats,
and historical usage data.
"""
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class UsageMeta(BaseModel):
    """Usage metadata attached to every partner API response."""
    kosten_abruf: float
    kosten_heute: float
    kosten_monat: float
    abrufe_heute: int


class UsageTagInfo(BaseModel):
    """Usage info for a single day."""
    datum: date
    anzahl_abrufe: int
    anzahl_ergebnisse_gesamt: int
    kosten_gesamt: float


class UsageMonatInfo(BaseModel):
    """Usage info for the current month."""
    monat: str  # e.g. "2026-02"
    anzahl_abrufe: int
    kosten_gesamt: float


class UsageAktuell(BaseModel):
    """Current usage overview (today + current month)."""
    heute: UsageTagInfo
    monat: UsageMonatInfo
    letzter_abruf: datetime | None = None


class UsageHistorieList(BaseModel):
    """Paginated daily usage history."""
    items: list[UsageTagInfo]
    total: int


# ============ Admin Usage Schemas ============

class UsagePartnerUebersicht(BaseModel):
    """Usage overview for a single partner (admin view)."""
    partner_id: str
    partner_name: str
    abrufe_heute: int
    kosten_heute: float
    abrufe_monat: int
    kosten_monat: float


class UsageAdminUebersichtList(BaseModel):
    """Paginated partner usage overview (admin)."""
    items: list[UsagePartnerUebersicht]
    total: int


class UsageAdminPartnerDetail(BaseModel):
    """Detailed usage for a specific partner (admin view)."""
    partner_id: str
    partner_name: str
    zeitraum_von: date
    zeitraum_bis: date
    tage: list[UsageTagInfo]
    gesamt_abrufe: int
    gesamt_kosten: float
