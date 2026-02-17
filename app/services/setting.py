"""
Business logic for System Settings (key-value store).

Supports encrypted storage for sensitive settings (ist_geheim=True).
Encryption uses Fernet (AES-128-CBC + HMAC) via app.services.crypto.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import SystemSetting
from app.services.crypto import decrypt_value, encrypt_value, mask_value

logger = logging.getLogger(__name__)


# Default settings with descriptions
DEFAULTS = {
    "bulk_action_max_results": {
        "value": "500",
        "beschreibung": "Max. Ergebnisse für Bulk-Aktionen (Auto-Expand bei Smart Filter)",
        "ist_geheim": False,
    },
    "recherche.google_places_api_key": {
        "value": "",
        "beschreibung": "Google Places API (New) Key für Recherche-Provider",
        "ist_geheim": True,
    },
    "recherche.dataforseo_login": {
        "value": "",
        "beschreibung": "DataForSEO Login (E-Mail) für SERP-Recherche",
        "ist_geheim": False,
    },
    "recherche.dataforseo_password": {
        "value": "",
        "beschreibung": "DataForSEO API-Passwort",
        "ist_geheim": True,
    },
}


class SettingService:
    """Service class for SystemSetting operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_settings(self) -> list[SystemSetting]:
        """Get all system settings."""
        query = select(SystemSetting).order_by(SystemSetting.key)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_settings_masked(self) -> list[dict]:
        """Get all settings with secret values masked.

        Returns dicts (not ORM objects) so we can safely replace values.
        """
        settings = await self.get_all_settings()
        result = []
        for s in settings:
            value = s.value
            if s.ist_geheim and value:
                plain = decrypt_value(value)
                value = mask_value(plain) if plain else ""
            result.append({
                "key": s.key,
                "value": value,
                "beschreibung": s.beschreibung,
                "ist_geheim": s.ist_geheim,
            })
        return result

    async def get_setting(self, key: str) -> SystemSetting | None:
        """Get a single setting by key."""
        query = select(SystemSetting).where(SystemSetting.key == key)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_value(self, key: str, default: str | None = None) -> str | None:
        """Get a decrypted setting value by key.

        For internal use (worker, services). Automatically decrypts
        secret values.
        """
        setting = await self.get_setting(key)
        if setting:
            if setting.ist_geheim and setting.value:
                return decrypt_value(setting.value)
            return setting.value
        return default

    async def get_value_masked(self, key: str) -> dict | None:
        """Get a setting with masked value (for API responses)."""
        setting = await self.get_setting(key)
        if not setting:
            return None

        value = setting.value
        if setting.ist_geheim and value:
            plain = decrypt_value(value)
            value = mask_value(plain) if plain else ""

        return {
            "key": setting.key,
            "value": value,
            "beschreibung": setting.beschreibung,
            "ist_geheim": setting.ist_geheim,
        }

    async def reveal_value(self, key: str) -> str | None:
        """Get decrypted plaintext for a secret setting.

        Returns None if key not found, empty string if not encrypted.
        """
        setting = await self.get_setting(key)
        if not setting:
            return None
        if setting.ist_geheim and setting.value:
            return decrypt_value(setting.value)
        return setting.value

    async def update_setting(self, key: str, value: str) -> SystemSetting | None:
        """Update a setting value. Encrypts if ist_geheim=True.

        Returns:
            Updated SystemSetting or None if key not found
        """
        setting = await self.get_setting(key)
        if not setting:
            return None

        if setting.ist_geheim and value:
            setting.value = encrypt_value(value)
        else:
            setting.value = value

        setting.aktualisiert_am = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def ensure_defaults(self) -> None:
        """Create default settings if they don't exist yet."""
        for key, config in DEFAULTS.items():
            existing = await self.get_setting(key)
            if not existing:
                setting = SystemSetting(
                    key=key,
                    value=config["value"],
                    beschreibung=config["beschreibung"],
                    ist_geheim=config.get("ist_geheim", False),
                )
                self.db.add(setting)
        await self.db.commit()
