"""
SQLAlchemy Models for Geodata.

Hierarchie: Land → Bundesland → Regierungsbezirk → Kreis → Ort → Ortsteil

Primary Key: UUID (für Synchronisation)
Business Keys: AGS/ISO-Code + hierarchischer Code (automatisch generiert)
"""
from datetime import datetime
from uuid import uuid4
import uuid as uuid_module

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    event,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.sqlite import BLOB

# SQLite doesn't have native UUID, so we use String(36)
UUID = String(36)

Base = declarative_base()


def generate_uuid() -> str:
    """Generates a new UUID string."""
    return str(uuid4())


class GeoLand(Base):
    """Countries (top level)."""
    __tablename__ = "geo_land"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    ags = Column(String(5), unique=True, nullable=False, index=True)  # ISO 3166-1 alpha-2: "DE"
    code = Column(String(10), unique=True, nullable=False, index=True)  # Same as AGS for countries
    name = Column(String(255), nullable=False)
    name_eng = Column(String(255))
    name_fra = Column(String(255))
    iso3 = Column(String(3))  # ISO 3166-1 alpha-3: "DEU"
    kontinent = Column(String(100))
    ist_eu = Column(Boolean, default=False)
    landesvorwahl = Column(String(20))
    legacy_id = Column(String(10))  # Original kLand_ISO from legacy DB
    color_palette_id = Column(UUID, ForeignKey("bas_color_palette.id"), nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Color palette for theming
    color_palette = relationship("BasColorPalette", lazy="joined")
    # Children
    bundeslaender = relationship(
        "GeoBundesland",
        back_populates="land",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    @property
    def primary_color(self) -> str | None:
        """Returns primary color from linked palette."""
        return self.color_palette.primary if self.color_palette else None

    @property
    def secondary_color(self) -> str | None:
        """Returns secondary color from linked palette."""
        return self.color_palette.secondary if self.color_palette else None

    def __repr__(self):
        return f"<GeoLand {self.code}: {self.name}>"


class GeoBundesland(Base):
    """Federal states (Bundesländer)."""
    __tablename__ = "geo_bundesland"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    ags = Column(String(10), nullable=False, index=True)  # e.g. "09" for Bayern (not unique across countries!)
    code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. "DE-BY" (unique!)
    kuerzel = Column(String(10), index=True)  # e.g. "BY", "NW"
    name = Column(String(255), nullable=False)
    einwohner = Column(Integer)
    einwohner_stand = Column(DateTime)
    land_id = Column(UUID, ForeignKey("geo_land.id"), nullable=False)
    legacy_id = Column(Integer)  # Original kBundesland from legacy DB
    color_palette_id = Column(UUID, ForeignKey("bas_color_palette.id"), nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Color palette for theming
    color_palette = relationship("BasColorPalette", lazy="joined")
    # Parent
    land = relationship("GeoLand", back_populates="bundeslaender", lazy="joined")
    # Children
    regierungsbezirke = relationship(
        "GeoRegierungsbezirk",
        back_populates="bundesland",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    kreise = relationship(
        "GeoKreis",
        back_populates="bundesland",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_bundesland_land", "land_id"),
    )

    @property
    def primary_color(self) -> str | None:
        """Returns primary color from linked palette."""
        return self.color_palette.primary if self.color_palette else None

    @property
    def secondary_color(self) -> str | None:
        """Returns secondary color from linked palette."""
        return self.color_palette.secondary if self.color_palette else None

    def __repr__(self):
        return f"<GeoBundesland {self.code}: {self.name}>"


class GeoRegierungsbezirk(Base):
    """Government districts (Regierungsbezirke) - optional level, not all states have them."""
    __tablename__ = "geo_regierungsbezirk"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    ags = Column(String(10), nullable=False, index=True)  # e.g. "091" for Oberbayern (not unique across countries!)
    code = Column(String(30), unique=True, nullable=False, index=True)  # e.g. "DE-BY-091" (unique!)
    name = Column(String(255), nullable=False)
    bundesland_id = Column(UUID, ForeignKey("geo_bundesland.id"), nullable=False)
    legacy_id = Column(Integer)  # Original kRegierungsbezirk from legacy DB
    color_palette_id = Column(UUID, ForeignKey("bas_color_palette.id"), nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Color palette for theming
    color_palette = relationship("BasColorPalette", lazy="joined")
    # Parent
    bundesland = relationship("GeoBundesland", back_populates="regierungsbezirke", lazy="joined")
    # Children
    kreise = relationship(
        "GeoKreis",
        back_populates="regierungsbezirk",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_regbez_bundesland", "bundesland_id"),
    )

    @property
    def primary_color(self) -> str | None:
        """Returns primary color from linked palette."""
        return self.color_palette.primary if self.color_palette else None

    @property
    def secondary_color(self) -> str | None:
        """Returns secondary color from linked palette."""
        return self.color_palette.secondary if self.color_palette else None

    def __repr__(self):
        return f"<GeoRegierungsbezirk {self.code}: {self.name}>"


class GeoKreis(Base):
    """Counties and independent cities (Landkreise und kreisfreie Städte)."""
    __tablename__ = "geo_kreis"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    ags = Column(String(20), nullable=False, index=True)  # e.g. "09162" (not unique across countries!)
    code = Column(String(60), unique=True, nullable=False, index=True)  # e.g. "DE-BY-09162-12345" (unique!)
    name = Column(String(255), nullable=False)
    typ = Column(String(50))  # "Landkreis", "Kreisfreie Stadt", etc.
    ist_landkreis = Column(Boolean)
    ist_kreisfreie_stadt = Column(Boolean)
    autokennzeichen = Column(String(10))
    kreissitz = Column(String(100))
    einwohner = Column(Integer)
    einwohner_stand = Column(DateTime)
    einwohner_pro_km2 = Column(Integer)
    flaeche_km2 = Column(Integer)
    beschreibung = Column(Text)
    wikipedia_url = Column(String(255))
    website_url = Column(String(255))
    bundesland_id = Column(UUID, ForeignKey("geo_bundesland.id"), nullable=False)
    regierungsbezirk_id = Column(UUID, ForeignKey("geo_regierungsbezirk.id"), nullable=True)  # Optional!
    legacy_id = Column(Integer)  # Original kKreis from legacy DB
    color_palette_id = Column(UUID, ForeignKey("bas_color_palette.id"), nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Color palette for theming
    color_palette = relationship("BasColorPalette", lazy="joined")
    # Parents
    bundesland = relationship("GeoBundesland", back_populates="kreise", lazy="joined")
    regierungsbezirk = relationship("GeoRegierungsbezirk", back_populates="kreise", lazy="joined")
    # Children
    orte = relationship(
        "GeoOrt",
        back_populates="kreis",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_kreis_bundesland", "bundesland_id"),
        Index("idx_kreis_regbez", "regierungsbezirk_id"),
        Index("idx_kreis_autokennzeichen", "autokennzeichen"),
    )

    @property
    def primary_color(self) -> str | None:
        """Returns primary color from linked palette."""
        return self.color_palette.primary if self.color_palette else None

    @property
    def secondary_color(self) -> str | None:
        """Returns secondary color from linked palette."""
        return self.color_palette.secondary if self.color_palette else None

    def __repr__(self):
        return f"<GeoKreis {self.code}: {self.name}>"


class GeoOrt(Base):
    """Cities and municipalities (Städte und Gemeinden)."""
    __tablename__ = "geo_ort"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    ags = Column(String(12), index=True)  # Gemeindeschlüssel, e.g. "09162000"
    code = Column(String(60), unique=True, nullable=False, index=True)  # e.g. "DE-BY-091-09162-München"
    name = Column(String(255), nullable=False)
    plz = Column(String(10), index=True)  # Main PLZ
    typ = Column(String(50))  # "Stadt", "Gemeinde", etc.
    ist_stadt = Column(Boolean)
    ist_gemeinde = Column(Boolean)
    ist_hauptort = Column(Boolean)  # Main location for PLZ
    lat = Column(Float)  # Latitude
    lng = Column(Float)  # Longitude
    einwohner = Column(Integer)
    einwohner_stand = Column(DateTime)
    einwohner_pro_km2 = Column(Integer)
    flaeche_km2 = Column(Float)
    beschreibung = Column(Text)
    wikipedia_url = Column(String(255))
    website_url = Column(String(255))
    kreis_id = Column(UUID, ForeignKey("geo_kreis.id"), nullable=False)
    legacy_id = Column(Integer)  # Original kGeoOrt from legacy DB
    color_palette_id = Column(UUID, ForeignKey("bas_color_palette.id"), nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Color palette for theming
    color_palette = relationship("BasColorPalette", lazy="joined")
    # Parent
    kreis = relationship("GeoKreis", back_populates="orte", lazy="joined")
    # Children
    ortsteile = relationship(
        "GeoOrtsteil",
        back_populates="ort",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_ort_kreis", "kreis_id"),
        Index("idx_ort_plz", "plz"),
        Index("idx_ort_name", "name"),
    )

    @property
    def primary_color(self) -> str | None:
        """Returns primary color from linked palette."""
        return self.color_palette.primary if self.color_palette else None

    @property
    def secondary_color(self) -> str | None:
        """Returns secondary color from linked palette."""
        return self.color_palette.secondary if self.color_palette else None

    def __repr__(self):
        return f"<GeoOrt {self.plz} {self.name}>"


class GeoOrtsteil(Base):
    """City districts (Ortsteile) - lowest level."""
    __tablename__ = "geo_ortsteil"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    ags = Column(String(20), index=True)  # If available
    code = Column(String(80), unique=True, nullable=False, index=True)  # Full hierarchical code
    name = Column(String(255), nullable=False)
    lat = Column(Float)
    lng = Column(Float)
    einwohner = Column(Integer)
    einwohner_stand = Column(DateTime)
    beschreibung = Column(Text)
    ort_id = Column(UUID, ForeignKey("geo_ort.id"), nullable=False)
    legacy_id = Column(Integer)  # Original kGeoOrtsteil from legacy DB
    color_palette_id = Column(UUID, ForeignKey("bas_color_palette.id"), nullable=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Color palette for theming
    color_palette = relationship("BasColorPalette", lazy="joined")
    # Parent
    ort = relationship("GeoOrt", back_populates="ortsteile", lazy="joined")

    __table_args__ = (
        Index("idx_ortsteil_ort", "ort_id"),
    )

    @property
    def primary_color(self) -> str | None:
        """Returns primary color from linked palette."""
        return self.color_palette.primary if self.color_palette else None

    @property
    def secondary_color(self) -> str | None:
        """Returns secondary color from linked palette."""
        return self.color_palette.secondary if self.color_palette else None

    def __repr__(self):
        return f"<GeoOrtsteil {self.name}>"
