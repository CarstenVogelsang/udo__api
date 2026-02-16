"""
SQLAlchemy Models for Product (Produktdaten) data.

EAV architecture with Sortiment-Blueprints:
- prod_artikel: Core article fields (all products)
- prod_sortiment: Product category types (Moba, Sammler, Glaskeramik, ...)
- prod_eigenschaft: Property definitions (Spurweite, Epoche, Material, ...)
- prod_sortiment_eigenschaft: Blueprint — which properties belong to which sortiment
- prod_artikel_sortiment: N:M — article belongs to sortiment(s)
- prod_artikel_eigenschaft: Concrete property values (EAV)
- prod_kategorie: Hierarchical catalog categories
- prod_artikel_bild: Media/images
- prod_werteliste: Controlled vocabularies

Table prefix: prod_
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.geo import Base, UUID, generate_uuid


# ── Controlled Vocabularies ──────────────────────────────────────────


class ProdWerteliste(Base):
    """Controlled vocabulary entries (Spurweite, Epoche, Artikelstatus, Bildart, ...)."""
    __tablename__ = "prod_werteliste"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    typ = Column(String(50), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    bezeichnung = Column(String(100), nullable=False)
    sortierung = Column(Integer, default=0)
    ist_aktiv = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("typ", "code", name="uq_werteliste_typ_code"),
        Index("idx_werteliste_typ", "typ"),
    )

    def __repr__(self):
        return f"<ProdWerteliste {self.typ}:{self.code}>"


# ── Sortiment & Eigenschaft (Blueprint System) ──────────────────────


class ProdSortiment(Base):
    """Product sortiment definition (Moba, Sammler, Glaskeramik, ...)."""
    __tablename__ = "prod_sortiment"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    beschreibung = Column(Text, nullable=True)
    sortierung = Column(Integer, default=0)

    # Relationships
    eigenschaft_zuordnungen = relationship(
        "ProdSortimentEigenschaft",
        back_populates="sortiment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ProdSortiment {self.code}>"


class ProdEigenschaft(Base):
    """Property definition (Spurweite, Epoche, Material, ...).

    daten_typ determines which value column is used in ProdArtikelEigenschaft:
    - 'text' / 'werteliste' → wert_text
    - 'ganzzahl' → wert_ganzzahl
    - 'dezimal' → wert_dezimal
    - 'bool' → wert_bool

    When daten_typ='werteliste', werteliste_typ points to ProdWerteliste.typ
    for validation during import.
    """
    __tablename__ = "prod_eigenschaft"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    daten_typ = Column(String(20), nullable=False)  # text, ganzzahl, dezimal, bool, werteliste
    werteliste_typ = Column(String(50), nullable=True)  # → ProdWerteliste.typ
    einheit = Column(String(20), nullable=True)  # mm, g, Monate
    ist_pflicht = Column(Boolean, default=False)
    sortierung = Column(Integer, default=0)

    # Relationships
    sortiment_zuordnungen = relationship(
        "ProdSortimentEigenschaft",
        back_populates="eigenschaft",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<ProdEigenschaft {self.code} ({self.daten_typ})>"


class ProdSortimentEigenschaft(Base):
    """Blueprint: which properties belong to which sortiment."""
    __tablename__ = "prod_sortiment_eigenschaft"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    sortiment_id = Column(UUID, ForeignKey("prod_sortiment.id", ondelete="CASCADE"), nullable=False)
    eigenschaft_id = Column(UUID, ForeignKey("prod_eigenschaft.id", ondelete="CASCADE"), nullable=False)
    ist_pflicht = Column(Boolean, nullable=True)  # Override per sortiment (NULL = use eigenschaft default)
    sortierung = Column(Integer, default=0)

    # Relationships
    sortiment = relationship("ProdSortiment", back_populates="eigenschaft_zuordnungen")
    eigenschaft = relationship("ProdEigenschaft", back_populates="sortiment_zuordnungen", lazy="joined")

    __table_args__ = (
        UniqueConstraint("sortiment_id", "eigenschaft_id", name="uq_sortiment_eigenschaft"),
        Index("idx_se_sortiment", "sortiment_id"),
        Index("idx_se_eigenschaft", "eigenschaft_id"),
    )

    def __repr__(self):
        return f"<ProdSortimentEigenschaft sortiment={self.sortiment_id} eigenschaft={self.eigenschaft_id}>"


# ── Kategorie (Catalog Hierarchy) ───────────────────────────────────


class ProdKategorie(Base):
    """Hierarchical product category (Google Product Taxonomy based).

    Separate from Sortiment:
    - Kategorie = "where in the catalog?" (tree, 1 path per article)
    - Sortiment = "which properties apply?" (N:M tag, multiple per article)
    """
    __tablename__ = "prod_kategorie"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    parent_id = Column(UUID, ForeignKey("prod_kategorie.id"), nullable=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    ebene = Column(Integer, nullable=False, default=1)
    sortierung = Column(Integer, default=0)
    ist_aktiv = Column(Boolean, default=True)

    # Self-referential relationship
    parent = relationship("ProdKategorie", remote_side="ProdKategorie.id", backref="children")

    __table_args__ = (
        Index("idx_kategorie_parent", "parent_id"),
        Index("idx_kategorie_ebene", "ebene"),
    )

    def __repr__(self):
        return f"<ProdKategorie {self.code}: {self.name}>"


# ── Artikel (Core Product) ──────────────────────────────────────────


class ProdArtikel(Base):
    """Core product article — sortiment-independent fields.

    Sortiment-specific properties are stored in ProdArtikelEigenschaft (EAV).
    """
    __tablename__ = "prod_artikel"

    id = Column(UUID, primary_key=True, default=generate_uuid)

    # FK to existing com_* tables
    hersteller_id = Column(UUID, ForeignKey("com_unternehmen.id"), nullable=False)
    marke_id = Column(UUID, ForeignKey("com_marke.id"), nullable=False)
    serie_id = Column(UUID, ForeignKey("com_serie.id"), nullable=True)
    kategorie_id = Column(UUID, ForeignKey("prod_kategorie.id"), nullable=True)

    # Grunddaten
    artikelnummer_hersteller = Column(String(30), nullable=False)
    ean_gtin = Column(String(14), nullable=True, index=True)
    artikelstatus = Column(String(10), nullable=False, default="NEU")
    bezeichnung = Column(String(250), nullable=False)
    bezeichnung_b2c = Column(String(250), nullable=True)
    beschreibung = Column(Text, nullable=True)
    beschreibung_b2c = Column(Text, nullable=True)
    ursprungsland = Column(String(2), nullable=True)
    zolltarifnummer = Column(String(11), nullable=True)

    # Preise
    listenpreis_netto = Column(Float, nullable=True)
    uvp_brutto = Column(Float, nullable=True)
    einkaufspreis_netto = Column(Float, nullable=True)  # GNP/Grosshandelspreis
    mwst_satz = Column(Float, nullable=True)
    waehrung = Column(String(3), nullable=False, default="EUR")
    verpackungseinheit = Column(Integer, nullable=True)  # VE (Stueck pro VE)
    rabattfaehig = Column(Boolean, nullable=True)
    verfuegbarkeit = Column(String(20), nullable=True)
    erstlieferdatum = Column(Date, nullable=True)
    neuheit_jahr = Column(Integer, nullable=True)

    # PAngV (Preisangabenverordnung — Grundpreispflicht)
    pangv_einheit = Column(String(10), nullable=True)   # m, qm, kg, l
    pangv_inhalt = Column(Float, nullable=True)          # Produktinhalt/-menge
    pangv_grundmenge = Column(Float, nullable=True)      # Referenzmenge (meist 1)

    # Logistik
    gewicht_netto_g = Column(Integer, nullable=True)
    gewicht_brutto_g = Column(Integer, nullable=True)
    verpackung_laenge_mm = Column(Integer, nullable=True)
    verpackung_breite_mm = Column(Integer, nullable=True)
    verpackung_hoehe_mm = Column(Integer, nullable=True)
    mindestbestellmenge = Column(Integer, nullable=True)

    # Compliance
    ce_kennzeichen = Column(Boolean, default=False)
    altersfreigabe_min = Column(Integer, nullable=True)
    warnhinweise = Column(Text, nullable=True)
    sicherheitssymbol = Column(String(20), nullable=True)  # symbol-1, symbol-2, symbol-3
    gpsr_bevollmaechtigter_id = Column(
        UUID, ForeignKey("com_unternehmen.id"), nullable=True
    )  # EU authorized representative (GPSR)

    # Meta
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    geloescht_am = Column(DateTime, nullable=True)

    # Relationships — FK targets
    hersteller = relationship("ComUnternehmen", foreign_keys=[hersteller_id], lazy="joined")
    marke = relationship("ComMarke", lazy="joined")
    serie = relationship("ComSerie", lazy="joined")
    kategorie = relationship("ProdKategorie", lazy="joined")
    gpsr_bevollmaechtigter = relationship(
        "ComUnternehmen", foreign_keys=[gpsr_bevollmaechtigter_id], lazy="joined"
    )

    # Relationships — children
    sortiment_zuordnungen = relationship(
        "ProdArtikelSortiment",
        back_populates="artikel",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    eigenschaft_werte = relationship(
        "ProdArtikelEigenschaft",
        back_populates="artikel",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    bilder = relationship(
        "ProdArtikelBild",
        back_populates="artikel",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    texte = relationship(
        "ProdArtikelText",
        back_populates="artikel",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("hersteller_id", "artikelnummer_hersteller", name="uq_artikel_hersteller_nr"),
        Index("idx_artikel_hersteller", "hersteller_id"),
        Index("idx_artikel_marke", "marke_id"),
        Index("idx_artikel_ean", "ean_gtin"),
        Index("idx_artikel_status", "artikelstatus"),
        Index("idx_artikel_kategorie", "kategorie_id"),
    )

    @property
    def sortimente(self) -> list:
        """Returns list of associated Sortimente."""
        return [z.sortiment for z in self.sortiment_zuordnungen]

    def __repr__(self):
        return f"<ProdArtikel {self.artikelnummer_hersteller}: {self.bezeichnung}>"


# ── Artikel ↔ Sortiment (N:M) ───────────────────────────────────────


class ProdArtikelSortiment(Base):
    """N:M junction — article belongs to sortiment(s)."""
    __tablename__ = "prod_artikel_sortiment"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    artikel_id = Column(UUID, ForeignKey("prod_artikel.id", ondelete="CASCADE"), nullable=False)
    sortiment_id = Column(UUID, ForeignKey("prod_sortiment.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    artikel = relationship("ProdArtikel", back_populates="sortiment_zuordnungen")
    sortiment = relationship("ProdSortiment", lazy="joined")

    __table_args__ = (
        UniqueConstraint("artikel_id", "sortiment_id", name="uq_artikel_sortiment"),
        Index("idx_as_artikel", "artikel_id"),
        Index("idx_as_sortiment", "sortiment_id"),
    )

    def __repr__(self):
        return f"<ProdArtikelSortiment artikel={self.artikel_id} sortiment={self.sortiment_id}>"


# ── Artikel ↔ Eigenschaft (EAV Values) ──────────────────────────────


class ProdArtikelEigenschaft(Base):
    """Concrete property value for an article (EAV pattern).

    Polymorphic value storage — only ONE value column is filled,
    determined by the eigenschaft's daten_typ:
    - 'text' / 'werteliste' → wert_text (for werteliste: stores the code, e.g. 'H0')
    - 'ganzzahl' → wert_ganzzahl
    - 'dezimal' → wert_dezimal
    - 'bool' → wert_bool
    """
    __tablename__ = "prod_artikel_eigenschaft"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    artikel_id = Column(UUID, ForeignKey("prod_artikel.id", ondelete="CASCADE"), nullable=False)
    eigenschaft_id = Column(UUID, ForeignKey("prod_eigenschaft.id", ondelete="CASCADE"), nullable=False)

    # Polymorphic value columns
    wert_text = Column(String(500), nullable=True)
    wert_ganzzahl = Column(Integer, nullable=True)
    wert_dezimal = Column(Float, nullable=True)
    wert_bool = Column(Boolean, nullable=True)

    # Relationships
    artikel = relationship("ProdArtikel", back_populates="eigenschaft_werte")
    eigenschaft = relationship("ProdEigenschaft", lazy="joined")

    __table_args__ = (
        UniqueConstraint("artikel_id", "eigenschaft_id", name="uq_artikel_eigenschaft"),
        Index("idx_ae_artikel", "artikel_id"),
        Index("idx_ae_eigenschaft", "eigenschaft_id"),
        Index("idx_ae_wert_text", "wert_text"),
    )

    @property
    def wert(self):
        """Returns the active value based on eigenschaft's daten_typ."""
        dt = self.eigenschaft.daten_typ if self.eigenschaft else None
        if dt in ("text", "werteliste"):
            return self.wert_text
        elif dt == "ganzzahl":
            return self.wert_ganzzahl
        elif dt == "dezimal":
            return self.wert_dezimal
        elif dt == "bool":
            return self.wert_bool
        return self.wert_text  # fallback

    def __repr__(self):
        return f"<ProdArtikelEigenschaft artikel={self.artikel_id} eigenschaft={self.eigenschaft_id}>"


# ── Artikel Bilder (Media) ──────────────────────────────────────────


class ProdArtikelBild(Base):
    """Product image/media with typed classification (bildart from Werteliste)."""
    __tablename__ = "prod_artikel_bild"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    artikel_id = Column(UUID, ForeignKey("prod_artikel.id", ondelete="CASCADE"), nullable=False)
    bildart = Column(String(20), nullable=False)  # Kurzcode from ProdWerteliste typ='bildart'
    dateiname = Column(String(200), nullable=True)
    url = Column(String(500), nullable=False)
    alt_text = Column(String(200), nullable=True)
    sortierung = Column(Integer, default=0)

    # Relationships
    artikel = relationship("ProdArtikel", back_populates="bilder")

    __table_args__ = (
        Index("idx_bild_artikel", "artikel_id"),
    )

    def __repr__(self):
        return f"<ProdArtikelBild {self.bildart}: {self.dateiname or self.url}>"


# ── Artikel Texte (i18n) ──────────────────────────────────────────


class ProdArtikelText(Base):
    """Translated product texts (i18n).

    Separate table for multilingual texts — scales to any number of languages
    without schema changes. The primary language (typically German) stays in
    ProdArtikel.bezeichnung/beschreibung for fast access without JOINs.
    """
    __tablename__ = "prod_artikel_text"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    artikel_id = Column(UUID, ForeignKey("prod_artikel.id", ondelete="CASCADE"), nullable=False)
    sprache = Column(String(5), nullable=False)  # ISO 639-1: de, en, fr, it, nl, ...
    bezeichnung = Column(String(250), nullable=True)
    beschreibung = Column(Text, nullable=True)

    # Relationships
    artikel = relationship("ProdArtikel", back_populates="texte")

    __table_args__ = (
        UniqueConstraint("artikel_id", "sprache", name="uq_artikel_text_sprache"),
        Index("idx_artikel_text_artikel_sprache", "artikel_id", "sprache"),
    )

    def __repr__(self):
        return f"<ProdArtikelText {self.sprache}: {self.bezeichnung or '(no title)'}>"
