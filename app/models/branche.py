"""
SQLAlchemy Models for Branchenklassifikation (WZ-2008).

Provides industry classification data with mappings to:
- Business directories (Verzeichnisse)
- Regional social media groups (Gruppen)
- Google Business Categories (Google-Kategorien)

Table prefix: brn_*
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.geo import Base, UUID, generate_uuid


# ============ Enums ============


class BrnAnmeldeArt(str, PyEnum):
    """Registration method for a business directory."""
    ONLINE_FORMULAR = "online_formular"
    API = "api"
    MANUELL = "manuell"
    PARTNER_DIENST = "partner_dienst"


class BrnKostenModell(str, PyEnum):
    """Pricing model for a business directory."""
    KOSTENLOS = "kostenlos"
    FREEMIUM = "freemium"
    KOSTENPFLICHTIG = "kostenpflichtig"


class BrnGruppenPlattform(str, PyEnum):
    """Social media platform for regional groups."""
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    XING = "xing"
    NEXTDOOR = "nextdoor"
    SONSTIGE = "sonstige"


# ============ Models ============


class BrnBranche(Base):
    """WZ-2008 industry classification (Wirtschaftszweige).

    Hierarchical structure with 5 levels:
    1 = Abschnitt (e.g. "C" = Verarbeitendes Gewerbe)
    2 = Abteilung (e.g. "43")
    3 = Gruppe (e.g. "43.2")
    4 = Klasse (e.g. "43.21")
    5 = Unterklasse (e.g. "43.21.0")
    """
    __tablename__ = "brn_branche"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    wz_code = Column(String(10), unique=True, nullable=False, index=True)
    bezeichnung = Column(String(200), nullable=False)
    ebene = Column(Integer, nullable=False)
    parent_wz_code = Column(String(10), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Children
    verzeichnisse = relationship("BrnVerzeichnis", back_populates="branche", lazy="selectin")
    gruppen = relationship("BrnRegionaleGruppe", back_populates="branche", lazy="selectin")
    google_mappings = relationship("BrnGoogleMapping", back_populates="branche", lazy="selectin")

    def __repr__(self):
        return f"<BrnBranche {self.wz_code}: {self.bezeichnung}>"


class BrnVerzeichnis(Base):
    """Business directory entry (Branchenverzeichnis).

    Can be industry-specific (linked to a BrnBranche via wz_code)
    or cross-industry (ist_branchenuebergreifend=True, no wz_code).
    """
    __tablename__ = "brn_verzeichnis"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    beschreibung = Column(Text, nullable=True)
    branche_wz_code = Column(String(10), ForeignKey("brn_branche.wz_code"), nullable=True)
    ist_branchenuebergreifend = Column(Boolean, default=False)
    hat_api = Column(Boolean, default=False)
    api_dokumentation_url = Column(String(500), nullable=True)
    anmeldeart = Column(SAEnum(BrnAnmeldeArt), nullable=False)
    anmelde_url = Column(String(500), nullable=True)
    kosten = Column(SAEnum(BrnKostenModell), nullable=False)
    kosten_details = Column(String(200), nullable=True)
    relevanz_score = Column(Integer, default=5)
    regionen = Column(JSON, default=list)
    anleitung_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    zuletzt_geprueft = Column(Date, nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Parent
    branche = relationship("BrnBranche", back_populates="verzeichnisse", lazy="joined")

    __table_args__ = (
        Index("idx_verzeichnis_branche", "branche_wz_code"),
    )

    def __repr__(self):
        return f"<BrnVerzeichnis {self.name}>"


class BrnRegionaleGruppe(Base):
    """Regional social media group for local marketing.

    Groups on Facebook, LinkedIn, Xing, etc. where businesses
    can promote their services in a specific region/industry.
    """
    __tablename__ = "brn_regionale_gruppe"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    plattform = Column(SAEnum(BrnGruppenPlattform), nullable=False)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    beschreibung = Column(Text, nullable=True)
    branche_wz_code = Column(String(10), ForeignKey("brn_branche.wz_code"), nullable=True)
    region_plz_prefix = Column(String(5), nullable=True)
    region_name = Column(String(100), nullable=True)
    region_bundesland = Column(String(50), nullable=True)
    mitglieder_anzahl = Column(Integer, nullable=True)
    werbung_erlaubt = Column(Boolean, default=False)
    posting_regeln = Column(Text, nullable=True)
    empfohlene_posting_art = Column(String(100), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    zuletzt_geprueft = Column(Date, nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Parent
    branche = relationship("BrnBranche", back_populates="gruppen", lazy="joined")

    __table_args__ = (
        Index("idx_gruppe_branche", "branche_wz_code"),
        Index("idx_gruppe_plattform", "plattform"),
        Index("idx_gruppe_bundesland", "region_bundesland"),
    )

    def __repr__(self):
        return f"<BrnRegionaleGruppe {self.plattform.value}: {self.name}>"


class BrnGoogleKategorie(Base):
    """Google Business Profile category.

    Stores the Google Category ID (gcid) with German and English names.
    Used for mapping WZ codes to Google categories via BrnGoogleMapping.
    """
    __tablename__ = "brn_google_kategorie"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    gcid = Column(String(100), unique=True, nullable=False, index=True)
    name_de = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=False)
    ist_aktiv = Column(Boolean, default=True)
    zuletzt_aktualisiert = Column(DateTime, default=datetime.utcnow)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Children
    mappings = relationship("BrnGoogleMapping", back_populates="google_kategorie", lazy="selectin")

    def __repr__(self):
        return f"<BrnGoogleKategorie {self.gcid}: {self.name_de}>"


class BrnGoogleMapping(Base):
    """M:N mapping between WZ codes and Google Business categories.

    Each WZ code can map to multiple Google categories, one of which
    is marked as primary (ist_primaer=True).
    """
    __tablename__ = "brn_google_mapping"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    wz_code = Column(String(10), ForeignKey("brn_branche.wz_code"), nullable=False, index=True)
    gcid = Column(String(100), ForeignKey("brn_google_kategorie.gcid"), nullable=False, index=True)
    ist_primaer = Column(Boolean, default=False)
    relevanz = Column(Integer, default=5)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # Parents
    branche = relationship("BrnBranche", back_populates="google_mappings", lazy="joined")
    google_kategorie = relationship("BrnGoogleKategorie", back_populates="mappings", lazy="joined")

    __table_args__ = (
        UniqueConstraint("wz_code", "gcid", name="uq_brn_google_mapping"),
    )

    def __repr__(self):
        return f"<BrnGoogleMapping {self.wz_code} → {self.gcid}>"
