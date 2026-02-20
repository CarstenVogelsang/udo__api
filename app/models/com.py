"""
SQLAlchemy Models for Company (Unternehmen) data.

Provides business entity data with geographic references.
Table prefix: com_ (analog zu geo_ für Geodaten)
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    JSON,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.geo import Base, UUID, generate_uuid


class ComUnternehmenOrganisation(Base):
    """
    Junction table for N:M relationship between Unternehmen and Organisation.

    Allows a company to belong to multiple organizations and
    an organization to contain multiple companies.

    Legacy migration note:
    - spi_tStore.kStoreGruppe1 -> organisation_id (with legacy_id lookup)
    - spi_tStore.kStoreGruppe2 -> second entry in this table
    """
    __tablename__ = "com_unternehmen_organisation"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    organisation_id = Column(UUID, ForeignKey("com_organisation.id"), nullable=False)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Relationships
    unternehmen = relationship("ComUnternehmen", back_populates="organisation_zuordnungen")
    organisation = relationship("ComOrganisation", back_populates="unternehmen_zuordnungen")

    __table_args__ = (
        Index("idx_uo_unternehmen", "unternehmen_id"),
        Index("idx_uo_organisation", "organisation_id"),
        Index("uq_unternehmen_organisation", "unternehmen_id", "organisation_id", unique=True),
    )

    def __repr__(self):
        return f"<ComUnternehmenOrganisation {self.unternehmen_id} <-> {self.organisation_id}>"


class ComOrganisation(Base):
    """
    Organization/Group entity.

    Represents groupings of companies such as:
    - Buying groups (Einkaufsgemeinschaften)
    - Corporate groups (Konzerne)
    - Associations (Verbände)

    Legacy mapping from spi_tStoreGruppe:
    - kStoreGruppe -> legacy_id
    - cKurzname -> kurzname
    """
    __tablename__ = "com_organisation"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    legacy_id = Column(Integer, unique=True, index=True)  # kStoreGruppe from spi_tStoreGruppe
    kurzname = Column(String(100), nullable=False, index=True)  # cKurzname
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to junction table
    unternehmen_zuordnungen = relationship(
        "ComUnternehmenOrganisation",
        back_populates="organisation",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_organisation_kurzname", "kurzname"),
        Index("idx_organisation_legacy", "legacy_id"),
    )

    @property
    def unternehmen(self) -> list:
        """Returns list of associated Unternehmen."""
        return [z.unternehmen for z in self.unternehmen_zuordnungen]

    def __repr__(self):
        return f"<ComOrganisation {self.kurzname}>"


class ComUnternehmen(Base):
    """
    Company/Business entity with geo reference.

    Each company is linked to a GeoOrt (city/municipality)
    which provides the full geo hierarchy (Ort → Kreis → Bundesland → Land).

    Legacy mapping from spi_tStore:
    - kStore → legacy_id
    - dStatusUnternehmen → status_datum
    - cKurzname → kurzname
    - cFirmierung → firmierung
    - cStrasse → strasse
    - cStrasseHausNr → strasse_hausnr
    - kGeoOrt → geo_ort_id (via GeoOrt.legacy_id lookup)
    """
    __tablename__ = "com_unternehmen"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    legacy_id = Column(Integer, unique=True, index=True)  # kStore from spi_tStore
    status_id = Column(UUID, ForeignKey("bas_status.id"), nullable=True)
    status_datum = Column(DateTime)  # dStatusUnternehmen
    kurzname = Column(String(200), index=True)  # cKurzname
    firmierung = Column(String(255))  # cFirmierung
    adresszeile = Column(String(500))  # Raw address line (international)
    strasse = Column(String(255))  # cStrasse (parsed, DACH only)
    strasse_hausnr = Column(String(50))  # cStrasseHausNr (parsed, DACH only)
    website = Column(String(255))
    email = Column(String(255), index=True)
    email2 = Column(String(255))  # Second email address
    telefon = Column(String(50))
    fax = Column(String(50))
    metadaten = Column(JSON, default=dict)  # Rich data from external providers (google, yelp, etc.)
    sprache_id = Column(UUID, ForeignKey("bas_sprache.id"), nullable=True)
    geo_ort_id = Column(UUID, ForeignKey("geo_ort.id"), nullable=True)  # kGeoOrt → GeoOrt
    wz_code = Column(String(10), ForeignKey("brn_branche.wz_code"), nullable=True)  # Primary WZ-2008 code
    # Hersteller-spezifische Felder
    gruendungsjahr = Column(Integer, nullable=True)
    gruender = Column(String(255), nullable=True)
    herkunftsland_id = Column(UUID, ForeignKey("geo_land.id"), nullable=True)
    rechtsform_id = Column(UUID, ForeignKey("bas_rechtsform.id"), nullable=True)
    gpsr_default_bevollmaechtigter_id = Column(
        UUID, ForeignKey("com_unternehmen.id"), nullable=True
    )  # Default EU-Bevollmächtigter für GPSR
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    geloescht_am = Column(DateTime, nullable=True)  # Soft delete timestamp

    # Relationship to Status
    status = relationship("BasStatus", lazy="joined")
    # Relationship to GeoOrt - provides full geo hierarchy
    geo_ort = relationship("GeoOrt", lazy="joined")
    # Relationship to language
    sprache = relationship("BasSprache", lazy="joined")
    # Relationship to WZ-2008 Branche (primary classification)
    branche = relationship("BrnBranche", lazy="joined")
    # Hersteller-spezifische Relationships
    herkunftsland = relationship("GeoLand", foreign_keys=[herkunftsland_id], lazy="joined")
    rechtsform = relationship("BasRechtsform", lazy="joined")
    gpsr_default_bevollmaechtigter = relationship(
        "ComUnternehmen",
        foreign_keys=[gpsr_default_bevollmaechtigter_id],
        remote_side=[id],
    )

    # Relationship to Google Place Types (N:M)
    google_type_zuordnungen = relationship(
        "ComUnternehmenGoogleType",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Relationship to UDO Klassifikationen (N:M)
    klassifikation_zuordnungen = relationship(
        "ComUnternehmenKlassifikation",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    @property
    def google_types(self) -> list:
        """Returns list of Google Place Types (gcids)."""
        return [z.gcid for z in self.google_type_zuordnungen]

    @property
    def primaerer_google_type(self) -> str | None:
        """Returns the primary Google Place Type."""
        for z in self.google_type_zuordnungen:
            if z.ist_primaer:
                return z.gcid
        return None

    @property
    def klassifikationen(self) -> list:
        """Returns list of UDO Klassifikationen."""
        return [z.klassifikation for z in self.klassifikation_zuordnungen]

    # Relationship to Organisationen via junction table
    organisation_zuordnungen = relationship(
        "ComUnternehmenOrganisation",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    @property
    def organisationen(self) -> list:
        """Returns list of associated Organisationen."""
        return [z.organisation for z in self.organisation_zuordnungen]

    # Relationship to Business Identifiers (USt-ID, DUNS, etc.)
    identifikationen = relationship(
        "ComUnternehmenIdentifikation",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # Relationship to Kontakte
    kontakte = relationship(
        "ComKontakt",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Relationship to Lieferbeziehungen (as customer)
    lieferbeziehungen = relationship(
        "ComLieferbeziehung",
        foreign_keys="ComLieferbeziehung.unternehmen_id",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Relationship to Sortiment (brands/series carried)
    sortimente = relationship(
        "ComUnternehmenSortiment",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Relationship to Dienstleistungen
    dienstleistung_zuordnungen = relationship(
        "ComUnternehmenDienstleistung",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Relationship to Bonität assessments
    bonitaeten = relationship(
        "ComBonitaet",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Relationship to platform ratings (Google, Yelp, etc.)
    bewertungen = relationship(
        "ComUnternehmenBewertung",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # Relationship to raw source data from external providers
    quelldaten = relationship(
        "ComUnternehmenQuelldaten",
        back_populates="unternehmen",
        lazy="noload",  # Not auto-loaded (large JSONs ~20KB each)
        cascade="all, delete-orphan",
    )

    # Hersteller-Recherche: Profiltexte, Medien, Quellen, Vertriebsstruktur
    profiltexte = relationship(
        "ComProfiltext",
        foreign_keys="ComProfiltext.unternehmen_id",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    medien = relationship(
        "ComMedien",
        foreign_keys="ComMedien.unternehmen_id",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    quellen = relationship(
        "ComQuelle",
        back_populates="unternehmen",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    vertriebskanaele = relationship(
        "ComVertriebsstruktur",
        foreign_keys="ComVertriebsstruktur.hersteller_id",
        back_populates="hersteller",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_unternehmen_geo_ort", "geo_ort_id"),
        Index("idx_unternehmen_kurzname", "kurzname"),
        Index("idx_unternehmen_legacy", "legacy_id"),
        Index("idx_unternehmen_sprache", "sprache_id"),
        Index("idx_unternehmen_status", "status_id"),
        Index("idx_unternehmen_wz_code", "wz_code"),
        Index("idx_unternehmen_herkunftsland", "herkunftsland_id"),
        Index("idx_unternehmen_rechtsform", "rechtsform_id"),
        Index("idx_unternehmen_gpsr_bevollm", "gpsr_default_bevollmaechtigter_id"),
    )

    def __repr__(self):
        return f"<ComUnternehmen {self.kurzname or self.firmierung}>"


class ComKontakt(Base):
    """
    Contact person for a company.

    Each contact belongs to exactly one company (1:N relationship).
    A company can have multiple contacts, with one optionally marked as primary.
    """
    __tablename__ = "com_kontakt"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    legacy_id = Column(Integer, unique=True, index=True, nullable=True)  # For future legacy sync

    # Contact type and title
    typ = Column(String(50))  # "Geschäftsführer", "Einkauf", "Vertrieb", etc.
    titel = Column(String(20))  # "Dr.", "Prof.", etc.
    anrede = Column(String(20))  # "Herr", "Frau", "Divers"

    # Name (required)
    vorname = Column(String(100), nullable=False)
    nachname = Column(String(100), nullable=False)

    # Position in company
    position = Column(String(255))  # Job title
    abteilung = Column(String(100))  # Department

    # Contact details
    telefon = Column(String(50))  # Landline
    mobil = Column(String(50))  # Mobile
    fax = Column(String(50))  # Fax
    email = Column(String(255), index=True)  # Not unique - same email can exist multiple times

    # Additional info
    notizen = Column(Text)  # Free text notes
    ist_hauptkontakt = Column(Boolean, default=False)  # Primary contact flag

    # Timestamps
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    geloescht_am = Column(DateTime, nullable=True)  # Soft delete (cascaded from Unternehmen)

    # Relationship back to Unternehmen
    unternehmen = relationship("ComUnternehmen", back_populates="kontakte")

    __table_args__ = (
        Index("idx_kontakt_unternehmen", "unternehmen_id"),
        Index("idx_kontakt_email", "email"),
        Index("idx_kontakt_legacy", "legacy_id"),
    )

    def __repr__(self):
        return f"<ComKontakt {self.vorname} {self.nachname}>"


class ComUnternehmenIdentifikation(Base):
    """
    Business identifiers for companies (USt-ID, DUNS, W-IdNr, etc.).

    Unlike ComExternalId (import artifacts), these are real-world,
    publicly registered business identifiers used for deduplication
    and compliance.

    Known types:
    - ust_id: Umsatzsteuer-Identifikationsnummer (DE123456789)
    - duns: D&B DUNS Number (123456789)
    - w_idnr: Wirtschafts-Identifikationsnr. (DE123456789012)
    - hrnr: Handelsregisternummer (HRB 12345)
    - glnr: Global Location Number (4012345000000)
    """
    __tablename__ = "com_unternehmen_identifikation"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    typ = Column(String(50), nullable=False)        # "ust_id", "duns", "w_idnr", "hrnr"
    wert = Column(String(255), nullable=False)       # "DE123456789"
    ist_verifiziert = Column(Boolean, default=False)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="identifikationen")

    __table_args__ = (
        Index("uq_unt_ident_typ", "unternehmen_id", "typ", unique=True),
        Index("idx_ident_lookup", "typ", "wert"),
    )

    def __repr__(self):
        return f"<ComUnternehmenIdentifikation {self.typ}={self.wert}>"


class ComExternalId(Base):
    """
    External identifiers for companies and contacts.

    Allows multiple IDs from different source systems per entity.
    Examples: smartmail subscriber_id=39, evendo kundennr=12345
    """
    __tablename__ = "com_external_id"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False)      # "unternehmen", "kontakt"
    entity_id = Column(UUID, nullable=False)
    source_name = Column(String(100), nullable=False)      # "smartmail", "evendo"
    id_type = Column(String(100), nullable=False)          # "subscriber_id", "kundennr"
    external_value = Column(String(255), nullable=False)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_extid_entity", "entity_type", "entity_id"),
        Index("idx_extid_lookup", "source_name", "id_type", "external_value"),
        Index(
            "uq_external_id",
            "entity_type", "entity_id", "source_name", "id_type",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<ComExternalId {self.source_name}:{self.id_type}={self.external_value}>"


# ============ Manufacturer / Brand / Series ============


class ComMarke(Base):
    """
    Brand belonging to a manufacturer (Hersteller).

    A manufacturer (ComUnternehmen) can have multiple brands.
    E.g., Märklin → Märklin, Trix, LGB.
    """
    __tablename__ = "com_marke"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    hersteller_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    name = Column(String(100), nullable=False)  # "Märklin", "Trix", "LGB"
    kurzname = Column(String(50))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hersteller = relationship("ComUnternehmen", foreign_keys=[hersteller_id])
    serien = relationship(
        "ComSerie", back_populates="marke",
        lazy="selectin", cascade="all, delete-orphan"
    )
    profiltexte = relationship(
        "ComProfiltext",
        foreign_keys="ComProfiltext.marke_id",
        back_populates="marke",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    medien = relationship(
        "ComMedien",
        foreign_keys="ComMedien.marke_id",
        back_populates="marke",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("uq_marke_hersteller_name", "hersteller_id", "name", unique=True),
        Index("idx_marke_name", "name"),
    )

    def __repr__(self):
        return f"<ComMarke {self.name}>"


class ComSerie(Base):
    """
    Product series belonging to a brand.

    E.g., Märklin → MyWorld, Premium Spur 1.
    """
    __tablename__ = "com_serie"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    marke_id = Column(UUID, ForeignKey("com_marke.id"), nullable=False)
    name = Column(String(100), nullable=False)  # "MyWorld", "Premium Spur 1"
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    marke = relationship("ComMarke", back_populates="serien")
    profiltexte = relationship(
        "ComProfiltext",
        foreign_keys="ComProfiltext.serie_id",
        back_populates="serie",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("uq_serie_marke_name", "marke_id", "name", unique=True),
    )

    def __repr__(self):
        return f"<ComSerie {self.name}>"


# ============ Supplier Relationship ============


class ComLieferbeziehung(Base):
    """
    Customer-supplier relationship between two companies.

    The 'unternehmen' is the dealer/customer, 'lieferant' is the supplier.
    Stores supplier-specific attributes like customer number, store type,
    and MHI membership.
    """
    __tablename__ = "com_lieferbeziehung"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    lieferant_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    kundennummer = Column(String(50))  # Customer number at supplier
    store_typ = Column(String(20))  # "maerklin_store", "shop_in_shop", "wandloesung", "standard"
    bonus_haendler = Column(Boolean, default=False)
    in_haendlersuche = Column(Boolean, default=True)  # Inverted from "keine Anzeige"
    ist_mhi = Column(Boolean, default=False)  # MHI member
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unternehmen = relationship(
        "ComUnternehmen",
        foreign_keys=[unternehmen_id],
        back_populates="lieferbeziehungen",
    )
    lieferant = relationship("ComUnternehmen", foreign_keys=[lieferant_id])

    __table_args__ = (
        Index("uq_lieferbeziehung", "unternehmen_id", "lieferant_id", unique=True),
        Index("idx_lieferbeziehung_lieferant", "lieferant_id"),
    )

    def __repr__(self):
        return f"<ComLieferbeziehung {self.unternehmen_id} → {self.lieferant_id}>"


# ============ Sortiment (Dealer carries Brand/Series) ============


class ComUnternehmenSortiment(Base):
    """
    Junction: which brands/series a dealer carries.

    Either marke_id or serie_id must be set (not both None).
    """
    __tablename__ = "com_unternehmen_sortiment"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    marke_id = Column(UUID, ForeignKey("com_marke.id"), nullable=True)
    serie_id = Column(UUID, ForeignKey("com_serie.id"), nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="sortimente")
    marke = relationship("ComMarke", lazy="joined")
    serie = relationship("ComSerie", lazy="joined")

    __table_args__ = (
        Index("idx_sortiment_unternehmen", "unternehmen_id"),
        Index("idx_sortiment_marke", "marke_id"),
        Index("idx_sortiment_serie", "serie_id"),
    )

    def __repr__(self):
        ref = self.marke_id or self.serie_id
        return f"<ComUnternehmenSortiment {self.unternehmen_id} → {ref}>"


# ============ Services / Dienstleistungen ============


class ComDienstleistung(Base):
    """
    Service offered by dealers (e.g., model railway repair service).

    Lookup table — services are referenced by junction table.
    """
    __tablename__ = "com_dienstleistung"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    beschreibung = Column(Text)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ComDienstleistung {self.name}>"


class ComUnternehmenDienstleistung(Base):
    """Junction: which services a company offers."""
    __tablename__ = "com_unternehmen_dienstleistung"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    dienstleistung_id = Column(UUID, ForeignKey("com_dienstleistung.id"), nullable=False)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="dienstleistung_zuordnungen")
    dienstleistung = relationship("ComDienstleistung", lazy="joined")

    __table_args__ = (
        Index("uq_unternehmen_dienstleistung", "unternehmen_id", "dienstleistung_id", unique=True),
        Index("idx_ud_unternehmen", "unternehmen_id"),
    )

    def __repr__(self):
        return f"<ComUnternehmenDienstleistung {self.unternehmen_id} → {self.dienstleistung_id}>"


# ============ Credit Rating / Bonität ============


class ComBonitaet(Base):
    """
    Anonymized credit assessment for a company.

    Score 1 (very good) to 5 (very bad).
    Source is anonymized (e.g., "Lieferantenauskunft" instead of specific supplier).
    Multiple assessments per company are possible (from different sources/dates).
    """
    __tablename__ = "com_bonitaet"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    score = Column(Integer, nullable=False)  # 1-5 (1=sehr gut, 5=sehr schlecht)
    quelle = Column(String(100))  # Anonymized: "Lieferantenauskunft"
    notiz = Column(Text)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="bonitaeten")

    __table_args__ = (
        Index("idx_bonitaet_unternehmen", "unternehmen_id"),
    )

    def __repr__(self):
        return f"<ComBonitaet {self.unternehmen_id}: Score {self.score}>"


# ============ Platform Ratings (Google, Yelp, etc.) ============


class ComUnternehmenBewertung(Base):
    """Platform rating for a company (1:N, one per platform).

    Stores aggregated ratings from external platforms (Google, Yelp, etc.).
    UNIQUE constraint ensures one rating per platform per company (upsert pattern).
    """
    __tablename__ = "com_unternehmen_bewertung"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    plattform_id = Column(UUID, ForeignKey("bas_bewertungsplattform.id"), nullable=False)
    bewertung = Column(Float, nullable=False)             # 4.4 (platform avg rating)
    anzahl_bewertungen = Column(Integer)                   # 330 (total review count)
    verteilung = Column(JSON)                              # {"1": 9, "2": 7, ...}
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="bewertungen")
    plattform = relationship("BasBewertungsplattform", lazy="joined")

    __table_args__ = (
        Index("idx_bewertung_unternehmen", "unternehmen_id"),
        Index("idx_bewertung_plattform", "plattform_id"),
        Index(
            "uq_bewertung_unternehmen_plattform",
            "unternehmen_id", "plattform_id",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<ComUnternehmenBewertung {self.unternehmen_id}: {self.bewertung}>"


# ============ Source Data from External Providers ============


class ComUnternehmenQuelldaten(Base):
    """Raw source data from external providers (1:N per Unternehmen).

    Stores the complete API response for re-processing without
    additional API costs. Each provider gets its own entry,
    updated on re-sync (upsert on unternehmen_id + provider + provider_id).
    """
    __tablename__ = "com_unternehmen_quelldaten"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    provider = Column(String(50), nullable=False)      # "dataforseo", "google_places", "yelp"
    provider_id = Column(String(255))                   # External ID (e.g., Google place_id)
    rohdaten = Column(JSON, nullable=False)             # Complete raw JSON from provider
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="quelldaten")

    __table_args__ = (
        Index("idx_quelldaten_unternehmen", "unternehmen_id"),
        Index(
            "uq_quelldaten_provider",
            "unternehmen_id", "provider", "provider_id",
            unique=True,
        ),
    )

    def __repr__(self):
        return f"<ComUnternehmenQuelldaten {self.provider}:{self.provider_id}>"


# ============ Classification / Kategorisierung ============


class ComUnternehmenGoogleType(Base):
    """
    Junction table: Unternehmen ↔ Google Place Types.

    Stores Google Place Types for a company. Each company can have
    multiple types, with one marked as primary. Types can also be
    marked as derived (e.g., "restaurant" derived from "chinese_restaurant").

    References brn_google_kategorie for type metadata (name_de, name_en).
    """
    __tablename__ = "com_unternehmen_google_type"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    gcid = Column(String(100), ForeignKey("brn_google_kategorie.gcid"), nullable=False)
    ist_primaer = Column(Boolean, default=False)      # Primary type (max. 1 per company)
    ist_abgeleitet = Column(Boolean, default=False)   # True if parent type (auto-derived)
    quelle = Column(String(50))                       # "google_places", "dataforseo", "manuell"
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="google_type_zuordnungen")
    google_kategorie = relationship("BrnGoogleKategorie", lazy="joined")

    __table_args__ = (
        Index("uq_unt_gtype", "unternehmen_id", "gcid", unique=True),
        Index("idx_unt_gtype_unternehmen", "unternehmen_id"),
        Index("idx_unt_gtype_gcid", "gcid"),
        Index("idx_unt_gtype_primaer", "ist_primaer", postgresql_where="ist_primaer = true"),
    )

    def __repr__(self):
        primary = " (primary)" if self.ist_primaer else ""
        return f"<ComUnternehmenGoogleType {self.gcid}{primary}>"


class ComKlassifikation(Base):
    """
    UDO-specific classification taxonomy.

    Provides German-specific categories that supplement Google Place Types.
    E.g., "Döner-Imbiss", "Pommesbude", "Currywurstbude".

    Can optionally map to a Google Place Type for cross-referencing.
    Supports hierarchy via parent_id.
    """
    __tablename__ = "com_klassifikation"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    slug = Column(String(100), unique=True, nullable=False)  # "doener_imbiss"
    name_de = Column(String(200), nullable=False)            # "Döner-Imbiss"
    beschreibung = Column(Text)
    dimension = Column(String(50))                           # "kueche", "betriebsart", "angebot"
    google_mapping_gcid = Column(
        String(100),
        ForeignKey("brn_google_kategorie.gcid"),
        nullable=True
    )  # Optional: maps to Google category
    parent_id = Column(UUID, ForeignKey("com_klassifikation.id"), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("ComKlassifikation", remote_side=[id], lazy="joined")
    google_kategorie = relationship("BrnGoogleKategorie", lazy="joined")

    __table_args__ = (
        Index("idx_klassifikation_slug", "slug"),
        Index("idx_klassifikation_dimension", "dimension"),
        Index("idx_klassifikation_parent", "parent_id"),
    )

    def __repr__(self):
        return f"<ComKlassifikation {self.slug}>"


class ComUnternehmenKlassifikation(Base):
    """
    Junction table: Unternehmen ↔ UDO Klassifikation.

    Allows a company to have multiple UDO classifications,
    with one optionally marked as primary per dimension.
    """
    __tablename__ = "com_unternehmen_klassifikation"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    klassifikation_id = Column(UUID, ForeignKey("com_klassifikation.id"), nullable=False)
    ist_primaer = Column(Boolean, default=False)
    quelle = Column(String(50))  # "manuell", "regel", "ki"
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="klassifikation_zuordnungen")
    klassifikation = relationship("ComKlassifikation", lazy="joined")

    __table_args__ = (
        Index("uq_unt_klass", "unternehmen_id", "klassifikation_id", unique=True),
        Index("idx_unt_klass_unternehmen", "unternehmen_id"),
        Index("idx_unt_klass_klassifikation", "klassifikation_id"),
    )


# ============ Profiltexte (B2C / B2B) ============


class ComProfiltext(Base):
    """
    Profile text for a company, brand, or series (B2C/B2B, i18n-ready).

    Polymorphic: exactly ONE of unternehmen_id, marke_id, serie_id must be set.
    Allows separate B2C and B2B texts per entity and language.
    """
    __tablename__ = "com_profiltext"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=True)
    marke_id = Column(UUID, ForeignKey("com_marke.id"), nullable=True)
    serie_id = Column(UUID, ForeignKey("com_serie.id"), nullable=True)
    typ = Column(String(10), nullable=False)  # "b2c", "b2b"
    sprache = Column(String(5), nullable=False, default="de")  # ISO 639-1
    text = Column(Text, nullable=False)
    quelle = Column(String(50))  # "recherche_ki", "manuell"
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="profiltexte")
    marke = relationship("ComMarke", back_populates="profiltexte")
    serie = relationship("ComSerie", back_populates="profiltexte")

    __table_args__ = (
        # Partial unique indices: one text per entity + language + type
        Index(
            "uq_profiltext_unternehmen",
            "unternehmen_id", "sprache", "typ",
            unique=True,
            postgresql_where="unternehmen_id IS NOT NULL",
        ),
        Index(
            "uq_profiltext_marke",
            "marke_id", "sprache", "typ",
            unique=True,
            postgresql_where="marke_id IS NOT NULL",
        ),
        Index(
            "uq_profiltext_serie",
            "serie_id", "sprache", "typ",
            unique=True,
            postgresql_where="serie_id IS NOT NULL",
        ),
        Index("idx_profiltext_unternehmen", "unternehmen_id"),
        Index("idx_profiltext_marke", "marke_id"),
        Index("idx_profiltext_serie", "serie_id"),
    )

    def __repr__(self):
        entity = self.unternehmen_id or self.marke_id or self.serie_id
        return f"<ComProfiltext {self.typ}/{self.sprache} for {entity}>"


# ============ Medien (Logos, Bilder) ============


class ComMedien(Base):
    """
    Media asset for a company or brand (logos, images).

    Polymorphic: exactly ONE of unternehmen_id, marke_id must be set.
    Tracks download status and license information.
    """
    __tablename__ = "com_medien"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=True)
    marke_id = Column(UUID, ForeignKey("com_marke.id"), nullable=True)
    medienart = Column(String(20), nullable=False)  # "LOGO", "LOGO_ICON", "TITELBILD", "FOTO"
    dateiname = Column(String(200))  # Local filename after download
    dateiformat = Column(String(10))  # "png", "svg", "jpg"
    url_quelle = Column(String(500))  # Source URL (where downloaded from)
    alt_text = Column(String(200))
    sortierung = Column(Integer, default=0)
    ist_heruntergeladen = Column(Boolean, default=False)
    download_fehler = Column(String(500))  # Error message on failed download
    lizenz_id = Column(UUID, ForeignKey("bas_medien_lizenz.id"), nullable=True)
    lizenz_hinweis = Column(String(500))  # Free-text license note
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="medien")
    marke = relationship("ComMarke", back_populates="medien")
    lizenz = relationship("BasMedienLizenz", lazy="joined")

    __table_args__ = (
        Index("idx_medien_unternehmen", "unternehmen_id"),
        Index("idx_medien_marke", "marke_id"),
        Index("idx_medien_lizenz", "lizenz_id"),
        Index("idx_medien_art", "medienart"),
    )

    def __repr__(self):
        entity = self.unternehmen_id or self.marke_id
        return f"<ComMedien {self.medienart} for {entity}>"


# ============ Quellen (Source References) ============


class ComQuelle(Base):
    """
    Source reference for a company (URLs used during research).

    Tracks where information came from (official website, Wikipedia, etc.).
    """
    __tablename__ = "com_quelle"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    unternehmen_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    url = Column(String(500), nullable=False)
    beschreibung = Column(String(500))  # "Offizielle Website", "Wikipedia"
    abrufdatum = Column(Date)  # When the source was accessed
    quelle_typ = Column(String(30), default="recherche_ki")  # "recherche_ki", "manuell", "import"
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    unternehmen = relationship("ComUnternehmen", back_populates="quellen")

    __table_args__ = (
        Index("uq_quelle_url", "unternehmen_id", "url", unique=True),
        Index("idx_quelle_unternehmen", "unternehmen_id"),
    )

    def __repr__(self):
        return f"<ComQuelle {self.url[:50]}>"


# ============ Vertriebsstruktur (Manufacturer Distribution) ============


class ComVertriebsstruktur(Base):
    """
    Manufacturer-centric distribution channel.

    Describes how a manufacturer's products can be sourced:
    "MGA products are available through Zapf Creation (recommended for DACH)."

    Distinct from ComLieferbeziehung which is dealer-centric:
    "Dealer X buys from Supplier Y."
    """
    __tablename__ = "com_vertriebsstruktur"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    hersteller_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    lieferant_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    rolle = Column(String(30), nullable=False)  # "tochtergesellschaft", "hauptlieferant", "grosshaendler", "importeur", "direktvertrieb"
    region = Column(String(10))  # "DACH", "DE", "EU"
    ist_empfohlen = Column(Boolean, default=False)
    empfehlung_text = Column(Text)  # Free-text recommendation reason
    sortierung = Column(Integer, default=0)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hersteller = relationship(
        "ComUnternehmen",
        foreign_keys=[hersteller_id],
        back_populates="vertriebskanaele",
    )
    lieferant = relationship("ComUnternehmen", foreign_keys=[lieferant_id])

    __table_args__ = (
        Index(
            "uq_vertrieb_hersteller_lieferant_region",
            "hersteller_id", "lieferant_id", "region",
            unique=True,
        ),
        Index("idx_vertrieb_hersteller", "hersteller_id"),
        Index("idx_vertrieb_lieferant", "lieferant_id"),
    )
