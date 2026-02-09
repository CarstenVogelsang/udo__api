"""
SQLAlchemy Model for System Settings.

Key-Value store for application-level configuration.
"""
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime

from app.models.geo import Base


class SystemSetting(Base):
    """Key-value store for application settings."""
    __tablename__ = "system_setting"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    beschreibung = Column(Text, nullable=True)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SystemSetting {self.key}={self.value}>"
