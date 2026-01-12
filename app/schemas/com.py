"""
Pydantic Schemas for Company (Unternehmen) API responses.

Provides nested GeoOrt hierarchy for each company.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.geo import GeoOrtWithParents


# ============ Base Schemas ============

class ComUnternehmenBase(BaseModel):
    """Base schema for ComUnternehmen (without geo relation)."""
    id: str
    legacy_id: int | None = None
    kurzname: str | None = None
    firmierung: str | None = None
    strasse: str | None = None
    strasse_hausnr: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============ Schemas with Relations ============

class ComUnternehmenWithGeo(ComUnternehmenBase):
    """
    Unternehmen with full GeoOrt hierarchy.

    Includes: Ort → Kreis → Bundesland → Land
    """
    geo_ort: GeoOrtWithParents | None = None


# ============ Detail Schemas ============

class ComUnternehmenDetail(ComUnternehmenWithGeo):
    """Unternehmen with all fields including timestamps."""
    status_datum: datetime | None = None
    geo_ort_id: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


# ============ List Response Schemas ============

class ComUnternehmenList(BaseModel):
    """Paginated list of companies."""
    items: list[ComUnternehmenWithGeo]
    total: int


# ============ Partner Schemas (Limited Fields) ============

class ComUnternehmenPartner(BaseModel):
    """
    Limited company schema for partner access.

    Only includes fields safe for external partners.
    """
    id: str
    kurzname: str | None = None
    firmierung: str | None = None
    strasse: str | None = None
    strasse_hausnr: str | None = None
    # Limited geo info - only ort name, not full hierarchy
    geo_ort_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ComUnternehmenPartnerList(BaseModel):
    """Paginated list of companies for partners."""
    items: list[ComUnternehmenPartner]
    total: int
