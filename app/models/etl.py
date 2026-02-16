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

    Serves as "project" for import workflows:
    - toyware_mssql: Legacy MS SQL Server database
    - maerklin_haendler: Excel-based dealer import
    """
    __tablename__ = "etl_source"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    titel = Column(String(200))  # Human-readable project title
    verantwortlicher = Column(String(200))  # Responsible person
    connection_type = Column(String(20), nullable=False)  # mssql, mysql, postgres, csv, excel
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
    import_files = relationship(
        "EtlImportFile",
        back_populates="source",
        lazy="selectin",
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
    drawflow_layout = Column(Text, nullable=True)  # JSON: Drawflow visual editor state
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
    source_field_aliases = Column(Text, nullable=True)  # JSON: ["Straße", "STRASSE"]
    target_field = Column(String(100), nullable=False)  # e.g., "kurzname"
    transform = Column(String(100))  # e.g., "trim", "fk_lookup:geo_ort.legacy_id"
    is_required = Column(Boolean, default=False)
    default_value = Column(String(255))
    update_rule = Column(String(20), default="always")  # "always", "if_empty", "never"
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


class EtlImportRecord(Base):
    """
    Tracks individual records created/updated by an import.

    Enables per-record auditing and soft-delete rollback:
    - Which batch created/updated which entity?
    - Rollback: set geloescht_am on all "created" entities of a batch.
    """
    __tablename__ = "etl_import_record"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    batch_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)    # "unternehmen", "kontakt", "junction"
    entity_id = Column(UUID, nullable=False)
    action = Column(String(20), nullable=False)         # "created", "updated"
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_import_record_entity", "entity_type", "entity_id"),
        Index("idx_import_record_batch", "batch_id", "entity_type"),
    )

    def __repr__(self):
        return f"<EtlImportRecord {self.action} {self.entity_type}:{self.entity_id}>"


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
    records_skipped = Column(Integer, default=0)
    batch_id = Column(String(36), index=True)  # Groups logs from one import run
    error_message = Column(Text)

    # Parent
    table_mapping = relationship("EtlTableMapping", lazy="joined")

    __table_args__ = (
        Index("idx_import_log_table", "table_mapping_id"),
        Index("idx_import_log_started", "started_at"),
    )

    def __repr__(self):
        return f"<EtlImportLog {self.status} ({self.records_created}+{self.records_updated})>"


class EtlImportFile(Base):
    """
    Persistent import file metadata.

    Tracks uploaded Excel files, their analysis results (header matching),
    and assignment to an EtlSource project. Actual file stored on disk at
    {upload_dir}/etl/{source_id|unassigned}/{stored_filename}.
    """
    __tablename__ = "etl_import_file"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    source_id = Column(UUID, ForeignKey("etl_source.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(100), nullable=False)  # UUID-based
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(200), default="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    status = Column(String(20), nullable=False, default="pending")  # pending, analyzed, assigned, error
    headers = Column(Text)  # JSON-serialized list of column headers
    row_count = Column(Integer)
    analysis_result = Column(Text)  # JSON: match scores per source
    uploaded_by = Column(String(200))
    notizen = Column(Text)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Parent
    source = relationship("EtlSource", back_populates="import_files", lazy="joined")

    __table_args__ = (
        Index("idx_import_file_source", "source_id"),
        Index("idx_import_file_status", "status"),
        Index("idx_import_file_created", "erstellt_am"),
    )

    # Merge integration
    file_role = Column(String(50), nullable=True)  # Role in merge config (e.g., "hauptdatei")
    merge_config_id = Column(UUID, ForeignKey("etl_merge_config.id", ondelete="SET NULL"), nullable=True)
    is_merged_output = Column(Boolean, default=False)  # True if produced by merge

    # Merge config (optional)
    merge_config = relationship("EtlMergeConfig", foreign_keys=[merge_config_id])

    @property
    def file_content(self) -> bytes | None:
        """Read file bytes from disk storage."""
        import os
        from app.config import get_settings
        settings = get_settings()
        source_dir = str(self.source_id) if self.source_id else "unassigned"
        path = os.path.join(settings.upload_dir, "etl", source_dir, self.stored_filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    def __repr__(self):
        return f"<EtlImportFile {self.original_filename} ({self.status})>"


class EtlMergeConfig(Base):
    """
    Persistent merge configuration for combining multiple source files.

    One EtlSource can have one merge config that defines how multiple
    uploaded files are joined together before ETL import.
    """
    __tablename__ = "etl_merge_config"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    source_id = Column(UUID, ForeignKey("etl_source.id", ondelete="CASCADE"), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    beschreibung = Column(Text, nullable=True)
    primary_file_role = Column(String(50), nullable=False, default="hauptdatei")
    output_renames = Column(Text, nullable=True)  # JSON: {"old_name": "new_name", ...}
    output_drop_cols = Column(Text, nullable=True)  # JSON: ["col1", "col2", ...]
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    aktualisiert_am = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("EtlSource", lazy="joined")
    joins = relationship(
        "EtlMergeJoin",
        back_populates="merge_config",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="EtlMergeJoin.sortierung",
    )

    def __repr__(self):
        return f"<EtlMergeConfig {self.name}>"


class EtlMergeJoin(Base):
    """
    A single join step in a merge configuration.

    Each join combines the running result (starting from primary file)
    with one additional file via a shared key column.
    """
    __tablename__ = "etl_merge_join"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    merge_config_id = Column(UUID, ForeignKey("etl_merge_config.id", ondelete="CASCADE"), nullable=False)
    file_role = Column(String(50), nullable=False)  # e.g., "haendlerpreise"
    join_type = Column(String(10), nullable=False, default="left")  # left, inner, right
    join_col_left = Column(String(100), nullable=False)  # Column in primary/result
    join_col_right = Column(String(100), nullable=False)  # Column in this file
    columns_include = Column(Text, nullable=True)  # JSON: ["GNP", "VE"] (null = all new)
    column_renames = Column(Text, nullable=True)  # JSON: {"NUMMER": "Artikel"}
    deduplicate = Column(Boolean, default=True)  # Remove duplicates on join key
    sortierung = Column(Integer, nullable=False, default=0)

    # Parent
    merge_config = relationship("EtlMergeConfig", back_populates="joins")

    __table_args__ = (
        Index("idx_merge_join_config", "merge_config_id"),
    )

    def __repr__(self):
        return f"<EtlMergeJoin {self.file_role}: {self.join_col_left}={self.join_col_right}>"
