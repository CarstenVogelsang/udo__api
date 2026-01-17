"""
Pydantic Schemas for Plugin Marketplace API.

Provides schemas for:
- Plugin registry and metadata
- Project types and pricing
- Licenses and subscriptions
- Marketplace public endpoints
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.plugin import PlgPluginStatus, PlgLizenzStatus, PlgPreisModell


# =============================================================================
# Kategorie Schemas
# =============================================================================

class PlgKategorieBase(BaseModel):
    """Base schema for Plugin-Kategorie."""
    id: str
    slug: str
    name: str
    beschreibung: str | None = None
    icon: str | None = None
    sortierung: int = 0
    ist_aktiv: bool = True

    model_config = ConfigDict(from_attributes=True)


class PlgKategorieCreate(BaseModel):
    """Schema for creating a new Kategorie."""
    slug: str
    name: str
    beschreibung: str | None = None
    icon: str | None = None
    sortierung: int = 0
    ist_aktiv: bool = True


class PlgKategorieUpdate(BaseModel):
    """Schema for updating a Kategorie (partial)."""
    slug: str | None = None
    name: str | None = None
    beschreibung: str | None = None
    icon: str | None = None
    sortierung: int | None = None
    ist_aktiv: bool | None = None


class PlgKategorieDetail(PlgKategorieBase):
    """Kategorie with timestamps."""
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class PlgKategorieList(BaseModel):
    """Paginated list of categories."""
    items: list[PlgKategorieBase]
    total: int


# =============================================================================
# Plugin Schemas
# =============================================================================

class PlgPluginBase(BaseModel):
    """Base schema for Plugin."""
    id: str
    slug: str
    name: str
    beschreibung_kurz: str | None = None
    version: str
    status: str
    icon: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PlgPluginCreate(BaseModel):
    """Schema for creating a new Plugin."""
    slug: str
    name: str
    beschreibung: str | None = None
    beschreibung_kurz: str | None = None
    kategorie_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    version: str = "0.1.0"
    status: str = PlgPluginStatus.ENTWICKLUNG.value
    dokumentation_url: str | None = None
    changelog_url: str | None = None
    min_api_version: str | None = None
    icon: str | None = None
    thumbnail_url: str | None = None


class PlgPluginUpdate(BaseModel):
    """Schema for updating a Plugin (partial)."""
    name: str | None = None
    beschreibung: str | None = None
    beschreibung_kurz: str | None = None
    kategorie_id: str | None = None
    tags: list[str] | None = None
    version: str | None = None
    status: str | None = None
    dokumentation_url: str | None = None
    changelog_url: str | None = None
    min_api_version: str | None = None
    icon: str | None = None
    thumbnail_url: str | None = None


class PlgPluginWithKategorie(PlgPluginBase):
    """Plugin with nested Kategorie."""
    kategorie: PlgKategorieBase | None = None
    tags: list[str] = Field(default_factory=list)


class PlgPluginDetail(PlgPluginWithKategorie):
    """Plugin with all fields including timestamps."""
    beschreibung: str | None = None
    version_datum: datetime | None = None
    dokumentation_url: str | None = None
    changelog_url: str | None = None
    repo_url: str | None = None
    min_api_version: str | None = None
    thumbnail_url: str | None = None
    plugin_json_hash: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class PlgPluginList(BaseModel):
    """Paginated list of plugins."""
    items: list[PlgPluginWithKategorie]
    total: int


# =============================================================================
# Plugin Version Schemas
# =============================================================================

class PlgPluginVersionBase(BaseModel):
    """Base schema for Plugin Version."""
    id: str
    plugin_id: str
    version: str
    ist_aktuell: bool = False
    ist_breaking_change: bool = False
    veroeffentlicht_am: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PlgPluginVersionDetail(PlgPluginVersionBase):
    """Plugin Version with changelog."""
    changelog: str | None = None
    min_api_version: str | None = None
    erstellt_am: datetime | None = None


class PlgPluginVersionCreate(BaseModel):
    """Schema for creating a new Plugin Version."""
    version: str
    changelog: str | None = None
    ist_aktuell: bool = False
    ist_breaking_change: bool = False
    min_api_version: str | None = None


# =============================================================================
# Projekttyp Schemas
# =============================================================================

class PlgProjekttypBase(BaseModel):
    """Base schema for Projekttyp."""
    id: str
    slug: str
    name: str
    beschreibung: str | None = None
    ist_kostenlos: bool = False
    ist_testphase_erlaubt: bool = True
    standard_testphase_tage: int = 30
    icon: str | None = None
    sortierung: int = 0

    model_config = ConfigDict(from_attributes=True)


class PlgProjekttypCreate(BaseModel):
    """Schema for creating a new Projekttyp."""
    slug: str
    name: str
    beschreibung: str | None = None
    ist_kostenlos: bool = False
    ist_testphase_erlaubt: bool = True
    standard_testphase_tage: int = 30
    max_benutzer: int | None = None
    max_api_calls_pro_monat: int | None = None
    icon: str | None = None
    sortierung: int = 0


class PlgProjekttypUpdate(BaseModel):
    """Schema for updating a Projekttyp (partial)."""
    name: str | None = None
    beschreibung: str | None = None
    ist_kostenlos: bool | None = None
    ist_testphase_erlaubt: bool | None = None
    standard_testphase_tage: int | None = None
    max_benutzer: int | None = None
    max_api_calls_pro_monat: int | None = None
    icon: str | None = None
    sortierung: int | None = None


class PlgProjekttypDetail(PlgProjekttypBase):
    """Projekttyp with all fields."""
    max_benutzer: int | None = None
    max_api_calls_pro_monat: int | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class PlgProjekttypList(BaseModel):
    """Paginated list of project types."""
    items: list[PlgProjekttypBase]
    total: int


# =============================================================================
# Preis Schemas
# =============================================================================

class PlgPreisBase(BaseModel):
    """Base schema for Preis."""
    id: str
    plugin_id: str
    projekttyp_id: str
    modell: str
    preis: float
    waehrung: str = "EUR"
    ist_aktiv: bool = True

    model_config = ConfigDict(from_attributes=True)


class PlgPreisCreate(BaseModel):
    """Schema for creating a new Preis."""
    plugin_id: str
    projekttyp_id: str
    modell: str = PlgPreisModell.MONATLICH.value
    preis: float
    waehrung: str = "EUR"
    staffel_ab_benutzer: int | None = None
    staffel_preis: float | None = None
    preis_pro_api_call: float | None = None
    inkludierte_api_calls: int | None = None
    einrichtungsgebuehr: float = 0.0
    gueltig_ab: datetime | None = None
    gueltig_bis: datetime | None = None
    ist_aktiv: bool = True


class PlgPreisUpdate(BaseModel):
    """Schema for updating a Preis (partial)."""
    modell: str | None = None
    preis: float | None = None
    waehrung: str | None = None
    staffel_ab_benutzer: int | None = None
    staffel_preis: float | None = None
    preis_pro_api_call: float | None = None
    inkludierte_api_calls: int | None = None
    einrichtungsgebuehr: float | None = None
    gueltig_ab: datetime | None = None
    gueltig_bis: datetime | None = None
    ist_aktiv: bool | None = None


class PlgPreisWithRelations(PlgPreisBase):
    """Preis with nested Plugin and Projekttyp names."""
    plugin_name: str | None = None
    projekttyp_name: str | None = None
    einrichtungsgebuehr: float = 0.0


class PlgPreisDetail(PlgPreisBase):
    """Preis with all fields."""
    staffel_ab_benutzer: int | None = None
    staffel_preis: float | None = None
    preis_pro_api_call: float | None = None
    preis_pro_datensatz: float | None = None
    inkludierte_api_calls: int | None = None
    einrichtungsgebuehr: float = 0.0
    gueltig_ab: datetime | None = None
    gueltig_bis: datetime | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class PlgPreisList(BaseModel):
    """Paginated list of prices."""
    items: list[PlgPreisBase]
    total: int


# =============================================================================
# Projekt Schemas
# =============================================================================

class PlgProjektBase(BaseModel):
    """Base schema for Projekt (Satellite)."""
    id: str
    slug: str
    name: str
    projekttyp_id: str
    ist_aktiv: bool = True

    model_config = ConfigDict(from_attributes=True)


class PlgProjektCreate(BaseModel):
    """Schema for creating a new Projekt."""
    slug: str
    name: str
    projekttyp_id: str
    beschreibung: str | None = None
    kontakt_name: str | None = None
    kontakt_email: str | None = None
    kontakt_telefon: str | None = None
    base_url: str | None = None
    geo_ort_id: str | None = None
    notizen: str | None = None


class PlgProjektUpdate(BaseModel):
    """Schema for updating a Projekt (partial)."""
    name: str | None = None
    projekttyp_id: str | None = None
    beschreibung: str | None = None
    kontakt_name: str | None = None
    kontakt_email: str | None = None
    kontakt_telefon: str | None = None
    base_url: str | None = None
    geo_ort_id: str | None = None
    notizen: str | None = None
    ist_aktiv: bool | None = None


class PlgProjektWithTyp(PlgProjektBase):
    """Projekt with nested Projekttyp."""
    projekttyp: PlgProjekttypBase | None = None
    beschreibung: str | None = None
    kontakt_email: str | None = None
    base_url: str | None = None


class PlgProjektDetail(PlgProjektWithTyp):
    """Projekt with all fields."""
    kontakt_name: str | None = None
    kontakt_telefon: str | None = None
    geo_ort_id: str | None = None
    aktiviert_am: datetime | None = None
    deaktiviert_am: datetime | None = None
    notizen: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class PlgProjektList(BaseModel):
    """Paginated list of projects."""
    items: list[PlgProjektWithTyp]
    total: int


class PlgProjektApiKeyResponse(BaseModel):
    """Response when generating new API key."""
    api_key: str
    message: str = "API-Key wurde generiert. Bitte sicher aufbewahren - er wird nur einmal angezeigt!"


# =============================================================================
# Lizenz Schemas
# =============================================================================

class PlgLizenzBase(BaseModel):
    """Base schema for Lizenz."""
    id: str
    projekt_id: str
    plugin_id: str
    status: str
    ist_testphase: bool = False
    lizenz_start: datetime
    lizenz_ende: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PlgLizenzCreate(BaseModel):
    """Schema for creating a new Lizenz."""
    projekt_id: str
    plugin_id: str
    preis_id: str | None = None
    ist_testphase: bool = False
    lizenz_ende: datetime | None = None
    notizen: str | None = None


class PlgLizenzUpdate(BaseModel):
    """Schema for updating a Lizenz (partial)."""
    status: str | None = None
    lizenz_ende: datetime | None = None
    notizen: str | None = None


class PlgLizenzKuendigung(BaseModel):
    """Schema for cancelling a license."""
    grund: str | None = None
    zum: datetime | None = None  # Effective cancellation date


class PlgLizenzWithRelations(PlgLizenzBase):
    """Lizenz with nested Projekt and Plugin names."""
    projekt_name: str | None = None
    plugin_name: str | None = None
    testphase_ende: datetime | None = None


class PlgLizenzDetail(PlgLizenzWithRelations):
    """Lizenz with all fields."""
    preis_id: str | None = None
    testphase_konvertiert: bool = False
    gekuendigt_am: datetime | None = None
    kuendigung_grund: str | None = None
    kuendigung_zum: datetime | None = None
    preis_snapshot: float | None = None
    preis_modell_snapshot: str | None = None
    plugin_version_bei_lizenzierung: str | None = None
    notizen: str | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class PlgLizenzList(BaseModel):
    """Paginated list of licenses."""
    items: list[PlgLizenzWithRelations]
    total: int


# =============================================================================
# Lizenz Historie Schemas
# =============================================================================

class PlgLizenzHistorieBase(BaseModel):
    """Base schema for Lizenz Historie."""
    id: str
    lizenz_id: str
    alter_status: str | None = None
    neuer_status: str
    aenderungsgrund: str | None = None
    geaendert_von_typ: str | None = None
    erstellt_am: datetime

    model_config = ConfigDict(from_attributes=True)


class PlgLizenzHistorieList(BaseModel):
    """List of license history entries."""
    items: list[PlgLizenzHistorieBase]


# =============================================================================
# Lizenz Check Schemas (for Satellites)
# =============================================================================

class PlgLizenzCheck(BaseModel):
    """Response for license check endpoint."""
    lizenziert: bool
    status: str | None = None
    lizenz_ende: datetime | None = None
    plugin_version: str | None = None
    ist_testphase: bool = False
    testphase_ende: datetime | None = None


# =============================================================================
# Marketplace Schemas (Public)
# =============================================================================

class MarketplacePluginBase(BaseModel):
    """Public plugin info for marketplace."""
    slug: str
    name: str
    beschreibung_kurz: str | None = None
    version: str
    kategorie_name: str | None = None
    icon: str | None = None
    thumbnail_url: str | None = None
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MarketplacePluginDetail(MarketplacePluginBase):
    """Detailed plugin info for marketplace."""
    beschreibung: str | None = None
    dokumentation_url: str | None = None
    changelog_url: str | None = None
    min_api_version: str | None = None


class MarketplacePreis(BaseModel):
    """Price info for marketplace."""
    projekttyp_slug: str
    projekttyp_name: str
    modell: str
    preis: float
    waehrung: str
    einrichtungsgebuehr: float = 0.0


class MarketplacePluginList(BaseModel):
    """List of marketplace plugins."""
    items: list[MarketplacePluginBase]
    total: int


class MarketplaceKategorieWithPlugins(PlgKategorieBase):
    """Kategorie with list of plugins for marketplace."""
    plugins: list[MarketplacePluginBase] = Field(default_factory=list)
