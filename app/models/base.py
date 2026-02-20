"""
SQLAlchemy Models for Base/Utility tables.

Prefix: bas_ (base)
"""
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Index, UniqueConstraint

from app.models.geo import Base, UUID, generate_uuid


class BasStatus(Base):
    """
    Universal status lookup table with context support.

    Each status belongs to a context (e.g. 'unternehmen', 'kontakt', 'projekt')
    so different entities can have different valid status values.

    UNIQUE(code, kontext) ensures no duplicate codes within a context.
    """
    __tablename__ = "bas_status"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(30), nullable=False, index=True)  # "aktiv", "geschlossen"
    name = Column(String(100), nullable=False)  # "Aktiv", "Geschlossen"
    kontext = Column(String(50), nullable=False, index=True)  # "unternehmen", "kontakt"
    icon = Column(String(50))  # Tabler icon name: "circle-check", "circle-x"
    farbe = Column(String(20))  # DaisyUI color: "success", "error", "warning"
    sortierung = Column(Integer, default=0)  # Display order
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("code", "kontext", name="uq_status_code_kontext"),
    )

    def __repr__(self) -> str:
        return f"<BasStatus {self.kontext}.{self.code}: {self.name}>"


class BasSprache(Base):
    """
    Language lookup table (ISO 639-1).

    Used as FK reference for company communication language.
    Seeded with: de, en, fr, it, nl.
    """
    __tablename__ = "bas_sprache"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(5), unique=True, nullable=False, index=True)  # ISO 639-1: "de", "en"
    name = Column(String(100), nullable=False)  # "Deutsch", "Englisch"
    name_eng = Column(String(100))  # "German", "English"
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BasSprache {self.code}: {self.name}>"


class BasBewertungsplattform(Base):
    """
    Rating platform lookup table (Google, Yelp, TripAdvisor, etc.).

    Used as FK reference for company ratings (com_unternehmen_bewertung).
    Seeded with: google, yelp, tripadvisor, trustpilot, kununu.
    """
    __tablename__ = "bas_bewertungsplattform"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(30), unique=True, nullable=False, index=True)  # "google", "yelp"
    name = Column(String(100), nullable=False)  # "Google Maps", "Yelp"
    website = Column(String(255))  # "https://maps.google.com"
    icon = Column(String(50))  # Tabler icon name: "brand-google"
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BasBewertungsplattform {self.code}: {self.name}>"


class BasRechtsform(Base):
    """
    Legal form reference table with country association.

    Each legal form belongs to a specific country (or is international).
    Examples: GmbH (DE), Inc. (US), Ltd. (GB), SA (FR/ES)
    """
    __tablename__ = "bas_rechtsform"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(30), unique=True, nullable=False, index=True)  # "gmbh", "inc", "ltd"
    name = Column(String(100), nullable=False)  # "GmbH", "Inc.", "Ltd."
    name_lang = Column(String(200))  # "Gesellschaft mit beschränkter Haftung"
    land_code = Column(String(5))  # ISO 3166-1 alpha-2: "DE", "US", None=international
    ist_favorit = Column(Boolean, default=False)
    sortierung = Column(Integer, default=0)
    ist_aktiv = Column(Boolean, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_rechtsform_land", "land_code"),
    )

    def __repr__(self) -> str:
        return f"<BasRechtsform {self.code}: {self.name} ({self.land_code})>"


class BasMedienLizenz(Base):
    """
    Media license reference table.

    Categorizes license types for images, logos, and other media.
    Enables filtering: "show images without license" or "problematic licenses".

    kategorie values:
    - "frei": Free use (PD, CC0, CC-BY)
    - "eingeschraenkt": Usable with conditions (CC-BY-SA, CC-BY-NC)
    - "geschuetzt": Trademark/Copyright, use only with permission
    """
    __tablename__ = "bas_medien_lizenz"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)  # "pd_textlogo", "cc_by_4"
    name = Column(String(100), nullable=False)  # "PD-textlogo", "CC BY 4.0"
    beschreibung = Column(Text)  # "Public Domain — reine Textlogos ohne Schöpfungshöhe"
    kategorie = Column(String(30), nullable=False)  # "frei", "eingeschraenkt", "geschuetzt"
    url = Column(String(500))  # Link to license text
    ist_aktiv = Column(Boolean, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_medien_lizenz_kategorie", "kategorie"),
    )

    def __repr__(self) -> str:
        return f"<BasMedienLizenz {self.code}: {self.name} ({self.kategorie})>"


class BasColorPalette(Base):
    """
    Predefined color palette with 8 semantic colors (DaisyUI convention).

    Used for theming geo locations based on their coat of arms colors.

    Colors follow the DaisyUI semantic naming convention:
    - primary: Main brand color (buttons, links, accents)
    - secondary: Supporting brand color
    - accent: Highlight color for special elements
    - neutral: Text and background tones
    - info: Informational messages (blue tones)
    - success: Success states (green tones)
    - warning: Warning states (yellow/orange tones)
    - error: Error states (red tones)
    """
    __tablename__ = "bas_color_palette"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)

    # 8 semantic colors (HEX format: #RRGGBB)
    primary = Column(String(7), nullable=False)
    secondary = Column(String(7), nullable=False)
    accent = Column(String(7), nullable=False)
    neutral = Column(String(7), nullable=False)
    info = Column(String(7), nullable=False)
    success = Column(String(7), nullable=False)
    warning = Column(String(7), nullable=False)
    error = Column(String(7), nullable=False)

    # Metadata
    is_default = Column(Boolean, default=False)
    category = Column(String(20))  # "warm", "cool", "neutral", "vibrant"

    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BasColorPalette {self.slug}: {self.name}>"

    def to_dict(self) -> dict:
        """Return palette colors as dictionary."""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "neutral": self.neutral,
            "info": self.info,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
        }
