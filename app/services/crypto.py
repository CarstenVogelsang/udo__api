"""Symmetric encryption for sensitive system settings.

Uses Fernet (AES-128-CBC + HMAC-SHA256) for authenticated encryption.
The encryption key is derived from jwt_secret_key via PBKDF2.

WARNING: If jwt_secret_key changes, existing encrypted values become
unreadable. Re-encrypt all secret settings after key rotation.
"""
import base64
import logging

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings

logger = logging.getLogger(__name__)

# Static salt — acceptable since jwt_secret_key is already a strong secret.
_SALT = b"udo-system-settings-v1"


def _derive_key() -> bytes:
    """Derive a Fernet key from jwt_secret_key via PBKDF2."""
    secret = get_settings().jwt_secret_key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


def encrypt_value(plain: str) -> str:
    """Encrypt a plaintext value. Returns base64-encoded ciphertext."""
    if not plain:
        return ""
    f = Fernet(_derive_key())
    return f.encrypt(plain.encode()).decode()


def decrypt_value(cipher: str) -> str:
    """Decrypt an encrypted value. Returns plaintext."""
    if not cipher:
        return ""
    try:
        f = Fernet(_derive_key())
        return f.decrypt(cipher.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt setting value — key rotation?")
        return ""


def mask_value(plain: str, show_last: int = 4) -> str:
    """Mask a value, showing only the last N characters.

    Examples:
        mask_value("AIzaSyD...QXI") → "●●●●●●●●●●●● QXI"
        mask_value("abc") → "●●●"
        mask_value("") → ""
    """
    if not plain:
        return ""
    if len(plain) <= show_last:
        return "\u25cf" * len(plain)
    return "\u25cf" * (len(plain) - show_last) + plain[-show_last:]
