"""
JWT Authentication Routes.

Endpoints:
- POST /auth/login - Login with email + password
- POST /auth/logout - Logout (invalidate token client-side)
- GET /auth/me - Get current user info
- POST /auth/refresh - Refresh access token
- POST /auth/set-password - Set password for first time (requires API-Key)
- PUT /auth/password - Change password (requires JWT)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.auth import (
    get_partner_by_email,
    get_current_partner,
    get_current_partner_jwt,
)
from app.models.partner import ApiPartner
from app.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
    verify_password,
    hash_password,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    AccessTokenResponse,
    CurrentUser,
    PasswordChangeRequest,
    SetPasswordRequest,
    MessageResponse,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login mit Email und Passwort",
    description="Authentifiziert einen Partner und gibt JWT Access- und Refresh-Tokens zurück.",
    responses={
        401: {"description": "Ungültige Credentials"},
        403: {"description": "Account deaktiviert"},
    },
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns JWT access token (short-lived) and refresh token (long-lived).
    """
    # Find partner by email
    partner = await get_partner_by_email(db, request.email)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige Email oder Passwort.",
        )

    # Check if password is set
    if not partner.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kein Passwort gesetzt. Bitte zuerst Passwort über /auth/set-password setzen.",
        )

    # Verify password
    if not verify_password(request.password, partner.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige Email oder Passwort.",
        )

    # Check if active
    if not partner.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner-Account ist deaktiviert.",
        )

    # Create tokens
    token_data = {"sub": partner.id, "email": partner.email, "role": partner.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Logout-Hinweis. Token-Invalidierung erfolgt client-seitig.",
)
async def logout():
    """
    Logout endpoint.

    Note: JWT tokens are stateless. Client should discard the tokens.
    For enhanced security, implement token blacklisting.
    """
    return MessageResponse(
        message="Logout erfolgreich. Bitte Token client-seitig verwerfen."
    )


@router.get(
    "/me",
    response_model=CurrentUser,
    summary="Aktueller Benutzer",
    description="Gibt Informationen zum aktuell authentifizierten Partner zurück.",
    responses={
        401: {"description": "Nicht authentifiziert"},
    },
)
async def get_me(
    partner: ApiPartner = Depends(get_current_partner_jwt),
):
    """Get current authenticated user info."""
    return CurrentUser.model_validate(partner)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Token erneuern",
    description="Erzeugt einen neuen Access Token mit einem gültigen Refresh Token.",
    responses={
        401: {"description": "Ungültiger Refresh Token"},
    },
)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using a valid refresh token.

    Returns a new access token. Refresh token remains unchanged.
    """
    payload = decode_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener Refresh Token.",
        )

    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falscher Token-Typ. Refresh Token erforderlich.",
        )

    partner_id = payload.get("sub")
    if not partner_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token enthält keine Partner-ID.",
        )

    # Verify partner still exists and is active
    from app.auth import get_partner_by_id
    partner = await get_partner_by_id(db, partner_id)

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partner nicht gefunden.",
        )

    if not partner.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner-Account ist deaktiviert.",
        )

    # Create new access token
    token_data = {"sub": partner.id, "email": partner.email, "role": partner.role}
    access_token = create_access_token(token_data)

    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/set-password",
    response_model=MessageResponse,
    summary="Passwort erstmalig setzen",
    description="Setzt das Passwort für einen Partner ohne Passwort. Erfordert API-Key Authentifizierung.",
    responses={
        400: {"description": "Passwort bereits gesetzt"},
        401: {"description": "Nicht authentifiziert"},
    },
)
async def set_password(
    request: SetPasswordRequest,
    partner: ApiPartner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """
    Set password for partner (first-time setup).

    Requires API-Key authentication. For partners without email,
    email must be set first via admin API.
    """
    if partner.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwort bereits gesetzt. Bitte /auth/password verwenden.",
        )

    if not partner.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keine Email-Adresse hinterlegt. Bitte zuerst Email via Admin-API setzen.",
        )

    # Set password
    partner.password_hash = hash_password(request.password)
    await db.commit()

    return MessageResponse(message="Passwort erfolgreich gesetzt.")


@router.put(
    "/password",
    response_model=MessageResponse,
    summary="Passwort ändern",
    description="Ändert das Passwort eines Partners. Erfordert JWT-Authentifizierung.",
    responses={
        400: {"description": "Aktuelles Passwort falsch"},
        401: {"description": "Nicht authentifiziert"},
    },
)
async def change_password(
    request: PasswordChangeRequest,
    partner: ApiPartner = Depends(get_current_partner_jwt),
    db: AsyncSession = Depends(get_db),
):
    """
    Change password for authenticated partner.

    Requires valid JWT token and correct current password.
    """
    if not partner.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kein Passwort gesetzt. Bitte /auth/set-password verwenden.",
        )

    if not verify_password(request.current_password, partner.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktuelles Passwort ist falsch.",
        )

    # Update password
    partner.password_hash = hash_password(request.new_password)
    await db.commit()

    return MessageResponse(message="Passwort erfolgreich geändert.")
