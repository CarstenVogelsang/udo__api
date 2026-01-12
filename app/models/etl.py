"""
SQLAlchemy Models for ETL (Extract-Transform-Load) configuration.

Provides a generic, configurable import framework:
- EtlSource: Data sources (MS SQL, MySQL, CSV, etc.)
- EtlTableMapping: Source table → Target table mapping
- EtlFieldMapping: Source field → Target field with optional transformation

Table prefix: etl_
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.geo import Base, UUID, generate_uuid


class EtlSource(Base):
    """
    Data source configuration for ETL imports.

    Examples:
    - toyware_mssql: Legacy MS SQL Server database
    - customer_csv: CSV file import
    """
    __tablename__ = "etl_source"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    connection_type = Column(String(20), nullable=False)  # mssql, mysql, postgres, csv
    connection_string = Column(String(500))  # Can be "env:MSSQL_*" for env reference
    is_active = Column(Boolean, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Children
    table_mappings = relationship(
        "EtlTableMapping",
        back_populates="source",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<EtlSource {self.name} ({self.connection_type})>"


class EtlTableMapping(Base):
    """
    Maps a source table to a target table.

    One source table can map to multiple target tables (1:N).
    Example: spi_tStore → com_unternehmen
    """
    __tablename__ = "etl_table_mapping"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    source_id = Column(UUID, ForeignKey("etl_source.id"), nullable=False)
    source_table = Column(String(100), nullable=False)  # e.g., "spi_tStore"
    source_pk_field = Column(String(100), nullable=False)  # e.g., "kStore"
    target_table = Column(String(100), nullable=False)  # e.g., "com_unternehmen"
    target_pk_field = Column(String(100), nullable=False)  # e.g., "legacy_id"
    is_active = Column(Boolean, default=True)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Parent
    source = relationship("EtlSource", back_populates="table_mappings", lazy="joined")

    # Children
    field_mappings = relationship(
        "EtlFieldMapping",
        back_populates="table_mapping",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_table_mapping_source", "source_id"),
        Index("idx_table_mapping_tables", "source_table", "target_table"),
    )

    def __repr__(self):
        return f"<EtlTableMapping {self.source_table} → {self.target_table}>"


class EtlFieldMapping(Base):
    """
    Maps a source field to a target field with optional transformation.

    Transformations are simple function names from a registry:
    - "trim": Strip whitespace
    - "upper": Convert to uppercase
    - "lower": Convert to lowercase
    - "to_int": Convert to integer
    - "to_date": Parse as date
    - "fk_lookup:table.field": Foreign key lookup
    """
    __tablename__ = "etl_field_mapping"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    table_mapping_id = Column(UUID, ForeignKey("etl_table_mapping.id"), nullable=False)
    source_field = Column(String(100), nullable=False)  # e.g., "cKurzname"
    target_field = Column(String(100), nullable=False)  # e.g., "kurzname"
    transform = Column(String(100))  # e.g., "trim", "fk_lookup:geo_ort.legacy_id"
    is_required = Column(Boolean, default=False)
    default_value = Column(String(255))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Parent
    table_mapping = relationship("EtlTableMapping", back_populates="field_mappings", lazy="joined")

    __table_args__ = (
        Index("idx_field_mapping_table", "table_mapping_id"),
    )

    def __repr__(self):
        transform_str = f" [{self.transform}]" if self.transform else ""
        return f"<EtlFieldMapping {self.source_field} → {self.target_field}{transform_str}>"


class EtlImportLog(Base):
    """
    Logs ETL import runs for auditing and debugging.
    """
    __tablename__ = "etl_import_log"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    table_mapping_id = Column(UUID, ForeignKey("etl_table_mapping.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    status = Column(String(20), default="running")  # running, success, failed
    records_read = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text)

    # Parent
    table_mapping = relationship("EtlTableMapping", lazy="joined")

    __table_args__ = (
        Index("idx_import_log_table", "table_mapping_id"),
        Index("idx_import_log_started", "started_at"),
    )

    def __repr__(self):
        return f"<EtlImportLog {self.status} ({self.records_created}+{self.records_updated})>"
