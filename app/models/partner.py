"""
SQLAlchemy Model for API Partners (authentication).

Partners access the API via API-Key (X-API-Key header).
Roles: "partner" (limited access) | "superadmin" (full access)
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Float, Boolean, DateTime, Index

from app.models.geo import Base, UUID, generate_uuid


class ApiPartner(Base):
    """API Partner with authentication credentials."""
    __tablename__ = "api_partner"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    api_key_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="partner")  # "partner" | "superadmin"
    kosten_geoapi_pro_einwohner = Column(Float, nullable=False, default=0.0001)  # Cost per inhabitant for GeoAPI queries
    is_active = Column(Boolean, nullable=False, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_partner_role", "role"),
        Index("idx_partner_active", "is_active"),
    )

    def __repr__(self):
        return f"<ApiPartner {self.name} ({self.role})>"
