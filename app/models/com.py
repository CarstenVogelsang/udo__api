"""
SQLAlchemy Models for Company (Unternehmen) data.

Provides business entity data with geographic references.
Table prefix: com_ (analog zu geo_ für Geodaten)
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.models.geo import Base, UUID, generate_uuid


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
    status_datum = Column(DateTime)  # dStatusUnternehmen
    kurzname = Column(String(100), index=True)  # cKurzname
    firmierung = Column(String(255))  # cFirmierung
    strasse = Column(String(255))  # cStrasse
    strasse_hausnr = Column(String(50))  # cStrasseHausNr
    geo_ort_id = Column(UUID, ForeignKey("geo_ort.id"), nullable=True)  # kGeoOrt → GeoOrt
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to GeoOrt - provides full geo hierarchy
    # Using lazy="joined" for eager loading in single query
    geo_ort = relationship("GeoOrt", lazy="joined")

    __table_args__ = (
        Index("idx_unternehmen_geo_ort", "geo_ort_id"),
        Index("idx_unternehmen_kurzname", "kurzname"),
        Index("idx_unternehmen_legacy", "legacy_id"),
    )

    def __repr__(self):
        return f"<ComUnternehmen {self.kurzname or self.firmierung}>"
