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

    __table_args__ = (
        Index("idx_unternehmen_geo_ort", "geo_ort_id"),
        Index("idx_unternehmen_kurzname", "kurzname"),
        Index("idx_unternehmen_legacy", "legacy_id"),
    )

    def __repr__(self):
        return f"<ComUnternehmen {self.kurzname or self.firmierung}>"
