"""
SQLAlchemy Model for System Settings.

Key-Value store for application-level configuration.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, String, Text, DateTime

from app.models.geo import Base


class SystemSetting(Base):
    """Key-value store for application settings."""
    __tablename__ = "system_setting"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    beschreibung = Column(Text, nullable=True)
    ist_geheim = Column(Boolean, nullable=False, default=False)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        masked = "***" if self.ist_geheim else self.value
        return f"<SystemSetting {self.key}={masked}>"
