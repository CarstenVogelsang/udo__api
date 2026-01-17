"""
SQLAlchemy Models for Plugin Marketplace.

Manages the plugin ecosystem for satellite projects including:
- Plugin registration and metadata
- Project types and pricing
- Licensing and subscriptions
- Audit trail for license changes

Table prefix: plg_ (analog zu geo_, com_, etl_)
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.models.geo import Base, UUID, generate_uuid


# =============================================================================
# Enums
# =============================================================================

class PlgPluginStatus(str, PyEnum):
    """Plugin lifecycle status."""
    ENTWICKLUNG = "entwicklung"  # In development, not in marketplace
    AKTIV = "aktiv"  # Available for licensing
    INAKTIV = "inaktiv"  # Temporarily disabled
    DEPRECATED = "deprecated"  # Deprecated, no new licenses


class PlgLizenzStatus(str, PyEnum):
    """License status values."""
    TESTPHASE = "testphase"  # Trial period
    AKTIV = "aktiv"  # Active subscription
    GEKUENDIGT = "gekuendigt"  # Cancelled but still valid until end date
    ABGELAUFEN = "abgelaufen"  # Expired
    PAUSIERT = "pausiert"  # Temporarily paused
    STORNIERT = "storniert"  # Cancelled immediately


class PlgPreisModell(str, PyEnum):
    """Pricing model types."""
    EINMALIG = "einmalig"  # One-time purchase
    MONATLICH = "monatlich"  # Monthly subscription
    JAEHRLICH = "jaehrlich"  # Yearly subscription
    NUTZUNGSBASIERT = "nutzungsbasiert"  # Pay-per-use (future)


# =============================================================================
# Models
# =============================================================================

class PlgKategorie(Base):
    """
    Plugin categories for organization in marketplace.

    Examples: "CRM", "ERP", "Marketing", "Analytics", "Integration"
    """
    __tablename__ = "plg_kategorie"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly
    name = Column(String(100), nullable=False)
    beschreibung = Column(Text)
    icon = Column(String(50))  # Tabler Icon class, e.g. "ti-puzzle"
    sortierung = Column(Integer, default=0)  # Order in UI
    ist_aktiv = Column(Boolean, default=True)

    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Children
    plugins = relationship("PlgPlugin", back_populates="kategorie", lazy="selectin")

    __table_args__ = (
        Index("idx_kategorie_sortierung", "sortierung"),
    )

    def __repr__(self):
        return f"<PlgKategorie {self.slug}: {self.name}>"


class PlgPlugin(Base):
    """
    Plugin master data.

    Initial data imported from plugin.json, then managed in DB.
    Backend is the single source of truth for plugin metadata.
    """
    __tablename__ = "plg_plugin"

    id = Column(UUID, primary_key=True, default=generate_uuid)

    # Identification
    slug = Column(String(100), unique=True, nullable=False, index=True)  # "crm-basic"
    name = Column(String(255), nullable=False)
    beschreibung = Column(Text)  # Full description (Markdown)
    beschreibung_kurz = Column(String(500))  # Short description for lists

    # Categorization
    kategorie_id = Column(UUID, ForeignKey("plg_kategorie.id"), nullable=True)
    tags = Column(JSON, default=list)  # ["reporting", "dashboard"]

    # Current version
    version = Column(String(20), nullable=False)  # Semantic versioning: "1.2.3"
    version_datum = Column(DateTime)  # Release date of current version

    # Status
    status = Column(
        String(20),
        nullable=False,
        default=PlgPluginStatus.ENTWICKLUNG.value
    )

    # Technical metadata
    dokumentation_url = Column(String(500))
    changelog_url = Column(String(500))
    repo_url = Column(String(500))  # Git repository
    min_api_version = Column(String(20))  # Minimum API version: "1.0.0"

    # Visual elements
    icon = Column(String(50))  # Tabler Icon
    thumbnail_url = Column(String(500))  # Screenshot/Preview

    # Import reference
    plugin_json_hash = Column(String(64))  # SHA-256 of original plugin.json

    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    kategorie = relationship("PlgKategorie", back_populates="plugins", lazy="joined")
    versionen = relationship(
        "PlgPluginVersion",
        back_populates="plugin",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    preise = relationship(
        "PlgPreis",
        back_populates="plugin",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    lizenzen = relationship(
        "PlgLizenz",
        back_populates="plugin",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_plugin_status", "status"),
        Index("idx_plugin_kategorie", "kategorie_id"),
    )

    def __repr__(self):
        return f"<PlgPlugin {self.slug}: {self.name} v{self.version}>"


class PlgPluginVersion(Base):
    """
    Plugin version history.

    Tracks all released versions with changelog.
    """
    __tablename__ = "plg_plugin_version"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    plugin_id = Column(UUID, ForeignKey("plg_plugin.id"), nullable=False)

    version = Column(String(20), nullable=False)  # "1.2.3"
    changelog = Column(Text)  # Markdown formatted
    ist_aktuell = Column(Boolean, default=False)  # Current version marker
    ist_breaking_change = Column(Boolean, default=False)  # Major version increment
    min_api_version = Column(String(20))  # If changed

    veroeffentlicht_am = Column(DateTime, default=datetime.utcnow)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Parent
    plugin = relationship("PlgPlugin", back_populates="versionen", lazy="joined")

    __table_args__ = (
        Index("idx_version_plugin", "plugin_id"),
        Index("idx_version_aktuell", "plugin_id", "ist_aktuell"),
        Index("uq_plugin_version", "plugin_id", "version", unique=True),
    )

    def __repr__(self):
        return f"<PlgPluginVersion {self.plugin_id}: v{self.version}>"


class PlgProjekttyp(Base):
    """
    Project type classification for satellite installations.

    Determines pricing tier and available features.

    Types:
    - business_directory: Branchenverzeichnisse (high volume)
    - einzelkunde: Normal websites (standard pricing)
    - city_server: City portals (volume discount)
    - intern: Internal projects (free)
    """
    __tablename__ = "plg_projekttyp"

    id = Column(UUID, primary_key=True, default=generate_uuid)

    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    beschreibung = Column(Text)

    # Properties
    ist_kostenlos = Column(Boolean, default=False)  # For internal projects
    ist_testphase_erlaubt = Column(Boolean, default=True)
    standard_testphase_tage = Column(Integer, default=30)  # Default trial duration

    # For future tiered pricing/metrics
    max_benutzer = Column(Integer, nullable=True)  # Soft limit
    max_api_calls_pro_monat = Column(Integer, nullable=True)  # Soft limit

    icon = Column(String(50))
    sortierung = Column(Integer, default=0)

    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Children
    projekte = relationship("PlgProjekt", back_populates="projekttyp", lazy="selectin")
    preise = relationship("PlgPreis", back_populates="projekttyp", lazy="selectin")

    __table_args__ = (
        Index("idx_projekttyp_sortierung", "sortierung"),
    )

    def __repr__(self):
        return f"<PlgProjekttyp {self.slug}: {self.name}>"


class PlgPreis(Base):
    """
    Pricing per plugin and project type.

    Allows different prices for the same plugin based on project type.
    Example: CRM-Basic costs 50 EUR/month for Einzelkunde,
             but 200 EUR/month for Business Directory.
    """
    __tablename__ = "plg_preis"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    plugin_id = Column(UUID, ForeignKey("plg_plugin.id"), nullable=False)
    projekttyp_id = Column(UUID, ForeignKey("plg_projekttyp.id"), nullable=False)

    # Pricing model
    modell = Column(String(20), nullable=False, default=PlgPreisModell.MONATLICH.value)

    # Base price
    preis = Column(Float, nullable=False)  # In EUR
    waehrung = Column(String(3), default="EUR")

    # Tiered pricing (for future use)
    staffel_ab_benutzer = Column(Integer, nullable=True)  # From X users
    staffel_preis = Column(Float, nullable=True)  # Reduced price

    # Usage-based pricing (for future use)
    preis_pro_api_call = Column(Float, nullable=True)
    preis_pro_datensatz = Column(Float, nullable=True)
    inkludierte_api_calls = Column(Integer, nullable=True)

    # Setup fee (optional)
    einrichtungsgebuehr = Column(Float, default=0.0)

    # Validity
    gueltig_ab = Column(DateTime, default=datetime.utcnow)
    gueltig_bis = Column(DateTime, nullable=True)  # NULL = unlimited
    ist_aktiv = Column(Boolean, default=True)

    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plugin = relationship("PlgPlugin", back_populates="preise", lazy="joined")
    projekttyp = relationship("PlgProjekttyp", back_populates="preise", lazy="joined")

    __table_args__ = (
        Index("idx_preis_plugin", "plugin_id"),
        Index("idx_preis_projekttyp", "projekttyp_id"),
        Index("idx_preis_aktiv", "ist_aktiv"),
    )

    def __repr__(self):
        return f"<PlgPreis {self.plugin_id}/{self.projekttyp_id}: {self.preis} {self.waehrung}>"


class PlgProjekt(Base):
    """
    Customer/tenant projects (satellite installations).

    Each satellite is a separate installation that can license plugins.
    Links to GeoOrt for geographic assignment (optional).
    """
    __tablename__ = "plg_projekt"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    projekttyp_id = Column(UUID, ForeignKey("plg_projekttyp.id"), nullable=False)

    # Identification
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    beschreibung = Column(Text)

    # Contact details
    kontakt_name = Column(String(255))
    kontakt_email = Column(String(255), index=True)
    kontakt_telefon = Column(String(50))

    # Technical data
    api_key_hash = Column(String(64), unique=True, index=True)  # SHA-256 for auth
    base_url = Column(String(500))  # URL of satellite installation

    # Geo reference (optional)
    geo_ort_id = Column(UUID, ForeignKey("geo_ort.id"), nullable=True)

    # Status
    ist_aktiv = Column(Boolean, default=True)
    aktiviert_am = Column(DateTime)
    deaktiviert_am = Column(DateTime, nullable=True)

    # Internal notes
    notizen = Column(Text)

    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projekttyp = relationship("PlgProjekttyp", back_populates="projekte", lazy="joined")
    geo_ort = relationship("GeoOrt", lazy="joined")
    lizenzen = relationship(
        "PlgLizenz",
        back_populates="projekt",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_projekt_typ", "projekttyp_id"),
        Index("idx_projekt_aktiv", "ist_aktiv"),
        Index("idx_projekt_geo", "geo_ort_id"),
    )

    def __repr__(self):
        return f"<PlgProjekt {self.slug}: {self.name}>"


class PlgLizenz(Base):
    """
    License/subscription linking projects to plugins.

    Tracks who licensed what plugin, when, and current status.
    Handles trial periods and subscription lifecycle.
    """
    __tablename__ = "plg_lizenz"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    projekt_id = Column(UUID, ForeignKey("plg_projekt.id"), nullable=False)
    plugin_id = Column(UUID, ForeignKey("plg_plugin.id"), nullable=False)
    preis_id = Column(UUID, ForeignKey("plg_preis.id"), nullable=True)  # Reference to price

    # License period
    lizenz_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    lizenz_ende = Column(DateTime, nullable=True)  # NULL = unlimited

    # Trial period
    ist_testphase = Column(Boolean, default=False)
    testphase_ende = Column(DateTime, nullable=True)
    testphase_konvertiert = Column(Boolean, default=False)  # Converted to full license

    # Status
    status = Column(String(20), nullable=False, default=PlgLizenzStatus.AKTIV.value)

    # Cancellation
    gekuendigt_am = Column(DateTime, nullable=True)
    kuendigung_grund = Column(Text, nullable=True)
    kuendigung_zum = Column(DateTime, nullable=True)  # Effective cancellation date

    # Price snapshot at licensing time
    preis_snapshot = Column(Float)
    preis_modell_snapshot = Column(String(20))

    # Plugin version at licensing
    plugin_version_bei_lizenzierung = Column(String(20))

    # Internal notes
    notizen = Column(Text)

    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projekt = relationship("PlgProjekt", back_populates="lizenzen", lazy="joined")
    plugin = relationship("PlgPlugin", back_populates="lizenzen", lazy="joined")
    preis = relationship("PlgPreis", lazy="joined")
    historie = relationship(
        "PlgLizenzHistorie",
        back_populates="lizenz",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PlgLizenzHistorie.erstellt_am.desc()"
    )

    __table_args__ = (
        Index("idx_lizenz_projekt", "projekt_id"),
        Index("idx_lizenz_plugin", "plugin_id"),
        Index("idx_lizenz_status", "status"),
        Index("idx_lizenz_testphase", "ist_testphase", "testphase_ende"),
    )

    def __repr__(self):
        return f"<PlgLizenz {self.projekt_id}/{self.plugin_id}: {self.status}>"


class PlgLizenzHistorie(Base):
    """
    Audit trail for license status changes.

    Records all status transitions for compliance and debugging.
    """
    __tablename__ = "plg_lizenz_historie"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    lizenz_id = Column(UUID, ForeignKey("plg_lizenz.id"), nullable=False)

    # Status change
    alter_status = Column(String(20))
    neuer_status = Column(String(20), nullable=False)

    # Metadata
    aenderungsgrund = Column(String(255))
    notizen = Column(Text)

    # Who made the change?
    geaendert_von = Column(UUID, nullable=True)  # User/Admin ID (if available)
    geaendert_von_typ = Column(String(20))  # "system", "admin", "api", "kunde"

    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Parent
    lizenz = relationship("PlgLizenz", back_populates="historie", lazy="joined")

    __table_args__ = (
        Index("idx_historie_lizenz", "lizenz_id"),
        Index("idx_historie_datum", "erstellt_am"),
    )

    def __repr__(self):
        return f"<PlgLizenzHistorie {self.lizenz_id}: {self.alter_status} -> {self.neuer_status}>"
