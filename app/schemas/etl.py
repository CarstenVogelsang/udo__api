"""
Pydantic Schemas for ETL (Extract-Transform-Load) API.

Provides schemas for:
- EtlSource: Data source configuration
- EtlTableMapping: Source → Target table mapping
- EtlFieldMapping: Field-level mapping with transformations
- EtlImportLog: Import run logs
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ============ EtlSource Schemas ============

class EtlSourceBase(BaseModel):
    """Base schema for EtlSource."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    connection_type: str = Field(..., min_length=1, max_length=20)
    connection_string: str | None = Field(None, max_length=500)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class EtlSourceCreate(EtlSourceBase):
    """Schema for creating an EtlSource."""
    pass


class EtlSourceUpdate(BaseModel):
    """Schema for updating an EtlSource."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    connection_type: str | None = Field(None, min_length=1, max_length=20)
    connection_string: str | None = Field(None, max_length=500)
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class EtlSourceResponse(EtlSourceBase):
    """Response schema for EtlSource."""
    id: str
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class EtlSourceWithMappings(EtlSourceResponse):
    """EtlSource with nested table mappings."""
    table_mappings: list["EtlTableMappingResponse"] = []


# ============ EtlTableMapping Schemas ============

class EtlTableMappingBase(BaseModel):
    """Base schema for EtlTableMapping."""
    source_table: str = Field(..., min_length=1, max_length=100)
    source_pk_field: str = Field(..., min_length=1, max_length=100)
    target_table: str = Field(..., min_length=1, max_length=100)
    target_pk_field: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class EtlTableMappingCreate(EtlTableMappingBase):
    """Schema for creating an EtlTableMapping."""
    source_id: str


class EtlTableMappingUpdate(BaseModel):
    """Schema for updating an EtlTableMapping."""
    source_table: str | None = Field(None, min_length=1, max_length=100)
    source_pk_field: str | None = Field(None, min_length=1, max_length=100)
    target_table: str | None = Field(None, min_length=1, max_length=100)
    target_pk_field: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class EtlTableMappingResponse(EtlTableMappingBase):
    """Response schema for EtlTableMapping."""
    id: str
    source_id: str
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


class EtlTableMappingWithFields(EtlTableMappingResponse):
    """EtlTableMapping with nested field mappings."""
    field_mappings: list["EtlFieldMappingResponse"] = []


class EtlTableMappingFull(EtlTableMappingWithFields):
    """EtlTableMapping with source and field mappings."""
    source: EtlSourceResponse | None = None


# ============ EtlFieldMapping Schemas ============

class EtlFieldMappingBase(BaseModel):
    """Base schema for EtlFieldMapping."""
    source_field: str = Field(..., min_length=1, max_length=100)
    target_field: str = Field(..., min_length=1, max_length=100)
    transform: str | None = Field(None, max_length=100)
    is_required: bool = False
    default_value: str | None = Field(None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class EtlFieldMappingCreate(EtlFieldMappingBase):
    """Schema for creating an EtlFieldMapping."""
    table_mapping_id: str


class EtlFieldMappingUpdate(BaseModel):
    """Schema for updating an EtlFieldMapping."""
    source_field: str | None = Field(None, min_length=1, max_length=100)
    target_field: str | None = Field(None, min_length=1, max_length=100)
    transform: str | None = Field(None, max_length=100)
    is_required: bool | None = None
    default_value: str | None = Field(None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class EtlFieldMappingResponse(EtlFieldMappingBase):
    """Response schema for EtlFieldMapping."""
    id: str
    table_mapping_id: str
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None


# ============ EtlImportLog Schemas ============

class EtlImportLogBase(BaseModel):
    """Base schema for EtlImportLog."""
    status: str
    records_read: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class EtlImportLogResponse(EtlImportLogBase):
    """Response schema for EtlImportLog."""
    id: str
    table_mapping_id: str
    started_at: datetime | None = None
    finished_at: datetime | None = None


class EtlImportLogWithMapping(EtlImportLogResponse):
    """EtlImportLog with table mapping info."""
    table_mapping: EtlTableMappingResponse | None = None


# ============ List Response Schemas ============

class EtlSourceList(BaseModel):
    """Paginated list of EtlSources."""
    items: list[EtlSourceResponse]
    total: int


class EtlTableMappingList(BaseModel):
    """Paginated list of EtlTableMappings."""
    items: list[EtlTableMappingResponse]
    total: int


class EtlFieldMappingList(BaseModel):
    """Paginated list of EtlFieldMappings."""
    items: list[EtlFieldMappingResponse]
    total: int


class EtlImportLogList(BaseModel):
    """Paginated list of EtlImportLogs."""
    items: list[EtlImportLogResponse]
    total: int


# ============ Trigger Import Schema ============

class EtlImportTrigger(BaseModel):
    """Schema for triggering an ETL import."""
    source_name: str = Field(..., description="Name der EtlSource")
    source_table: str = Field(..., description="Quell-Tabelle (z.B. spi_tStore)")
    dry_run: bool = Field(False, description="Testlauf ohne Schreiben")


class EtlImportResult(BaseModel):
    """Result of an ETL import run."""
    success: bool
    import_log_id: str | None = None
    records_read: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_message: str | None = None


# Forward reference updates
EtlSourceWithMappings.model_rebuild()
EtlTableMappingFull.model_rebuild()
