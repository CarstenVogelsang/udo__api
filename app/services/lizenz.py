"""
Business logic for License (Lizenz) management.

Handles:
- License CRUD operations
- License lifecycle (testphase -> aktiv -> gekündigt -> abgelaufen)
- License history/audit trail
- License checks for satellites
"""
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.plugin import (
    PlgLizenz,
    PlgLizenzHistorie,
    PlgPlugin,
    PlgProjekt,
    PlgPreis,
    PlgProjekttyp,
    PlgLizenzStatus,
    PlgPluginStatus,
)


class LizenzService:
    """Service for License operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # List & Query
    # =========================================================================

    async def get_list(
        self,
        projekt_id: str | None = None,
        plugin_id: str | None = None,
        status: str | None = None,
        nur_aktiv: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get list of licenses with optional filters."""
        base_query = select(PlgLizenz).options(
            joinedload(PlgLizenz.projekt),
            joinedload(PlgLizenz.plugin),
            joinedload(PlgLizenz.preis),
        )

        if projekt_id:
            base_query = base_query.where(PlgLizenz.projekt_id == projekt_id)
        if plugin_id:
            base_query = base_query.where(PlgLizenz.plugin_id == plugin_id)
        if status:
            base_query = base_query.where(PlgLizenz.status == status)
        elif nur_aktiv:
            base_query = base_query.where(
                PlgLizenz.status.in_([
                    PlgLizenzStatus.AKTIV.value,
                    PlgLizenzStatus.TESTPHASE.value,
                ])
            )

        # Count
        count_query = select(func.count(PlgLizenz.id))
        if projekt_id:
            count_query = count_query.where(PlgLizenz.projekt_id == projekt_id)
        if plugin_id:
            count_query = count_query.where(PlgLizenz.plugin_id == plugin_id)
        if status:
            count_query = count_query.where(PlgLizenz.status == status)
        elif nur_aktiv:
            count_query = count_query.where(
                PlgLizenz.status.in_([
                    PlgLizenzStatus.AKTIV.value,
                    PlgLizenzStatus.TESTPHASE.value,
                ])
            )
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = (
            base_query
            .order_by(PlgLizenz.lizenz_start.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_by_id(self, lizenz_id: str) -> PlgLizenz | None:
        """Get license by ID with relations."""
        query = (
            select(PlgLizenz)
            .options(
                joinedload(PlgLizenz.projekt).joinedload(PlgProjekt.projekttyp),
                joinedload(PlgLizenz.plugin),
                joinedload(PlgLizenz.preis),
                joinedload(PlgLizenz.historie),
            )
            .where(PlgLizenz.id == lizenz_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_for_projekt_and_plugin(
        self,
        projekt_id: str,
        plugin_id: str,
        nur_aktiv: bool = True
    ) -> PlgLizenz | None:
        """Get license for a specific project-plugin combination."""
        query = (
            select(PlgLizenz)
            .options(
                joinedload(PlgLizenz.projekt),
                joinedload(PlgLizenz.plugin),
            )
            .where(PlgLizenz.projekt_id == projekt_id)
            .where(PlgLizenz.plugin_id == plugin_id)
        )

        if nur_aktiv:
            query = query.where(
                PlgLizenz.status.in_([
                    PlgLizenzStatus.AKTIV.value,
                    PlgLizenzStatus.TESTPHASE.value,
                    PlgLizenzStatus.GEKUENDIGT.value,  # Still valid until end date
                ])
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_projekt_lizenzen(self, projekt_id: str) -> list[PlgLizenz]:
        """Get all licenses for a project."""
        query = (
            select(PlgLizenz)
            .options(joinedload(PlgLizenz.plugin))
            .where(PlgLizenz.projekt_id == projekt_id)
            .order_by(PlgLizenz.lizenz_start.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    # =========================================================================
    # Create & Update
    # =========================================================================

    async def create(
        self,
        projekt_id: str,
        plugin_id: str,
        preis_id: str | None = None,
        ist_testphase: bool = False,
        lizenz_ende: datetime | None = None,
        notizen: str | None = None,
    ) -> PlgLizenz | None:
        """
        Create a new license.

        For trial licenses, calculates end date based on project type.
        Creates initial history entry.
        """
        # Verify project and plugin exist
        projekt_query = (
            select(PlgProjekt)
            .options(joinedload(PlgProjekt.projekttyp))
            .where(PlgProjekt.id == projekt_id)
        )
        projekt_result = await self.db.execute(projekt_query)
        projekt = projekt_result.scalar_one_or_none()
        if not projekt:
            return None

        plugin_query = select(PlgPlugin).where(PlgPlugin.id == plugin_id)
        plugin_result = await self.db.execute(plugin_query)
        plugin = plugin_result.scalar_one_or_none()
        if not plugin:
            return None

        # Check if license already exists
        existing = await self.get_for_projekt_and_plugin(projekt_id, plugin_id)
        if existing:
            return None  # Already licensed

        # Determine price
        preis = None
        preis_snapshot = None
        preis_modell_snapshot = None
        if preis_id:
            preis_query = select(PlgPreis).where(PlgPreis.id == preis_id)
            preis_result = await self.db.execute(preis_query)
            preis = preis_result.scalar_one_or_none()
            if preis:
                preis_snapshot = preis.preis
                preis_modell_snapshot = preis.modell

        # Calculate trial end date if applicable
        testphase_ende = None
        if ist_testphase and projekt.projekttyp:
            if not projekt.projekttyp.ist_testphase_erlaubt:
                ist_testphase = False  # Override if not allowed
            else:
                tage = projekt.projekttyp.standard_testphase_tage or 30
                testphase_ende = datetime.utcnow() + timedelta(days=tage)

        # Determine initial status
        if ist_testphase:
            status = PlgLizenzStatus.TESTPHASE.value
        elif projekt.projekttyp and projekt.projekttyp.ist_kostenlos:
            status = PlgLizenzStatus.AKTIV.value  # Internal projects are immediately active
        else:
            status = PlgLizenzStatus.AKTIV.value

        # Create license
        lizenz = PlgLizenz(
            projekt_id=projekt_id,
            plugin_id=plugin_id,
            preis_id=preis_id,
            status=status,
            ist_testphase=ist_testphase,
            testphase_ende=testphase_ende,
            lizenz_ende=lizenz_ende,
            preis_snapshot=preis_snapshot,
            preis_modell_snapshot=preis_modell_snapshot,
            plugin_version_bei_lizenzierung=plugin.version,
            notizen=notizen,
        )
        self.db.add(lizenz)
        await self.db.commit()
        await self.db.refresh(lizenz)

        # Create initial history entry
        await self._add_history(
            lizenz_id=str(lizenz.id),
            alter_status=None,
            neuer_status=status,
            aenderungsgrund="Lizenz erstellt",
            geaendert_von_typ="system",
        )

        return await self.get_by_id(str(lizenz.id))

    async def update(self, lizenz_id: str, **kwargs) -> PlgLizenz | None:
        """Update a license (general update)."""
        query = select(PlgLizenz).where(PlgLizenz.id == lizenz_id)
        result = await self.db.execute(query)
        lizenz = result.scalar_one_or_none()

        if not lizenz:
            return None

        old_status = lizenz.status

        for key, value in kwargs.items():
            if value is not None and hasattr(lizenz, key):
                setattr(lizenz, key, value)

        # Track status change
        if "status" in kwargs and kwargs["status"] != old_status:
            await self._add_history(
                lizenz_id=lizenz_id,
                alter_status=old_status,
                neuer_status=kwargs["status"],
                aenderungsgrund="Status manuell geändert",
                geaendert_von_typ="admin",
            )

        await self.db.commit()
        return await self.get_by_id(lizenz_id)

    # =========================================================================
    # Lifecycle Operations
    # =========================================================================

    async def aktivieren(
        self,
        lizenz_id: str,
        preis_id: str | None = None,
    ) -> PlgLizenz | None:
        """
        Convert trial to active license.

        Sets status to AKTIV and marks testphase_konvertiert.
        """
        lizenz = await self.get_by_id(lizenz_id)
        if not lizenz:
            return None

        if lizenz.status != PlgLizenzStatus.TESTPHASE.value:
            return None  # Can only activate from trial

        old_status = lizenz.status

        # Update price if provided
        if preis_id:
            preis_query = select(PlgPreis).where(PlgPreis.id == preis_id)
            preis_result = await self.db.execute(preis_query)
            preis = preis_result.scalar_one_or_none()
            if preis:
                lizenz.preis_id = preis_id
                lizenz.preis_snapshot = preis.preis
                lizenz.preis_modell_snapshot = preis.modell

        lizenz.status = PlgLizenzStatus.AKTIV.value
        lizenz.ist_testphase = False
        lizenz.testphase_konvertiert = True

        await self.db.commit()

        await self._add_history(
            lizenz_id=lizenz_id,
            alter_status=old_status,
            neuer_status=PlgLizenzStatus.AKTIV.value,
            aenderungsgrund="Testphase in Vollversion umgewandelt",
            geaendert_von_typ="admin",
        )

        return await self.get_by_id(lizenz_id)

    async def kuendigen(
        self,
        lizenz_id: str,
        grund: str | None = None,
        zum: datetime | None = None,
    ) -> PlgLizenz | None:
        """
        Cancel a license.

        License remains active until the effective cancellation date.
        """
        lizenz = await self.get_by_id(lizenz_id)
        if not lizenz:
            return None

        if lizenz.status not in [
            PlgLizenzStatus.AKTIV.value,
            PlgLizenzStatus.TESTPHASE.value,
        ]:
            return None  # Can only cancel active/trial licenses

        old_status = lizenz.status

        lizenz.status = PlgLizenzStatus.GEKUENDIGT.value
        lizenz.gekuendigt_am = datetime.utcnow()
        lizenz.kuendigung_grund = grund
        lizenz.kuendigung_zum = zum or lizenz.lizenz_ende

        await self.db.commit()

        await self._add_history(
            lizenz_id=lizenz_id,
            alter_status=old_status,
            neuer_status=PlgLizenzStatus.GEKUENDIGT.value,
            aenderungsgrund=grund or "Lizenz gekündigt",
            geaendert_von_typ="admin",
        )

        return await self.get_by_id(lizenz_id)

    async def stornieren(
        self,
        lizenz_id: str,
        grund: str | None = None,
    ) -> PlgLizenz | None:
        """
        Immediately cancel a license (hard cancel).

        Use sparingly - only for contract violations or fraud.
        """
        lizenz = await self.get_by_id(lizenz_id)
        if not lizenz:
            return None

        old_status = lizenz.status

        lizenz.status = PlgLizenzStatus.STORNIERT.value
        lizenz.gekuendigt_am = datetime.utcnow()
        lizenz.kuendigung_grund = grund
        lizenz.kuendigung_zum = datetime.utcnow()  # Effective immediately

        await self.db.commit()

        await self._add_history(
            lizenz_id=lizenz_id,
            alter_status=old_status,
            neuer_status=PlgLizenzStatus.STORNIERT.value,
            aenderungsgrund=grund or "Lizenz storniert",
            geaendert_von_typ="admin",
        )

        return await self.get_by_id(lizenz_id)

    async def pausieren(self, lizenz_id: str) -> PlgLizenz | None:
        """Pause a license temporarily."""
        lizenz = await self.get_by_id(lizenz_id)
        if not lizenz:
            return None

        if lizenz.status != PlgLizenzStatus.AKTIV.value:
            return None

        old_status = lizenz.status
        lizenz.status = PlgLizenzStatus.PAUSIERT.value

        await self.db.commit()

        await self._add_history(
            lizenz_id=lizenz_id,
            alter_status=old_status,
            neuer_status=PlgLizenzStatus.PAUSIERT.value,
            aenderungsgrund="Lizenz pausiert",
            geaendert_von_typ="admin",
        )

        return await self.get_by_id(lizenz_id)

    async def fortsetzen(self, lizenz_id: str) -> PlgLizenz | None:
        """Resume a paused license."""
        lizenz = await self.get_by_id(lizenz_id)
        if not lizenz:
            return None

        if lizenz.status != PlgLizenzStatus.PAUSIERT.value:
            return None

        old_status = lizenz.status
        lizenz.status = PlgLizenzStatus.AKTIV.value

        await self.db.commit()

        await self._add_history(
            lizenz_id=lizenz_id,
            alter_status=old_status,
            neuer_status=PlgLizenzStatus.AKTIV.value,
            aenderungsgrund="Lizenz fortgesetzt",
            geaendert_von_typ="admin",
        )

        return await self.get_by_id(lizenz_id)

    # =========================================================================
    # License Check (for Satellites)
    # =========================================================================

    async def check_lizenz(
        self,
        projekt_id: str,
        plugin_slug: str,
    ) -> dict:
        """
        Check if a project has a valid license for a plugin.

        Used by satellites to verify access.

        Returns:
            Dict with license status information
        """
        # Get plugin by slug
        plugin_query = select(PlgPlugin).where(PlgPlugin.slug == plugin_slug)
        plugin_result = await self.db.execute(plugin_query)
        plugin = plugin_result.scalar_one_or_none()

        if not plugin:
            return {
                "lizenziert": False,
                "status": None,
                "lizenz_ende": None,
                "plugin_version": None,
                "ist_testphase": False,
                "testphase_ende": None,
            }

        # Check for active license
        lizenz = await self.get_for_projekt_and_plugin(projekt_id, str(plugin.id))

        if not lizenz:
            return {
                "lizenziert": False,
                "status": None,
                "lizenz_ende": None,
                "plugin_version": plugin.version,
                "ist_testphase": False,
                "testphase_ende": None,
            }

        # Check if license is still valid
        now = datetime.utcnow()
        is_valid = True

        if lizenz.status == PlgLizenzStatus.TESTPHASE.value:
            if lizenz.testphase_ende and lizenz.testphase_ende < now:
                is_valid = False
        elif lizenz.status == PlgLizenzStatus.GEKUENDIGT.value:
            if lizenz.kuendigung_zum and lizenz.kuendigung_zum < now:
                is_valid = False
        elif lizenz.status in [
            PlgLizenzStatus.ABGELAUFEN.value,
            PlgLizenzStatus.STORNIERT.value,
        ]:
            is_valid = False
        elif lizenz.status == PlgLizenzStatus.PAUSIERT.value:
            is_valid = False

        return {
            "lizenziert": is_valid,
            "status": lizenz.status,
            "lizenz_ende": lizenz.lizenz_ende or lizenz.kuendigung_zum,
            "plugin_version": plugin.version,
            "ist_testphase": lizenz.ist_testphase,
            "testphase_ende": lizenz.testphase_ende,
        }

    # =========================================================================
    # History
    # =========================================================================

    async def get_historie(self, lizenz_id: str) -> list[PlgLizenzHistorie]:
        """Get license history."""
        query = (
            select(PlgLizenzHistorie)
            .where(PlgLizenzHistorie.lizenz_id == lizenz_id)
            .order_by(PlgLizenzHistorie.erstellt_am.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _add_history(
        self,
        lizenz_id: str,
        alter_status: str | None,
        neuer_status: str,
        aenderungsgrund: str | None = None,
        notizen: str | None = None,
        geaendert_von: str | None = None,
        geaendert_von_typ: str = "system",
    ) -> PlgLizenzHistorie:
        """Add a history entry (internal method)."""
        historie = PlgLizenzHistorie(
            lizenz_id=lizenz_id,
            alter_status=alter_status,
            neuer_status=neuer_status,
            aenderungsgrund=aenderungsgrund,
            notizen=notizen,
            geaendert_von=geaendert_von,
            geaendert_von_typ=geaendert_von_typ,
        )
        self.db.add(historie)
        await self.db.commit()
        return historie

    # =========================================================================
    # Maintenance
    # =========================================================================

    async def expire_trials(self) -> int:
        """
        Mark expired trial licenses as ABGELAUFEN.

        Should be called periodically (e.g., daily cron job).

        Returns:
            Number of expired licenses
        """
        now = datetime.utcnow()

        query = (
            select(PlgLizenz)
            .where(PlgLizenz.status == PlgLizenzStatus.TESTPHASE.value)
            .where(PlgLizenz.testphase_ende < now)
        )
        result = await self.db.execute(query)
        expired = result.scalars().all()

        count = 0
        for lizenz in expired:
            lizenz.status = PlgLizenzStatus.ABGELAUFEN.value
            await self._add_history(
                lizenz_id=str(lizenz.id),
                alter_status=PlgLizenzStatus.TESTPHASE.value,
                neuer_status=PlgLizenzStatus.ABGELAUFEN.value,
                aenderungsgrund="Testphase automatisch abgelaufen",
                geaendert_von_typ="system",
            )
            count += 1

        await self.db.commit()
        return count

    async def expire_cancelled(self) -> int:
        """
        Mark cancelled licenses past their end date as ABGELAUFEN.

        Should be called periodically (e.g., daily cron job).

        Returns:
            Number of expired licenses
        """
        now = datetime.utcnow()

        query = (
            select(PlgLizenz)
            .where(PlgLizenz.status == PlgLizenzStatus.GEKUENDIGT.value)
            .where(PlgLizenz.kuendigung_zum < now)
        )
        result = await self.db.execute(query)
        expired = result.scalars().all()

        count = 0
        for lizenz in expired:
            lizenz.status = PlgLizenzStatus.ABGELAUFEN.value
            await self._add_history(
                lizenz_id=str(lizenz.id),
                alter_status=PlgLizenzStatus.GEKUENDIGT.value,
                neuer_status=PlgLizenzStatus.ABGELAUFEN.value,
                aenderungsgrund="Kündigungsdatum erreicht",
                geaendert_von_typ="system",
            )
            count += 1

        await self.db.commit()
        return count
