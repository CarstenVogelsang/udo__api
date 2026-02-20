"""
Pydantic validation schemas for Hersteller-Recherche JSON import.

Validates the JSON structure produced by the research AI.
All fields are as lenient as possible (Optional) to handle incomplete research results.
"""
from datetime import date
from pydantic import BaseModel


class RechercheLogoInfo(BaseModel):
    dateiname: str | None = None
    format: str | None = None
    quelle_url: str | None = None
    quelle_alternativ: str | None = None
    lizenz: str | None = None
    lizenz_code: str | None = None  # Optional code for direct FK lookup
    download_status: str | None = None
    dateigroesse_kb: int | None = None


class RechercheGPSRKontakt(BaseModel):
    name: str
    adresse: str | None = None
    land: str | None = None
    kontakt_email: str | None = None
    kontakt_telefon: str | None = None


class RechercheGPSRInverkehrbringer(RechercheGPSRKontakt):
    registergericht: str | None = None
    ust_id: str | None = None
    geschaeftsfuehrer: str | None = None


class RechercheGPSR(BaseModel):
    hersteller: RechercheGPSRKontakt | None = None
    inverkehrbringer_eu: RechercheGPSRInverkehrbringer | None = None
    hinweis: str | None = None
    verifiziert: bool = False


class RechercheTochtergesellschaft(BaseModel):
    name: str
    adresse: str | None = None
    kontakt: str | None = None
    geschaeftsfuehrer: str | None = None
    registergericht: str | None = None


class RechercheHauptlieferant(BaseModel):
    name: str
    typ: str | None = None
    adresse: str | None = None
    kontakt: str | None = None


class RechercheWeitererLieferant(BaseModel):
    name: str


class RechercheVertriebDACH(BaseModel):
    direktvertrieb: bool = False
    tochtergesellschaft_de: RechercheTochtergesellschaft | None = None
    hauptlieferant_de: RechercheHauptlieferant | None = None
    weitere_lieferanten: list[RechercheWeitererLieferant] = []
    empfehlung_bezugsweg: str | None = None


class RechercheSerie(BaseModel):
    name: str
    profil_b2c: str | None = None
    profil_b2b: str | None = None


class RechercheMarke(BaseModel):
    name: str
    profil_b2c: str | None = None
    profil_b2b: str | None = None
    logo: RechercheLogoInfo | None = None
    serien: list[RechercheSerie] = []


class RechercheHersteller(BaseModel):
    name: str
    name_kurz: str | None = None
    website: str | None = None
    herkunftsland: str | None = None
    gruendungsjahr: int | None = None
    gruender: str | None = None
    hauptsitz: str | None = None
    rechtsform: str | None = None
    rechtsform_code: str | None = None  # Optional code for direct FK lookup
    branche: str | None = None
    profil_b2c: str | None = None
    profil_b2b: str | None = None
    logo: RechercheLogoInfo | None = None
    gpsr: RechercheGPSR | None = None
    vertrieb_dach: RechercheVertriebDACH | None = None
    marken: list[RechercheMarke] = []


class RechercheQuelle(BaseModel):
    url: str
    beschreibung: str | None = None
    abrufdatum: date | None = None


class RechercheMeta(BaseModel):
    recherche_datum: date | None = None
    zielmarkt: str | None = None
    sprache: str = "de"
    erstellt_durch: str | None = None


class HerstellerRechercheImport(BaseModel):
    """Root schema for a complete Hersteller-Recherche JSON."""
    meta: RechercheMeta | None = None
    hersteller: RechercheHersteller
    quellen: list[RechercheQuelle] = []


# ============ Import Response ============

class ImportAktion(BaseModel):
    id: str
    aktion: str  # "angelegt", "aktualisiert", "unveraendert"


class ImportMarkeResult(BaseModel):
    name: str
    aktion: str
    serien_angelegt: int = 0


class ImportResult(BaseModel):
    status: str  # "success", "dry_run"
    hersteller: ImportAktion | None = None
    marken: list[ImportMarkeResult] = []
    medien: dict = {}  # {"angelegt": N, "download_ausstehend": N}
    quellen: dict = {}  # {"angelegt": N}
    profiltexte: dict = {}  # {"angelegt": N}
    vertriebsstruktur: dict = {}  # {"angelegt": N}
    warnungen: list[str] = []
