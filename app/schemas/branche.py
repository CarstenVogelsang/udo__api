"""
Pydantic Schemas for Branchenklassifikation API responses.

Provides Base, Detail, and List schemas for all Branchen models.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# ============ BrnBranche ============


class BrnBrancheBase(BaseModel):
    """WZ-2008 industry code (compact)."""
    id: str
    wz_code: str
    bezeichnung: str
    ebene: int
    parent_wz_code: str | None = None
    ist_aktiv: bool

    model_config = ConfigDict(from_attributes=True)


class BrnBrancheDetail(BrnBrancheBase):
    """WZ-2008 industry code with timestamps."""
    erstellt_am: datetime | None = None


class BrnBrancheList(BaseModel):
    """Paginated list of WZ codes."""
    items: list[BrnBrancheBase]
    total: int


# ============ BrnVerzeichnis ============


class BrnVerzeichnisBase(BaseModel):
    """Business directory entry (compact)."""
    id: str
    name: str
    url: str
    beschreibung: str | None = None
    branche_wz_code: str | None = None
    ist_branchenuebergreifend: bool
    hat_api: bool
    api_dokumentation_url: str | None = None
    anmeldeart: str
    anmelde_url: str | None = None
    kosten: str
    kosten_details: str | None = None
    relevanz_score: int
    regionen: list[str] | None = None
    anleitung_url: str | None = None
    logo_url: str | None = None
    ist_aktiv: bool
    zuletzt_geprueft: date | None = None

    model_config = ConfigDict(from_attributes=True)


class BrnVerzeichnisDetail(BrnVerzeichnisBase):
    """Business directory entry with timestamps."""
    erstellt_am: datetime | None = None


class BrnVerzeichnisList(BaseModel):
    """Paginated list of business directories."""
    items: list[BrnVerzeichnisBase]
    total: int


class BrnVerzeichnisListForBranche(BaseModel):
    """Business directories for a specific WZ code (incl. cross-industry)."""
    branche: BrnBrancheBase
    verzeichnisse: list[BrnVerzeichnisBase]
    gesamt: int


# ============ BrnRegionaleGruppe ============


class BrnRegionaleGruppeBase(BaseModel):
    """Regional social media group (compact)."""
    id: str
    plattform: str
    name: str
    url: str
    beschreibung: str | None = None
    branche_wz_code: str | None = None
    region_plz_prefix: str | None = None
    region_name: str | None = None
    region_bundesland: str | None = None
    mitglieder_anzahl: int | None = None
    werbung_erlaubt: bool
    posting_regeln: str | None = None
    empfohlene_posting_art: str | None = None
    ist_aktiv: bool
    zuletzt_geprueft: date | None = None

    model_config = ConfigDict(from_attributes=True)


class BrnRegionaleGruppeDetail(BrnRegionaleGruppeBase):
    """Regional group with timestamps."""
    erstellt_am: datetime | None = None


class BrnRegionaleGruppeList(BaseModel):
    """Paginated list of regional groups."""
    items: list[BrnRegionaleGruppeBase]
    total: int


class BrnRegionaleGruppeListForBranche(BaseModel):
    """Regional groups for a specific WZ code."""
    branche: BrnBrancheBase
    gruppen: list[BrnRegionaleGruppeBase]
    gesamt: int


# ============ BrnGoogleKategorie ============


class BrnGoogleKategorieBase(BaseModel):
    """Google Business category (compact)."""
    id: str
    gcid: str
    name_de: str
    name_en: str
    ist_aktiv: bool

    model_config = ConfigDict(from_attributes=True)


class BrnGoogleKategorieDetail(BrnGoogleKategorieBase):
    """Google Business category with timestamps."""
    zuletzt_aktualisiert: datetime | None = None
    erstellt_am: datetime | None = None


class BrnGoogleKategorieList(BaseModel):
    """Paginated list of Google categories."""
    items: list[BrnGoogleKategorieBase]
    total: int


# ============ BrnGoogleMapping ============


class BrnGoogleMappingBase(BaseModel):
    """WZ to Google category mapping."""
    id: str
    wz_code: str
    gcid: str
    ist_primaer: bool
    relevanz: int

    model_config = ConfigDict(from_attributes=True)


class BrnGoogleMappingWithKategorie(BrnGoogleMappingBase):
    """Mapping with embedded Google category details."""
    google_kategorie: BrnGoogleKategorieBase


class BrnGoogleMappingListForBranche(BaseModel):
    """Google category mappings for a specific WZ code."""
    branche: BrnBrancheBase
    mappings: list[BrnGoogleMappingWithKategorie]
    gesamt: int
