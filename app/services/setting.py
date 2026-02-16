"""
Business logic for System Settings (key-value store).
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import SystemSetting


# Default settings with descriptions
DEFAULTS = {
    "bulk_action_max_results": {
        "value": "500",
        "beschreibung": "Max. Ergebnisse für Bulk-Aktionen (Auto-Expand bei Smart Filter)",
    },
    "recherche.google_places_api_key": {
        "value": "",
        "beschreibung": "Google Places API (New) Key für Recherche-Provider",
    },
    "recherche.dataforseo_login": {
        "value": "",
        "beschreibung": "DataForSEO Login (E-Mail) für SERP-Recherche",
    },
    "recherche.dataforseo_password": {
        "value": "",
        "beschreibung": "DataForSEO API-Passwort",
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

    async def get_setting(self, key: str) -> SystemSetting | None:
        """Get a single setting by key."""
        query = select(SystemSetting).where(SystemSetting.key == key)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_value(self, key: str, default: str | None = None) -> str | None:
        """Get a setting value by key, with optional default."""
        setting = await self.get_setting(key)
        if setting:
            return setting.value
        return default

    async def update_setting(self, key: str, value: str) -> SystemSetting | None:
        """
        Update a setting value.

        Returns:
            Updated SystemSetting or None if key not found
        """
        setting = await self.get_setting(key)
        if not setting:
            return None

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
                )
                self.db.add(setting)
        await self.db.commit()
