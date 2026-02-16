"""
Pydantic Schemas for Product (Produktdaten) API.

Covers: Artikel, Sortiment, Eigenschaft, Kategorie, Bilder, Werteliste.
"""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


# ============ Werteliste Schemas ============


class ProdWertelisteRead(BaseModel):
    """Single entry in a controlled vocabulary."""
    id: str
    typ: str
    code: str
    bezeichnung: str
    sortierung: int = 0
    ist_aktiv: bool = True

    model_config = ConfigDict(from_attributes=True)


class ProdWertelisteCreate(BaseModel):
    """Create a new Werteliste entry."""
    code: str
    bezeichnung: str
    sortierung: int = 0
    ist_aktiv: bool = True


# ============ Sortiment Schemas ============


class ProdSortimentRead(BaseModel):
    """Product sortiment definition."""
    id: str
    code: str
    name: str
    beschreibung: str | None = None
    sortierung: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProdArtikelSortimentRead(BaseModel):
    """Junction: article belongs to sortiment (with nested sortiment)."""
    id: str
    sortiment: ProdSortimentRead

    model_config = ConfigDict(from_attributes=True)


# ============ Eigenschaft Schemas ============


class ProdEigenschaftRead(BaseModel):
    """Property definition."""
    id: str
    code: str
    name: str
    daten_typ: str
    werteliste_typ: str | None = None
    einheit: str | None = None
    ist_pflicht: bool = False
    sortierung: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProdSortimentEigenschaftRead(BaseModel):
    """Blueprint entry: eigenschaft within a sortiment."""
    id: str
    ist_pflicht: bool | None = None
    sortierung: int = 0
    eigenschaft: ProdEigenschaftRead

    model_config = ConfigDict(from_attributes=True)


class ProdSortimentDetailRead(ProdSortimentRead):
    """Sortiment with its eigenschaft blueprint."""
    eigenschaft_zuordnungen: list[ProdSortimentEigenschaftRead] = []


# ============ Kategorie Schemas ============


class ProdKategorieRead(BaseModel):
    """Catalog category node."""
    id: str
    parent_id: str | None = None
    code: str
    name: str
    ebene: int = 1
    sortierung: int = 0
    ist_aktiv: bool = True

    model_config = ConfigDict(from_attributes=True)


class ProdKategorieCreate(BaseModel):
    """Create a new category."""
    parent_id: str | None = None
    code: str
    name: str
    ebene: int = 1
    sortierung: int = 0


class ProdKategorieTree(ProdKategorieRead):
    """Category with children (for tree rendering)."""
    children: list["ProdKategorieTree"] = []


# ============ Artikel Text Schemas (i18n) ============


class ProdArtikelTextRead(BaseModel):
    """Translated product text entry."""
    id: str
    sprache: str
    bezeichnung: str | None = None
    beschreibung: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProdArtikelTextCreate(BaseModel):
    """Create/update a translation."""
    sprache: str
    bezeichnung: str | None = None
    beschreibung: str | None = None


# ============ Artikel Bild Schemas ============


class ProdArtikelBildRead(BaseModel):
    """Product image entry."""
    id: str
    bildart: str
    dateiname: str | None = None
    url: str
    alt_text: str | None = None
    sortierung: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProdArtikelBildCreate(BaseModel):
    """Create a new product image."""
    bildart: str
    dateiname: str | None = None
    url: str
    alt_text: str | None = None
    sortierung: int = 0


# ============ Artikel Eigenschaft Schemas ============


class ProdArtikelEigenschaftRead(BaseModel):
    """Concrete property value for an article."""
    id: str
    eigenschaft: ProdEigenschaftRead
    wert_text: str | None = None
    wert_ganzzahl: int | None = None
    wert_dezimal: float | None = None
    wert_bool: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class ProdArtikelEigenschaftCreate(BaseModel):
    """Set a property value by eigenschaft code."""
    eigenschaft_code: str
    wert_text: str | None = None
    wert_ganzzahl: int | None = None
    wert_dezimal: float | None = None
    wert_bool: bool | None = None


class ProdArtikelEigenschaftenBulk(BaseModel):
    """Bulk set property values for an article."""
    eigenschaften: list[ProdArtikelEigenschaftCreate]


# ============ Artikel Schemas ============


class ProdArtikelBase(BaseModel):
    """Core article fields (without relations)."""
    id: str
    hersteller_id: str
    marke_id: str
    serie_id: str | None = None
    kategorie_id: str | None = None

    # Grunddaten
    artikelnummer_hersteller: str
    ean_gtin: str | None = None
    artikelstatus: str = "NEU"
    bezeichnung: str
    bezeichnung_b2c: str | None = None
    beschreibung: str | None = None
    beschreibung_b2c: str | None = None
    ursprungsland: str | None = None
    zolltarifnummer: str | None = None

    # Preise
    listenpreis_netto: float | None = None
    uvp_brutto: float | None = None
    einkaufspreis_netto: float | None = None
    mwst_satz: float | None = None
    waehrung: str = "EUR"
    verpackungseinheit: int | None = None
    rabattfaehig: bool | None = None
    verfuegbarkeit: str | None = None
    erstlieferdatum: date | None = None
    neuheit_jahr: int | None = None

    # PAngV
    pangv_einheit: str | None = None
    pangv_inhalt: float | None = None
    pangv_grundmenge: float | None = None

    # Logistik
    gewicht_netto_g: int | None = None
    gewicht_brutto_g: int | None = None
    verpackung_laenge_mm: int | None = None
    verpackung_breite_mm: int | None = None
    verpackung_hoehe_mm: int | None = None
    mindestbestellmenge: int | None = None

    # Compliance
    ce_kennzeichen: bool = False
    altersfreigabe_min: int | None = None
    warnhinweise: str | None = None
    sicherheitssymbol: str | None = None
    gpsr_bevollmaechtigter_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProdArtikelCreate(BaseModel):
    """Create a new article."""
    hersteller_id: str
    marke_id: str
    serie_id: str | None = None
    kategorie_id: str | None = None

    artikelnummer_hersteller: str
    ean_gtin: str | None = None
    artikelstatus: str = "NEU"
    bezeichnung: str
    bezeichnung_b2c: str | None = None
    beschreibung: str | None = None
    beschreibung_b2c: str | None = None
    ursprungsland: str | None = None
    zolltarifnummer: str | None = None

    listenpreis_netto: float | None = None
    uvp_brutto: float | None = None
    einkaufspreis_netto: float | None = None
    mwst_satz: float | None = None
    waehrung: str = "EUR"
    verpackungseinheit: int | None = None
    rabattfaehig: bool | None = None
    verfuegbarkeit: str | None = None
    erstlieferdatum: date | None = None
    neuheit_jahr: int | None = None

    pangv_einheit: str | None = None
    pangv_inhalt: float | None = None
    pangv_grundmenge: float | None = None

    gewicht_netto_g: int | None = None
    gewicht_brutto_g: int | None = None
    verpackung_laenge_mm: int | None = None
    verpackung_breite_mm: int | None = None
    verpackung_hoehe_mm: int | None = None
    mindestbestellmenge: int | None = None

    ce_kennzeichen: bool = False
    altersfreigabe_min: int | None = None
    warnhinweise: str | None = None
    sicherheitssymbol: str | None = None
    gpsr_bevollmaechtigter_id: str | None = None


class ProdArtikelUpdate(BaseModel):
    """Update an existing article (all fields optional)."""
    marke_id: str | None = None
    serie_id: str | None = None
    kategorie_id: str | None = None

    artikelnummer_hersteller: str | None = None
    ean_gtin: str | None = None
    artikelstatus: str | None = None
    bezeichnung: str | None = None
    bezeichnung_b2c: str | None = None
    beschreibung: str | None = None
    beschreibung_b2c: str | None = None
    ursprungsland: str | None = None
    zolltarifnummer: str | None = None

    listenpreis_netto: float | None = None
    uvp_brutto: float | None = None
    einkaufspreis_netto: float | None = None
    mwst_satz: float | None = None
    waehrung: str | None = None
    verpackungseinheit: int | None = None
    rabattfaehig: bool | None = None
    verfuegbarkeit: str | None = None
    erstlieferdatum: date | None = None
    neuheit_jahr: int | None = None

    pangv_einheit: str | None = None
    pangv_inhalt: float | None = None
    pangv_grundmenge: float | None = None

    gewicht_netto_g: int | None = None
    gewicht_brutto_g: int | None = None
    verpackung_laenge_mm: int | None = None
    verpackung_breite_mm: int | None = None
    verpackung_hoehe_mm: int | None = None
    mindestbestellmenge: int | None = None

    ce_kennzeichen: bool | None = None
    altersfreigabe_min: int | None = None
    warnhinweise: str | None = None
    sicherheitssymbol: str | None = None
    gpsr_bevollmaechtigter_id: str | None = None


class ProdArtikelListItem(ProdArtikelBase):
    """Article in list view (with sortiment tags)."""
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None
    geloescht_am: datetime | None = None
    sortiment_zuordnungen: list[ProdArtikelSortimentRead] = []


class ProdArtikelDetail(ProdArtikelBase):
    """Full article detail with all nested relations."""
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None
    geloescht_am: datetime | None = None
    kategorie: ProdKategorieRead | None = None
    sortiment_zuordnungen: list[ProdArtikelSortimentRead] = []
    eigenschaft_werte: list[ProdArtikelEigenschaftRead] = []
    bilder: list[ProdArtikelBildRead] = []
    texte: list[ProdArtikelTextRead] = []


# ============ List Response Schemas ============


class ProdArtikelList(BaseModel):
    """Paginated list of articles."""
    items: list[ProdArtikelListItem]
    total: int
    page: int = 1
    page_size: int = 50
