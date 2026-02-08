"""
Authentication module for API-Key and JWT based access control.

Supports two authentication methods:
1. API-Key: Passed via X-API-Key header (for programmatic API access)
2. JWT Bearer Token: Passed via Authorization header (for web UI access)

Billing-aware dependency: get_current_partner_with_billing()
checks billing access (credits/invoice/internal) before allowing API calls.
"""
import hashlib

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.partner import ApiPartner
from app.services.jwt_service import decode_token, verify_token_type

# API Key Header definition (existing)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer token definition (new)
bearer_scheme = HTTPBearer(auto_error=False)


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


# === JWT Authentication ===

async def get_partner_by_email(db: AsyncSession, email: str) -> ApiPartner | None:
    """Retrieves partner by email address."""
    query = select(ApiPartner).where(ApiPartner.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_partner_by_id(db: AsyncSession, partner_id: str) -> ApiPartner | None:
    """Retrieves partner by ID."""
    query = select(ApiPartner).where(ApiPartner.id == partner_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_current_partner_jwt(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> ApiPartner:
    """
    Validates JWT bearer token and returns the authenticated partner.

    Raises:
        HTTPException 401: If token is missing or invalid
        HTTPException 403: If partner account is deactivated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization-Header fehlt. Bitte Bearer Token setzen.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener Token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falscher Token-Typ. Access Token erforderlich.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    partner_id = payload.get("sub")
    if not partner_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token enthält keine Partner-ID.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    partner = await get_partner_by_id(db, partner_id)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partner nicht gefunden.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not partner.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner-Account ist deaktiviert.",
        )

    return partner


async def get_current_partner_flexible(
    api_key: str | None = Security(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> ApiPartner:
    """
    Flexible authentication that accepts either API-Key or JWT Bearer token.

    Priority: JWT Bearer token > API-Key

    Raises:
        HTTPException 401: If neither auth method is provided or valid
        HTTPException 403: If partner account is deactivated
    """
    # Try JWT first
    if credentials:
        payload = decode_token(credentials.credentials)
        if payload and verify_token_type(payload, "access"):
            partner_id = payload.get("sub")
            if partner_id:
                partner = await get_partner_by_id(db, partner_id)
                if partner:
                    if not partner.is_active:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Partner-Account ist deaktiviert.",
                        )
                    return partner

    # Fallback to API-Key
    if api_key:
        key_hash = hash_api_key(api_key)
        partner = await get_partner_by_key_hash(db, key_hash)
        if partner:
            if not partner.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Partner-Account ist deaktiviert.",
                )
            return partner

    # Neither method worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentifizierung erforderlich. Bitte X-API-Key Header oder Bearer Token setzen.",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )


# === Billing Access Control ===

async def get_current_partner_with_billing(
    partner: ApiPartner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
) -> ApiPartner:
    """
    Validates API key AND checks billing access.

    Raises 402 Payment Required if:
    - Partner is manually blocked (ist_gesperrt)
    - Credits billing: balance <= 0
    - Invoice billing: monthly limit reached
    """
    from app.services.billing import BillingService
    billing_service = BillingService(db)
    await billing_service.check_billing_access(partner.id)
    return partner


# === Role-based Access Control ===

async def require_superadmin(
    partner: ApiPartner = Depends(get_current_partner_flexible)
) -> ApiPartner:
    """
    Requires the authenticated partner to have superadmin role.
    Accepts both API-Key and JWT Bearer token.

    Raises:
        HTTPException 403: If partner is not a superadmin
    """
    if partner.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin-Berechtigung erforderlich.",
        )
    return partner
