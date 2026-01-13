"""
Pydantic Schemas for API Partner management.

Partners are API consumers with API-Key authentication.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class ApiPartnerCreate(BaseModel):
    """Schema for creating a new partner."""
    name: str = Field(..., min_length=2, max_length=100, description="Partner name")
    email: EmailStr | None = Field(None, description="Contact email")
    role: str = Field("partner", pattern="^(partner|superadmin)$", description="Role: partner or superadmin")
    kosten_geoapi_pro_einwohner: float = Field(0.0001, ge=0, description="Cost per inhabitant for GeoAPI queries")
    kosten_unternehmen_pro_abfrage: float = Field(0.001, ge=0, description="Cost per company query")
    zugelassene_laender_ids: list[str] | None = Field(None, description="Allowed country UUIDs (empty/null = all)")


class ApiPartnerUpdate(BaseModel):
    """Schema for updating a partner (partial update)."""
    name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None
    role: str | None = Field(None, pattern="^(partner|superadmin)$")
    kosten_geoapi_pro_einwohner: float | None = Field(None, ge=0)
    kosten_unternehmen_pro_abfrage: float | None = Field(None, ge=0)
    zugelassene_laender_ids: list[str] | None = None
    is_active: bool | None = None


class ApiPartnerResponse(BaseModel):
    """Schema for partner response (without sensitive data)."""
    id: str
    name: str
    email: str | None
    role: str
    kosten_geoapi_pro_einwohner: float
    kosten_unternehmen_pro_abfrage: float
    zugelassene_laender_ids: list[str] | None
    is_active: bool
    erstellt_am: datetime | None
    aktualisiert_am: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ApiPartnerWithKey(ApiPartnerResponse):
    """
    Schema for partner response with API key.
    Only returned once during partner creation!
    """
    api_key: str = Field(..., description="API Key (shown only once!)")


class ApiPartnerList(BaseModel):
    """List of partners."""
    items: list[ApiPartnerResponse]
    total: int
