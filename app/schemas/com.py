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
    geloescht_am: datetime | None = None


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
    total_unfiltered: int | None = None


# ============ Partner Schemas (All Fields with Geo-Hierarchy) ============

class ComUnternehmenPartner(ComUnternehmenWithGeo):
    """
    Company schema for partner access with full geo hierarchy.

    Includes all fields plus: Ort → Kreis → Bundesland → Land
    Partners can only see companies in their assigned countries.
    """
    legacy_id: int | None = None


class UsageMeta(BaseModel):
    """Usage metadata attached to partner API responses."""
    kosten_abruf: float
    kosten_heute: float
    kosten_monat: float
    abrufe_heute: int
    guthaben_cents: int = 0
    billing_typ: str = "internal"


class ComUnternehmenPartnerList(BaseModel):
    """Paginated list of companies for partners (with usage metadata)."""
    items: list[ComUnternehmenPartner]
    total: int
    meta: UsageMeta | None = None


class ComUnternehmenPartnerCount(BaseModel):
    """Company count for partners (only companies they can access)."""
    total: int


# ============ Organisation Schemas ============

class ComOrganisationBase(BaseModel):
    """Base schema for ComOrganisation."""
    id: str
    legacy_id: int | None = None
    kurzname: str

    model_config = ConfigDict(from_attributes=True)


class ComOrganisationSimple(ComOrganisationBase):
    """Simple Organisation without nested relations (for embedding in Unternehmen)."""
    pass


class ComOrganisationDetail(ComOrganisationBase):
    """Organisation with timestamps and member count."""
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class ComOrganisationWithUnternehmen(ComOrganisationDetail):
    """Organisation with list of associated Unternehmen."""
    unternehmen: list[ComUnternehmenBase] = []


class ComOrganisationList(BaseModel):
    """Paginated list of organisations."""
    items: list[ComOrganisationBase]
    total: int


class ComOrganisationCreate(BaseModel):
    """Schema for creating a new Organisation."""
    kurzname: str
    legacy_id: int | None = None


class ComOrganisationUpdate(BaseModel):
    """Schema for updating an Organisation (partial)."""
    kurzname: str | None = None


# ============ Extended Unternehmen Schemas with Organisationen ============

class ComUnternehmenWithOrganisationen(ComUnternehmenWithGeo):
    """Unternehmen with associated Organisationen."""
    organisationen: list[ComOrganisationSimple] = []


class ComUnternehmenDetailWithOrg(ComUnternehmenDetail):
    """Unternehmen Detail with Organisationen."""
    organisationen: list[ComOrganisationSimple] = []


# ============ Kontakt Schemas ============

class ComKontaktBase(BaseModel):
    """Base schema for ComKontakt."""
    id: str
    typ: str | None = None
    titel: str | None = None
    anrede: str | None = None
    vorname: str
    nachname: str
    position: str | None = None
    abteilung: str | None = None
    telefon: str | None = None
    mobil: str | None = None
    fax: str | None = None
    email: str | None = None
    notizen: str | None = None
    ist_hauptkontakt: bool = False

    model_config = ConfigDict(from_attributes=True)


class ComKontaktDetail(ComKontaktBase):
    """Kontakt with all fields including timestamps."""
    legacy_id: int | None = None
    unternehmen_id: str
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class ComKontaktList(BaseModel):
    """Paginated list of contacts."""
    items: list[ComKontaktBase]
    total: int


class ComKontaktCreate(BaseModel):
    """Schema for creating a new Kontakt."""
    typ: str | None = None
    titel: str | None = None
    anrede: str | None = None
    vorname: str
    nachname: str
    position: str | None = None
    abteilung: str | None = None
    telefon: str | None = None
    mobil: str | None = None
    fax: str | None = None
    email: str | None = None
    notizen: str | None = None
    ist_hauptkontakt: bool = False
    legacy_id: int | None = None


class ComKontaktUpdate(BaseModel):
    """Schema for updating a Kontakt (partial)."""
    typ: str | None = None
    titel: str | None = None
    anrede: str | None = None
    vorname: str | None = None
    nachname: str | None = None
    position: str | None = None
    abteilung: str | None = None
    telefon: str | None = None
    mobil: str | None = None
    fax: str | None = None
    email: str | None = None
    notizen: str | None = None
    ist_hauptkontakt: bool | None = None


# ============ Unternehmen Create/Update Schemas ============

class ComUnternehmenCreate(BaseModel):
    """Schema for creating a new Unternehmen."""
    kurzname: str
    firmierung: str | None = None
    strasse: str | None = None
    strasse_hausnr: str | None = None
    geo_ort_id: str | None = None
    legacy_id: int | None = None


class ComUnternehmenUpdate(BaseModel):
    """Schema for updating an Unternehmen (partial)."""
    kurzname: str | None = None
    firmierung: str | None = None
    strasse: str | None = None
    strasse_hausnr: str | None = None
    geo_ort_id: str | None = None
    status_datum: datetime | None = None


# ============ Bulk Action Schemas ============

class BulkActionRequest(BaseModel):
    """Request for bulk actions on Unternehmen."""
    ids: list[str]


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""
    erfolg: int
    fehler: int
