"""
SQLAlchemy Models for Company (Unternehmen) data.

Provides business entity data with geographic references.
Table prefix: com_ (analog zu geo_ für Geodaten)
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
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
    sprache_id = Column(UUID, ForeignKey("bas_sprache.id"), nullable=True)
    geo_ort_id = Column(UUID, ForeignKey("geo_ort.id"), nullable=True)  # kGeoOrt → GeoOrt
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    geloescht_am = Column(DateTime, nullable=True)  # Soft delete timestamp

    # Relationship to Status
    status = relationship("BasStatus", lazy="joined")
    # Relationship to GeoOrt - provides full geo hierarchy
    geo_ort = relationship("GeoOrt", lazy="joined")
    # Relationship to language
    sprache = relationship("BasSprache", lazy="joined")

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

    __table_args__ = (
        Index("idx_unternehmen_geo_ort", "geo_ort_id"),
        Index("idx_unternehmen_kurzname", "kurzname"),
        Index("idx_unternehmen_legacy", "legacy_id"),
        Index("idx_unternehmen_sprache", "sprache_id"),
        Index("idx_unternehmen_status", "status_id"),
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
