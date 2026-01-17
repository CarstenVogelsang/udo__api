"""
Business logic for Plugin and Projekt management.

Handles:
- Plugin CRUD operations
- Plugin auto-sync from filesystem
- Projekt (satellite) management
- Projekttyp management
- Preis (pricing) management
"""
from datetime import datetime
import hashlib
import secrets

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.plugin import (
    PlgKategorie,
    PlgPlugin,
    PlgPluginVersion,
    PlgProjekttyp,
    PlgPreis,
    PlgProjekt,
    PlgPluginStatus,
)


# =============================================================================
# Kategorie Service
# =============================================================================

class KategorieService:
    """Service for Plugin-Kategorie operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        nur_aktiv: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get list of categories."""
        base_query = select(PlgKategorie)
        if nur_aktiv:
            base_query = base_query.where(PlgKategorie.ist_aktiv == True)

        # Count
        count_query = select(func.count(PlgKategorie.id))
        if nur_aktiv:
            count_query = count_query.where(PlgKategorie.ist_aktiv == True)
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(PlgKategorie.sortierung).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_by_id(self, kategorie_id: str) -> PlgKategorie | None:
        """Get category by ID."""
        query = select(PlgKategorie).where(PlgKategorie.id == kategorie_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> PlgKategorie | None:
        """Get category by slug."""
        query = select(PlgKategorie).where(PlgKategorie.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PlgKategorie:
        """Create a new category."""
        kategorie = PlgKategorie(**kwargs)
        self.db.add(kategorie)
        await self.db.commit()
        await self.db.refresh(kategorie)
        return kategorie

    async def update(self, kategorie_id: str, **kwargs) -> PlgKategorie | None:
        """Update a category."""
        kategorie = await self.get_by_id(kategorie_id)
        if not kategorie:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(kategorie, key):
                setattr(kategorie, key, value)

        await self.db.commit()
        await self.db.refresh(kategorie)
        return kategorie

    async def delete(self, kategorie_id: str) -> bool:
        """Delete a category (soft delete by setting ist_aktiv=False)."""
        kategorie = await self.get_by_id(kategorie_id)
        if not kategorie:
            return False

        kategorie.ist_aktiv = False
        await self.db.commit()
        return True


# =============================================================================
# Plugin Service
# =============================================================================

class PluginService:
    """Service for Plugin operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        status: str | None = None,
        kategorie_id: str | None = None,
        suche: str | None = None,
        nur_aktiv: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get list of plugins with optional filters."""
        base_query = select(PlgPlugin).options(
            joinedload(PlgPlugin.kategorie)
        )

        # Filters
        if status:
            base_query = base_query.where(PlgPlugin.status == status)
        elif nur_aktiv:
            base_query = base_query.where(PlgPlugin.status == PlgPluginStatus.AKTIV.value)

        if kategorie_id:
            base_query = base_query.where(PlgPlugin.kategorie_id == kategorie_id)

        if suche:
            pattern = f"%{suche}%"
            base_query = base_query.where(
                or_(
                    PlgPlugin.name.ilike(pattern),
                    PlgPlugin.beschreibung_kurz.ilike(pattern),
                    PlgPlugin.slug.ilike(pattern),
                )
            )

        # Count
        count_query = select(func.count(PlgPlugin.id))
        if status:
            count_query = count_query.where(PlgPlugin.status == status)
        elif nur_aktiv:
            count_query = count_query.where(PlgPlugin.status == PlgPluginStatus.AKTIV.value)
        if kategorie_id:
            count_query = count_query.where(PlgPlugin.kategorie_id == kategorie_id)
        if suche:
            pattern = f"%{suche}%"
            count_query = count_query.where(
                or_(
                    PlgPlugin.name.ilike(pattern),
                    PlgPlugin.beschreibung_kurz.ilike(pattern),
                    PlgPlugin.slug.ilike(pattern),
                )
            )
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(PlgPlugin.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_by_id(self, plugin_id: str) -> PlgPlugin | None:
        """Get plugin by ID with category."""
        query = (
            select(PlgPlugin)
            .options(joinedload(PlgPlugin.kategorie))
            .where(PlgPlugin.id == plugin_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> PlgPlugin | None:
        """Get plugin by slug with category."""
        query = (
            select(PlgPlugin)
            .options(joinedload(PlgPlugin.kategorie))
            .where(PlgPlugin.slug == slug)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PlgPlugin:
        """Create a new plugin."""
        plugin = PlgPlugin(**kwargs)
        self.db.add(plugin)
        await self.db.commit()
        await self.db.refresh(plugin)
        return await self.get_by_id(str(plugin.id))

    async def update(self, plugin_id: str, **kwargs) -> PlgPlugin | None:
        """Update a plugin."""
        query = select(PlgPlugin).where(PlgPlugin.id == plugin_id)
        result = await self.db.execute(query)
        plugin = result.scalar_one_or_none()

        if not plugin:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(plugin, key):
                setattr(plugin, key, value)

        await self.db.commit()
        return await self.get_by_id(plugin_id)

    async def delete(self, plugin_id: str) -> bool:
        """Delete a plugin (soft delete by setting status=deprecated)."""
        plugin = await self.get_by_id(plugin_id)
        if not plugin:
            return False

        plugin.status = PlgPluginStatus.DEPRECATED.value
        await self.db.commit()
        return True

    async def add_version(
        self,
        plugin_id: str,
        version: str,
        changelog: str | None = None,
        ist_breaking_change: bool = False,
        min_api_version: str | None = None,
    ) -> PlgPluginVersion | None:
        """Add a new version to a plugin."""
        plugin = await self.get_by_id(plugin_id)
        if not plugin:
            return None

        # Mark old version as not current
        update_query = (
            select(PlgPluginVersion)
            .where(PlgPluginVersion.plugin_id == plugin_id)
            .where(PlgPluginVersion.ist_aktuell == True)
        )
        result = await self.db.execute(update_query)
        old_version = result.scalar_one_or_none()
        if old_version:
            old_version.ist_aktuell = False

        # Create new version
        new_version = PlgPluginVersion(
            plugin_id=plugin_id,
            version=version,
            changelog=changelog,
            ist_aktuell=True,
            ist_breaking_change=ist_breaking_change,
            min_api_version=min_api_version,
        )
        self.db.add(new_version)

        # Update plugin's current version
        plugin.version = version
        plugin.version_datum = datetime.utcnow()
        if min_api_version:
            plugin.min_api_version = min_api_version

        await self.db.commit()
        await self.db.refresh(new_version)
        return new_version

    async def get_versions(self, plugin_id: str) -> list[PlgPluginVersion]:
        """Get all versions of a plugin."""
        query = (
            select(PlgPluginVersion)
            .where(PlgPluginVersion.plugin_id == plugin_id)
            .order_by(PlgPluginVersion.veroeffentlicht_am.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


# =============================================================================
# Projekttyp Service
# =============================================================================

class ProjekttypService:
    """Service for Projekttyp operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(self, skip: int = 0, limit: int = 100) -> dict:
        """Get list of project types."""
        # Count
        count_query = select(func.count(PlgProjekttyp.id))
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = (
            select(PlgProjekttyp)
            .order_by(PlgProjekttyp.sortierung)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_by_id(self, projekttyp_id: str) -> PlgProjekttyp | None:
        """Get project type by ID."""
        query = select(PlgProjekttyp).where(PlgProjekttyp.id == projekttyp_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> PlgProjekttyp | None:
        """Get project type by slug."""
        query = select(PlgProjekttyp).where(PlgProjekttyp.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PlgProjekttyp:
        """Create a new project type."""
        projekttyp = PlgProjekttyp(**kwargs)
        self.db.add(projekttyp)
        await self.db.commit()
        await self.db.refresh(projekttyp)
        return projekttyp

    async def update(self, projekttyp_id: str, **kwargs) -> PlgProjekttyp | None:
        """Update a project type."""
        projekttyp = await self.get_by_id(projekttyp_id)
        if not projekttyp:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(projekttyp, key):
                setattr(projekttyp, key, value)

        await self.db.commit()
        await self.db.refresh(projekttyp)
        return projekttyp

    async def seed_default_types(self) -> list[PlgProjekttyp]:
        """
        Seed default project types if they don't exist.

        Called during application startup.
        """
        default_types = [
            {
                "slug": "business_directory",
                "name": "Business Directory",
                "beschreibung": "Branchenverzeichnisse mit hohem Datenvolumen",
                "ist_kostenlos": False,
                "standard_testphase_tage": 14,
                "icon": "ti-building-store",
                "sortierung": 1,
            },
            {
                "slug": "einzelkunde",
                "name": "Einzelkunde",
                "beschreibung": "Normale Unternehmens-Webseiten",
                "ist_kostenlos": False,
                "standard_testphase_tage": 30,
                "icon": "ti-user",
                "sortierung": 2,
            },
            {
                "slug": "city_server",
                "name": "City Server",
                "beschreibung": "Stadtportale und kommunale Projekte",
                "ist_kostenlos": False,
                "standard_testphase_tage": 30,
                "icon": "ti-building-community",
                "sortierung": 3,
            },
            {
                "slug": "intern",
                "name": "Intern",
                "beschreibung": "Interne Projekte (kostenlos)",
                "ist_kostenlos": True,
                "ist_testphase_erlaubt": False,
                "standard_testphase_tage": 0,
                "icon": "ti-home",
                "sortierung": 4,
            },
        ]

        created = []
        for type_data in default_types:
            existing = await self.get_by_slug(type_data["slug"])
            if not existing:
                projekttyp = await self.create(**type_data)
                created.append(projekttyp)

        return created


# =============================================================================
# Preis Service
# =============================================================================

class PreisService:
    """Service for Preis (pricing) operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        plugin_id: str | None = None,
        projekttyp_id: str | None = None,
        nur_aktiv: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get list of prices with optional filters."""
        base_query = select(PlgPreis).options(
            joinedload(PlgPreis.plugin),
            joinedload(PlgPreis.projekttyp),
        )

        if plugin_id:
            base_query = base_query.where(PlgPreis.plugin_id == plugin_id)
        if projekttyp_id:
            base_query = base_query.where(PlgPreis.projekttyp_id == projekttyp_id)
        if nur_aktiv:
            base_query = base_query.where(PlgPreis.ist_aktiv == True)

        # Count
        count_query = select(func.count(PlgPreis.id))
        if plugin_id:
            count_query = count_query.where(PlgPreis.plugin_id == plugin_id)
        if projekttyp_id:
            count_query = count_query.where(PlgPreis.projekttyp_id == projekttyp_id)
        if nur_aktiv:
            count_query = count_query.where(PlgPreis.ist_aktiv == True)
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_by_id(self, preis_id: str) -> PlgPreis | None:
        """Get price by ID."""
        query = (
            select(PlgPreis)
            .options(
                joinedload(PlgPreis.plugin),
                joinedload(PlgPreis.projekttyp),
            )
            .where(PlgPreis.id == preis_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_for_plugin_and_typ(
        self,
        plugin_id: str,
        projekttyp_id: str
    ) -> PlgPreis | None:
        """Get active price for a specific plugin and project type."""
        query = (
            select(PlgPreis)
            .where(PlgPreis.plugin_id == plugin_id)
            .where(PlgPreis.projekttyp_id == projekttyp_id)
            .where(PlgPreis.ist_aktiv == True)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PlgPreis:
        """Create a new price."""
        preis = PlgPreis(**kwargs)
        self.db.add(preis)
        await self.db.commit()
        await self.db.refresh(preis)
        return await self.get_by_id(str(preis.id))

    async def update(self, preis_id: str, **kwargs) -> PlgPreis | None:
        """Update a price."""
        query = select(PlgPreis).where(PlgPreis.id == preis_id)
        result = await self.db.execute(query)
        preis = result.scalar_one_or_none()

        if not preis:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(preis, key):
                setattr(preis, key, value)

        await self.db.commit()
        return await self.get_by_id(preis_id)

    async def deactivate(self, preis_id: str) -> bool:
        """Deactivate a price."""
        preis = await self.get_by_id(preis_id)
        if not preis:
            return False

        preis.ist_aktiv = False
        await self.db.commit()
        return True


# =============================================================================
# Projekt Service
# =============================================================================

class ProjektService:
    """Service for Projekt (satellite) operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        projekttyp_id: str | None = None,
        nur_aktiv: bool = True,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get list of projects with optional filters."""
        base_query = select(PlgProjekt).options(
            joinedload(PlgProjekt.projekttyp)
        )

        if projekttyp_id:
            base_query = base_query.where(PlgProjekt.projekttyp_id == projekttyp_id)
        if nur_aktiv:
            base_query = base_query.where(PlgProjekt.ist_aktiv == True)
        if suche:
            pattern = f"%{suche}%"
            base_query = base_query.where(
                or_(
                    PlgProjekt.name.ilike(pattern),
                    PlgProjekt.slug.ilike(pattern),
                    PlgProjekt.kontakt_email.ilike(pattern),
                )
            )

        # Count
        count_query = select(func.count(PlgProjekt.id))
        if projekttyp_id:
            count_query = count_query.where(PlgProjekt.projekttyp_id == projekttyp_id)
        if nur_aktiv:
            count_query = count_query.where(PlgProjekt.ist_aktiv == True)
        if suche:
            pattern = f"%{suche}%"
            count_query = count_query.where(
                or_(
                    PlgProjekt.name.ilike(pattern),
                    PlgProjekt.slug.ilike(pattern),
                    PlgProjekt.kontakt_email.ilike(pattern),
                )
            )
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(PlgProjekt.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_by_id(self, projekt_id: str) -> PlgProjekt | None:
        """Get project by ID."""
        query = (
            select(PlgProjekt)
            .options(joinedload(PlgProjekt.projekttyp))
            .where(PlgProjekt.id == projekt_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> PlgProjekt | None:
        """Get project by slug."""
        query = (
            select(PlgProjekt)
            .options(joinedload(PlgProjekt.projekttyp))
            .where(PlgProjekt.slug == slug)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_api_key(self, api_key: str) -> PlgProjekt | None:
        """Get project by API key (hashed)."""
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        query = (
            select(PlgProjekt)
            .options(joinedload(PlgProjekt.projekttyp))
            .where(PlgProjekt.api_key_hash == api_key_hash)
            .where(PlgProjekt.ist_aktiv == True)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PlgProjekt:
        """Create a new project."""
        projekt = PlgProjekt(**kwargs)
        projekt.aktiviert_am = datetime.utcnow()
        self.db.add(projekt)
        await self.db.commit()
        await self.db.refresh(projekt)
        return await self.get_by_id(str(projekt.id))

    async def update(self, projekt_id: str, **kwargs) -> PlgProjekt | None:
        """Update a project."""
        query = select(PlgProjekt).where(PlgProjekt.id == projekt_id)
        result = await self.db.execute(query)
        projekt = result.scalar_one_or_none()

        if not projekt:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(projekt, key):
                setattr(projekt, key, value)

        await self.db.commit()
        return await self.get_by_id(projekt_id)

    async def deactivate(self, projekt_id: str) -> bool:
        """Deactivate a project."""
        projekt = await self.get_by_id(projekt_id)
        if not projekt:
            return False

        projekt.ist_aktiv = False
        projekt.deaktiviert_am = datetime.utcnow()
        await self.db.commit()
        return True

    async def generate_api_key(self, projekt_id: str) -> str | None:
        """
        Generate a new API key for a project.

        Returns the plain API key (only shown once!).
        The hash is stored in the database.
        """
        query = select(PlgProjekt).where(PlgProjekt.id == projekt_id)
        result = await self.db.execute(query)
        projekt = result.scalar_one_or_none()

        if not projekt:
            return None

        # Generate secure API key
        api_key = secrets.token_urlsafe(32)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        projekt.api_key_hash = api_key_hash
        await self.db.commit()

        return api_key
