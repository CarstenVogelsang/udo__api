"""
SQLAlchemy Model for Smart Filters.

Smart Filters store reusable DSL filter expressions that can be applied
to entity list queries (e.g. Unternehmen, Kontakte).
"""
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Boolean, Index

from app.models.geo import Base, UUID, generate_uuid


class SmartFilter(Base):
    """
    Saved filter with DSL expression.

    Each filter targets a specific entity type and stores its query
    as a DSL expression that gets parsed and translated to SQLAlchemy
    conditions at query time.
    """
    __tablename__ = "smart_filter"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    beschreibung = Column(Text)
    entity_type = Column(String(50), nullable=False, default="unternehmen")
    dsl_expression = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_smart_filter_entity_type", "entity_type"),
    )

    def __repr__(self):
        return f"<SmartFilter {self.name} ({self.entity_type})>"
