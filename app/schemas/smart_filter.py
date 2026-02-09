"""
Pydantic Schemas for Smart Filter management.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SmartFilterCreate(BaseModel):
    """Schema for creating a new smart filter."""
    name: str = Field(..., min_length=1, max_length=100, description="Filter name")
    beschreibung: str | None = Field(None, description="Optional description")
    entity_type: str = Field("unternehmen", description="Target entity type")
    dsl_expression: str = Field(..., min_length=1, description="Filter DSL expression")


class SmartFilterUpdate(BaseModel):
    """Schema for updating a smart filter (partial update)."""
    name: str | None = Field(None, min_length=1, max_length=100)
    beschreibung: str | None = None
    dsl_expression: str | None = Field(None, min_length=1)


class SmartFilterResponse(BaseModel):
    """Schema for smart filter response."""
    id: str
    name: str
    beschreibung: str | None
    entity_type: str
    dsl_expression: str
    erstellt_am: datetime | None
    aktualisiert_am: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SmartFilterList(BaseModel):
    """List of smart filters."""
    items: list[SmartFilterResponse]
    total: int


class SmartFilterValidateRequest(BaseModel):
    """Schema for validating a DSL expression."""
    dsl_expression: str = Field(..., min_length=1, description="DSL expression to validate")
    entity_type: str = Field("unternehmen", description="Target entity type for validation")


class SmartFilterValidateResponse(BaseModel):
    """Schema for validation result."""
    valid: bool
    error: str | None = None
    count: int | None = Field(None, description="Number of matching records (only if valid)")
