"""
Pydantic Schemas for System Settings.
"""
from pydantic import BaseModel, ConfigDict


class SystemSettingResponse(BaseModel):
    """Response schema for a system setting.

    For secret settings (ist_geheim=True), value is masked.
    """
    key: str
    value: str
    beschreibung: str | None = None
    ist_geheim: bool = False

    model_config = ConfigDict(from_attributes=True)


class SystemSettingRevealResponse(BaseModel):
    """Response for revealing a secret setting value."""
    key: str
    value: str


class SystemSettingUpdate(BaseModel):
    """Schema for updating a system setting value."""
    value: str


class SystemSettingList(BaseModel):
    """List of system settings."""
    items: list[SystemSettingResponse]
