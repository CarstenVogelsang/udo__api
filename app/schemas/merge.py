"""
Pydantic Schemas for ETL Merge Configuration API.
"""
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def _parse_json_field(v: Any) -> Any:
    """Parse a JSON string into a Python object if needed."""
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, TypeError):
            return None
    return v


# ============ MergeJoin Schemas ============

class EtlMergeJoinRead(BaseModel):
    """A single join step in a merge config."""
    id: str
    file_role: str
    join_type: str = "left"
    join_col_left: str
    join_col_right: str
    columns_include: list[str] | None = None
    column_renames: dict[str, str] | None = None
    deduplicate: bool = True
    sortierung: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("columns_include", "column_renames", mode="before")
    @classmethod
    def parse_json(cls, v: Any) -> Any:
        return _parse_json_field(v)


class EtlMergeJoinCreate(BaseModel):
    """Create a new join step."""
    file_role: str
    join_type: str = "left"
    join_col_left: str
    join_col_right: str
    columns_include: list[str] | None = None
    column_renames: dict[str, str] | None = None
    deduplicate: bool = True
    sortierung: int = 0


class EtlMergeJoinUpdate(BaseModel):
    """Update a join step (partial)."""
    file_role: str | None = None
    join_type: str | None = None
    join_col_left: str | None = None
    join_col_right: str | None = None
    columns_include: list[str] | None = None
    column_renames: dict[str, str] | None = None
    deduplicate: bool | None = None
    sortierung: int | None = None


# ============ MergeConfig Schemas ============

class EtlMergeConfigRead(BaseModel):
    """Merge config with all join steps."""
    id: str
    source_id: str
    name: str
    beschreibung: str | None = None
    primary_file_role: str = "hauptdatei"
    output_renames: dict[str, str] | None = None
    output_drop_cols: list[str] | None = None
    erstellt_am: datetime | None = None
    aktualisiert_am: datetime | None = None
    joins: list[EtlMergeJoinRead] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("output_renames", "output_drop_cols", mode="before")
    @classmethod
    def parse_json(cls, v: Any) -> Any:
        return _parse_json_field(v)


class EtlMergeConfigCreate(BaseModel):
    """Create a new merge config."""
    source_id: str
    name: str
    beschreibung: str | None = None
    primary_file_role: str = "hauptdatei"
    output_renames: dict[str, str] | None = None
    output_drop_cols: list[str] | None = None


class EtlMergeConfigUpdate(BaseModel):
    """Update a merge config (partial)."""
    name: str | None = None
    beschreibung: str | None = None
    primary_file_role: str | None = None
    output_renames: dict[str, str] | None = None
    output_drop_cols: list[str] | None = None


# ============ Preview / Execute Response ============

class MergePreviewResponse(BaseModel):
    """Preview result of a merge operation."""
    headers: list[str]
    rows: list[dict]
    total_rows: int
    total_cols: int
    join_stats: list[dict] = []  # Per-join statistics


class MergeExecuteResponse(BaseModel):
    """Result of executing a merge."""
    import_file_id: str
    original_filename: str
    total_rows: int
    total_cols: int
    join_stats: list[dict] = []
