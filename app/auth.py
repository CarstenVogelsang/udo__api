"""
Authentication module for API-Key based access control.

API-Keys are passed via X-API-Key header and validated against SHA-256 hashes in the database.
"""
import hashlib

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.partner import ApiPartner

# API Key Header definition
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(api_key: str) -> str:
    """Creates SHA-256 hash of API key."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_partner_by_key_hash(db: AsyncSession, key_hash: str) -> ApiPartner | None:
    """Retrieves partner by API key hash."""
    query = select(ApiPartner).where(ApiPartner.api_key_hash == key_hash)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_current_partner(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> ApiPartner:
    """
    Validates API key and returns the authenticated partner.

    Raises:
        HTTPException 401: If API key is missing or invalid
        HTTPException 403: If partner account is deactivated
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API-Key fehlt. Bitte X-API-Key Header setzen.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_hash = hash_api_key(api_key)
    partner = await get_partner_by_key_hash(db, key_hash)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not partner.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner-Account ist deaktiviert.",
        )

    return partner


async def require_superadmin(
    partner: ApiPartner = Depends(get_current_partner)
) -> ApiPartner:
    """
    Requires the authenticated partner to have superadmin role.

    Raises:
        HTTPException 403: If partner is not a superadmin
    """
    if partner.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin-Berechtigung erforderlich.",
        )
    return partner
