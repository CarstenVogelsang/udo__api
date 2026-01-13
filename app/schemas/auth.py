"""
Pydantic Schemas for JWT Authentication.

Defines request/response models for login, token refresh, and user info.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr = Field(..., description="Partner email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


class TokenResponse(BaseModel):
    """JWT token response after successful login."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(..., description="Valid refresh token")


class AccessTokenResponse(BaseModel):
    """New access token response."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class CurrentUser(BaseModel):
    """Current authenticated user info."""
    id: str
    name: str
    email: str | None
    role: str
    is_active: bool
    erstellt_am: datetime | None
    aktualisiert_am: datetime | None

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class SetPasswordRequest(BaseModel):
    """Set password for partner without password (first-time setup)."""
    password: str = Field(..., min_length=8, description="New password (min 8 characters)")


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str = Field(..., description="Response message")
