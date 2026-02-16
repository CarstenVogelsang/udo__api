"""
Pydantic Schemas for ETL (Extract-Transform-Load) API.

Provides schemas for:
- EtlSource: Data source configuration
- EtlTableMapping: Source → Target table mapping
- EtlFieldMapping: Field-level mapping with transformations
- EtlImportLog: Import run logs
"""
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============ EtlSource Schemas ============

class EtlSourceBase(BaseModel):
    """Base schema for EtlSource."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    titel: str | None = Field(None, max_length=200)
    verantwortlicher: str | None = Field(None, max_length=200)
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
    titel: str | None = Field(None, max_length=200)
    verantwortlicher: str | None = Field(None, max_length=200)
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
    drawflow_layout: str | None = None
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
    source_field_aliases: list[str] | None = None
    target_field: str = Field(..., min_length=1, max_length=100)
    transform: str | None = Field(None, max_length=100)
    is_required: bool = False
    default_value: str | None = Field(None, max_length=255)
    update_rule: str = Field("always", max_length=20)  # "always", "if_empty", "never"

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
    update_rule: str | None = Field(None, max_length=20)

    model_config = ConfigDict(from_attributes=True)


class EtlFieldMappingResponse(EtlFieldMappingBase):
    """Response schema for EtlFieldMapping."""
    id: str
    table_mapping_id: str
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None

    @field_validator("source_field_aliases", mode="before")
    @classmethod
    def parse_aliases(cls, v: Any) -> list[str] | None:
        if isinstance(v, str):
            return json.loads(v)
        return v


# ============ EtlImportLog Schemas ============

class EtlImportLogBase(BaseModel):
    """Base schema for EtlImportLog."""
    status: str
    records_read: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    records_skipped: int = 0
    batch_id: str | None = None
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
    items: list[EtlImportLogWithMapping]
    total: int


# ============ Import Record Tracking Schemas ============

class EtlImportRecordResponse(BaseModel):
    """Response schema for EtlImportRecord."""
    id: str
    batch_id: str
    entity_type: str
    entity_id: str
    action: str
    erstellt_am: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EtlImportRecordList(BaseModel):
    """List of import records for a batch."""
    items: list[EtlImportRecordResponse]
    total: int
    batch_id: str


class EtlImportRollbackResult(BaseModel):
    """Result of a batch rollback operation."""
    batch_id: str
    rolled_back: int
    skipped: int
    details: list[str] = []


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


# ============ Excel Import Schemas ============

class ExcelImportResult(BaseModel):
    """Result of an Excel import run."""
    batch_id: str
    rows_read: int = 0
    unternehmen_created: int = 0
    unternehmen_updated: int = 0
    unternehmen_skipped: int = 0
    kontakte_created: int = 0
    kontakte_updated: int = 0
    kontakte_skipped: int = 0
    errors: int = 0
    error_details: list[str] = []
    dry_run: bool = False


class ExcelSourcePreview(BaseModel):
    """Preview of configured column mappings for an Excel import source."""
    source_name: str
    description: str | None = None
    unternehmen_mappings: list[EtlFieldMappingResponse] = []
    kontakt_mappings: list[EtlFieldMappingResponse] = []


# ============ Bulk Field Mapping Schemas ============

class BulkFieldMappingItem(BaseModel):
    """Single field mapping in a bulk operation."""
    source_field: str = Field(..., min_length=1, max_length=100)
    source_field_aliases: list[str] | None = None
    target_field: str = Field(..., min_length=1, max_length=100)
    transform: str | None = Field(None, max_length=100)
    is_required: bool = False
    default_value: str | None = Field(None, max_length=255)
    update_rule: str = Field("always", max_length=20)


class BulkFieldMappingPayload(BaseModel):
    """Payload for bulk-replacing all field mappings of a table mapping."""
    field_mappings: list[BulkFieldMappingItem]
    drawflow_layout: dict | None = None


class BulkFieldMappingResponse(BaseModel):
    """Response after bulk field mapping replace."""
    table_mapping_id: str
    field_mappings_count: int
    field_mappings: list[EtlFieldMappingResponse]


# ============ Schema Discovery Schemas ============

class TableColumnInfo(BaseModel):
    """Column metadata for schema discovery."""
    name: str
    type: str
    nullable: bool
    is_pk: bool


class TableSchemaResponse(BaseModel):
    """Schema of a target table for the visual mapping editor."""
    table_name: str
    columns: list[TableColumnInfo]


# ============ Import File Schemas ============

class EtlImportFileResponse(BaseModel):
    """Response schema for EtlImportFile."""
    id: str
    source_id: str | None = None
    original_filename: str
    stored_filename: str
    file_size: int
    content_type: str | None = None
    status: str
    headers: list[str] | None = None
    row_count: int | None = None
    analysis_result: list[dict[str, Any]] | None = None
    uploaded_by: str | None = None
    notizen: str | None = None
    file_role: str | None = None
    is_merged_output: bool | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("headers", mode="before")
    @classmethod
    def parse_headers(cls, v: Any) -> list[str] | None:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("analysis_result", mode="before")
    @classmethod
    def parse_analysis_result(cls, v: Any) -> list[dict[str, Any]] | None:
        if isinstance(v, str):
            return json.loads(v)
        return v


class EtlImportFileList(BaseModel):
    """Paginated list of EtlImportFiles."""
    items: list[EtlImportFileResponse]
    total: int


class EtlImportFileAssign(BaseModel):
    """Payload for assigning a file to a source."""
    source_id: str


class EtlImportFileRowsResponse(BaseModel):
    """Paginated rows from an import file."""
    file_id: str
    headers: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    offset: int
    limit: int


# ============ Field Alias Schemas ============

class FieldAliasUpdate(BaseModel):
    """Payload for adding/removing source field aliases."""
    add: list[str] = []
    remove: list[str] = []


# ============ Compatibility Report Schemas ============

class FieldSuggestion(BaseModel):
    """Fuzzy match suggestion for a missing field."""
    header: str
    similarity: float
    normalized_similarity: float | None = None


class FieldCompatibility(BaseModel):
    """Single field compatibility entry."""
    field_mapping_id: str
    source_field: str
    target_field: str
    status: str  # "matched" | "matched_by_alias" | "missing"
    matched_header: str | None = None
    aliases: list[str] = []
    is_required: bool = False
    suggestions: list[FieldSuggestion] = []


class UnmappedHeader(BaseModel):
    """File header that has no field mapping."""
    header: str
    suggestions: list[dict[str, Any]] = []


class CompatibilityReport(BaseModel):
    """Full compatibility report between file and source."""
    file_id: str
    source_id: str
    source_name: str
    total_fields: int
    matched_count: int
    matched_by_alias_count: int
    missing_count: int
    unmapped_count: int
    coverage: float
    fields: list[FieldCompatibility]
    unmapped_headers: list[UnmappedHeader]


# Forward reference updates
EtlSourceWithMappings.model_rebuild()
EtlTableMappingFull.model_rebuild()
