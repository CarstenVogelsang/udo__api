"""
Pydantic Schemas for Geodata API responses.

Provides nested parent hierarchies for each level.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ============ Base Schemas (without relations) ============

class GeoLandBase(BaseModel):
    """Land base schema."""
    id: str
    ags: str
    code: str
    name: str
    name_eng: str | None = None
    iso3: str | None = None
    kontinent: str | None = None
    ist_eu: bool | None = None
    ist_favorit: bool | None = False
    sortierung: int | None = 0
    primary_color: str | None = None
    secondary_color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GeoBundeslandBase(BaseModel):
    """Bundesland base schema."""
    id: str
    ags: str
    code: str
    kuerzel: str | None = None
    name: str
    einwohner: int | None = None
    icon: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GeoRegierungsbezirkBase(BaseModel):
    """Regierungsbezirk base schema."""
    id: str
    ags: str
    code: str
    name: str
    primary_color: str | None = None
    secondary_color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GeoKreisBase(BaseModel):
    """Kreis base schema."""
    id: str
    ags: str
    code: str
    name: str
    typ: str | None = None
    ist_landkreis: bool | None = None
    ist_kreisfreie_stadt: bool | None = None
    autokennzeichen: str | None = None
    einwohner: int | None = None
    primary_color: str | None = None
    secondary_color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GeoOrtBase(BaseModel):
    """Ort base schema."""
    id: str
    ags: str | None = None
    code: str
    name: str
    plz: str | None = None
    typ: str | None = None
    ist_stadt: bool | None = None
    ist_gemeinde: bool | None = None
    lat: float | None = None
    lng: float | None = None
    einwohner: int | None = None
    primary_color: str | None = None
    secondary_color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GeoOrtsteilBase(BaseModel):
    """Ortsteil base schema."""
    id: str
    ags: str | None = None
    code: str
    name: str
    lat: float | None = None
    lng: float | None = None
    einwohner: int | None = None
    primary_color: str | None = None
    secondary_color: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============ Nested Schemas (with parent hierarchies) ============

class GeoBundeslandWithParent(GeoBundeslandBase):
    """Bundesland with Land."""
    land: GeoLandBase


class GeoRegierungsbezirkWithParents(GeoRegierungsbezirkBase):
    """Regierungsbezirk with Bundesland and Land."""
    bundesland: GeoBundeslandWithParent


class GeoKreisWithParents(GeoKreisBase):
    """Kreis with all parent levels."""
    bundesland: GeoBundeslandWithParent
    regierungsbezirk: GeoRegierungsbezirkBase | None = None


class GeoOrtWithParents(GeoOrtBase):
    """Ort with all parent levels."""
    kreis: GeoKreisWithParents


class GeoOrtsteilWithParents(GeoOrtsteilBase):
    """Ortsteil with all parent levels."""
    ort: GeoOrtWithParents


# ============ Detailed Schemas (with more fields) ============

class GeoLandDetail(GeoLandBase):
    """Land with all fields."""
    name_fra: str | None = None
    landesvorwahl: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class GeoBundeslandDetail(GeoBundeslandWithParent):
    """Bundesland with all fields."""
    einwohner_stand: datetime | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class GeoKreisDetail(GeoKreisWithParents):
    """Kreis with all fields."""
    kreissitz: str | None = None
    einwohner_stand: datetime | None = None
    einwohner_pro_km2: int | None = None
    flaeche_km2: int | None = None
    beschreibung: str | None = None
    wikipedia_url: str | None = None
    website_url: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class GeoOrtDetail(GeoOrtWithParents):
    """Ort with all fields."""
    ist_hauptort: bool | None = None
    einwohner_stand: datetime | None = None
    einwohner_pro_km2: int | None = None
    flaeche_km2: float | None = None
    beschreibung: str | None = None
    wikipedia_url: str | None = None
    website_url: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class GeoOrtsteilDetail(GeoOrtsteilWithParents):
    """Ortsteil with all fields."""
    einwohner_stand: datetime | None = None
    beschreibung: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


# ============ Partner Schemas (for Partner API - limited fields) ============

class GeoLandPartner(BaseModel):
    """Land schema for Partner API (limited fields)."""
    id: str
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class GeoBundeslandPartner(BaseModel):
    """Bundesland schema for Partner API (limited fields)."""
    id: str
    code: str
    kuerzel: str | None
    name: str
    icon: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GeoKreisPartner(BaseModel):
    """
    Kreis schema for Partner API (limited fields).

    Note: einwohner is rounded to 1000, abrufkosten is calculated dynamically.
    """
    id: str
    code: str
    kuerzel: str | None = Field(None, description="Autokennzeichen")
    name: str
    ist_landkreis: bool | None
    ist_kreisfreie_stadt: bool | None
    einwohner: int | None = Field(None, description="Einwohner (gerundet auf 1000)")
    abrufkosten: float = Field(..., description="Kosten = Einwohner x KostenProEinwohner")

    model_config = ConfigDict(from_attributes=True)


class GeoOrtPartner(BaseModel):
    """Ort schema for Partner API (limited fields)."""
    id: str
    code: str
    name: str
    plz: str | None
    lat: float | None
    lng: float | None
    kreis_id: str
    ist_hauptort: bool

    model_config = ConfigDict(from_attributes=True)


# ============ List Response Schemas ============

class GeoLandList(BaseModel):
    """List of countries."""
    items: list[GeoLandBase]
    total: int


class GeoBundeslandList(BaseModel):
    """List of federal states."""
    items: list[GeoBundeslandWithParent]
    total: int


class GeoRegierungsbezirkList(BaseModel):
    """List of government districts."""
    items: list[GeoRegierungsbezirkWithParents]
    total: int


class GeoKreisList(BaseModel):
    """List of counties."""
    items: list[GeoKreisWithParents]
    total: int


class GeoOrtList(BaseModel):
    """List of cities/municipalities."""
    items: list[GeoOrtWithParents]
    total: int


class GeoOrtsteilList(BaseModel):
    """List of city districts."""
    items: list[GeoOrtsteilWithParents]
    total: int
