"""
Pydantic Schemas for System Settings.
"""
from pydantic import BaseModel, ConfigDict


class SystemSettingResponse(BaseModel):
    """Response schema for a system setting."""
    key: str
    value: str
    beschreibung: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SystemSettingUpdate(BaseModel):
    """Schema for updating a system setting value."""
    value: str


class SystemSettingList(BaseModel):
    """List of system settings."""
    items: list[SystemSettingResponse]
