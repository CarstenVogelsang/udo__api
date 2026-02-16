"""Pydantic Schemas for Recherche-Auftrag API.

Request/Response models for cost estimation, order creation,
order listing, and order details.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator


class QualitaetsStufe(str, Enum):
    """Quality tier for recherche orders."""
    standard = "standard"
    premium = "premium"
    komplett = "komplett"


# ============ Request Schemas ============

class RecherchSchaetzungRequest(BaseModel):
    """Request for cost estimation (no order created)."""
    # Geographic scope (at least one required)
    geo_ort_id: str | None = None
    geo_kreis_id: str | None = None
    plz: str | None = None

    # Industry filter (at least one required)
    wz_code: str | None = None
    google_kategorie_gcid: str | None = None
    branche_freitext: str | None = None

    # Quality tier
    qualitaets_stufe: QualitaetsStufe = QualitaetsStufe.standard

    @model_validator(mode="after")
    def validate_filters(self):
        has_geo = any([self.geo_ort_id, self.geo_kreis_id, self.plz])
        has_branche = any([self.wz_code, self.google_kategorie_gcid, self.branche_freitext])

        if not has_geo:
            raise ValueError("Mindestens ein Geo-Filter erforderlich (geo_ort_id, geo_kreis_id oder plz).")
        if not has_branche:
            raise ValueError("Mindestens ein Branchenfilter erforderlich (wz_code, google_kategorie_gcid oder branche_freitext).")
        return self


class RecherchAuftragRequest(RecherchSchaetzungRequest):
    """Request to create a recherche order.

    Same fields as estimation, but creates an actual order
    and reserves credits.
    """
    pass  # Inherits all fields + validation from estimation


# ============ Response Schemas ============

class RecherchSchaetzungResponse(BaseModel):
    """Cost estimation response."""
    einwohner: int
    geschaetzt_gesamt: int
    bestehend: int
    geschaetzt_neu: int
    grundgebuehr_cents: int
    pro_treffer_cents: int
    geschaetzt_kosten_cents: int
    qualitaets_stufe: str


class RecherchAuftragResponse(BaseModel):
    """Order summary (for list views)."""
    id: str
    status: str
    qualitaets_stufe: str

    # Scope
    geo_ort_id: str | None = None
    geo_kreis_id: str | None = None
    plz: str | None = None
    branche_freitext: str | None = None

    # Estimation
    schaetzung_anzahl: int | None = None
    schaetzung_kosten_cents: int | None = None

    # Results (populated after completion)
    ergebnis_anzahl_neu: int = 0
    kosten_tatsaechlich_cents: int | None = None

    # Timestamps
    erstellt_am: datetime | None = None
    abgeschlossen_am: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RecherchAuftragDetailResponse(RecherchAuftragResponse):
    """Detailed order view with all fields."""
    partner_id: str

    # Full industry filter
    wz_code: str | None = None
    google_kategorie_gcid: str | None = None

    # Full results
    ergebnis_anzahl_roh: int = 0
    ergebnis_anzahl_duplikat: int = 0
    ergebnis_anzahl_aktualisiert: int = 0

    # Worker info
    versuche: int = 0
    max_versuche: int = 3
    fehler_meldung: str | None = None
    worker_gestartet_am: datetime | None = None
    worker_beendet_am: datetime | None = None

    # Timestamps
    bestaetigt_am: datetime | None = None


class RecherchAuftragList(BaseModel):
    """Paginated list of orders."""
    items: list[RecherchAuftragResponse]
    total: int
