"""
SQLAlchemy Models for Base/Utility tables.

Prefix: bas_ (base)
"""
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime

from app.models.geo import Base, UUID, generate_uuid


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
