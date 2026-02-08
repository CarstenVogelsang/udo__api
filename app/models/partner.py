"""
SQLAlchemy Model for API Partners (authentication).

Partners access the API via API-Key (X-API-Key header).
Roles: "partner" (limited access) | "superadmin" (full access)
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Index, JSON

from app.models.geo import Base, UUID, generate_uuid


class ApiPartner(Base):
    """API Partner with authentication credentials."""
    __tablename__ = "api_partner"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    api_key_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    password_hash = Column(String(128), nullable=True)  # bcrypt hash for JWT login
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, unique=True, index=True)  # Made unique for login
    role = Column(String(20), nullable=False, default="partner")  # "partner" | "superadmin"
    kosten_geoapi_pro_einwohner = Column(Float, nullable=False, default=0.0001)  # Cost per inhabitant for GeoAPI queries
    kosten_unternehmen_pro_abfrage = Column(Float, nullable=False, default=0.001)  # Cost per company query (0.1 Cent)
    zugelassene_laender_ids = Column(JSON, nullable=True, default=list)  # List of allowed country UUIDs (empty = all)
    rate_limit_pro_minute = Column(Integer, nullable=False, default=60)
    rate_limit_pro_stunde = Column(Integer, nullable=False, default=1000)
    rate_limit_pro_tag = Column(Integer, nullable=False, default=10000)
    is_active = Column(Boolean, nullable=False, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_partner_role", "role"),
        Index("idx_partner_active", "is_active"),
    )

    def __repr__(self):
        return f"<ApiPartner {self.name} ({self.role})>"
