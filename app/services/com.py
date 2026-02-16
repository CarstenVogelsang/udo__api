"""
Business logic and database queries for Company (Unternehmen) data.
"""
from datetime import datetime

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.com import ComUnternehmen, ComKontakt
from app.models.geo import GeoOrt, GeoKreis, GeoBundesland


class ComService:
    """Service class for Company (Unternehmen) operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_unternehmen_list(
        self,
        geo_ort_id: str | None = None,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 100,
        filter_conditions: list | None = None,
        include_deleted: bool = False,
    ) -> dict:
        """
        Get companies with full geo hierarchy.

        Args:
            geo_ort_id: Filter by GeoOrt UUID
            suche: Search in kurzname and firmierung
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Dict with items and total count
        """
        # Base query with eager loading of full geo hierarchy
        base_query = (
            select(ComUnternehmen)
            .options(
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.regierungsbezirk),
            )
        )

        # Soft-delete filter (default: only non-deleted)
        if not include_deleted:
            base_query = base_query.where(ComUnternehmen.geloescht_am == None)  # noqa: E711

        # Apply filters
        if geo_ort_id:
            base_query = base_query.where(ComUnternehmen.geo_ort_id == geo_ort_id)
        if suche:
            search_pattern = f"%{suche}%"
            base_query = base_query.where(
                or_(
                    ComUnternehmen.kurzname.ilike(search_pattern),
                    ComUnternehmen.firmierung.ilike(search_pattern),
                )
            )
        if filter_conditions:
            for condition in filter_conditions:
                base_query = base_query.where(condition)

        # Count query
        count_query = select(func.count(ComUnternehmen.id))
        if not include_deleted:
            count_query = count_query.where(ComUnternehmen.geloescht_am == None)  # noqa: E711
        if geo_ort_id:
            count_query = count_query.where(ComUnternehmen.geo_ort_id == geo_ort_id)
        if suche:
            search_pattern = f"%{suche}%"
            count_query = count_query.where(
                or_(
                    ComUnternehmen.kurzname.ilike(search_pattern),
                    ComUnternehmen.firmierung.ilike(search_pattern),
                )
            )
        if filter_conditions:
            for condition in filter_conditions:
                count_query = count_query.where(condition)
        total = (await self.db.execute(count_query)).scalar()

        # Unfiltered total (when smart filter is active, also count without filter)
        total_unfiltered = total
        if filter_conditions:
            unfiltered_count_query = select(func.count(ComUnternehmen.id))
            if not include_deleted:
                unfiltered_count_query = unfiltered_count_query.where(
                    ComUnternehmen.geloescht_am == None  # noqa: E711
                )
            if geo_ort_id:
                unfiltered_count_query = unfiltered_count_query.where(
                    ComUnternehmen.geo_ort_id == geo_ort_id
                )
            if suche:
                search_pattern = f"%{suche}%"
                unfiltered_count_query = unfiltered_count_query.where(
                    or_(
                        ComUnternehmen.kurzname.ilike(search_pattern),
                        ComUnternehmen.firmierung.ilike(search_pattern),
                    )
                )
            total_unfiltered = (await self.db.execute(unfiltered_count_query)).scalar()

        # Data query
        query = (
            base_query
            .order_by(ComUnternehmen.kurzname)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        # .unique() because joinedload can create duplicates
        items = result.scalars().unique().all()

        return {"items": items, "total": total, "total_unfiltered": total_unfiltered}

    async def get_unternehmen_by_id(self, unternehmen_id: str) -> ComUnternehmen | None:
        """
        Get a single company by UUID with full geo hierarchy.
        """
        query = (
            select(ComUnternehmen)
            .options(
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.regierungsbezirk),
            )
            .where(ComUnternehmen.id == unternehmen_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_unternehmen_by_legacy_id(self, legacy_id: int) -> ComUnternehmen | None:
        """
        Get a single company by legacy ID (kStore) with full geo hierarchy.

        Useful for:
        - Looking up companies by their original spi_tStore key
        - Verifying import results
        """
        query = (
            select(ComUnternehmen)
            .options(
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.regierungsbezirk),
            )
            .where(ComUnternehmen.legacy_id == legacy_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_unternehmen_count(self) -> int:
        """Get total number of companies."""
        query = select(func.count(ComUnternehmen.id))
        return (await self.db.execute(query)).scalar() or 0

    async def get_unternehmen_by_ort(
        self,
        geo_ort_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """
        Get all companies in a specific city/municipality.

        Shortcut for get_unternehmen_list with geo_ort_id filter.
        """
        return await self.get_unternehmen_list(
            geo_ort_id=geo_ort_id,
            skip=skip,
            limit=limit
        )

    async def create_unternehmen(self, **kwargs) -> ComUnternehmen:
        """
        Create a new company.

        Accepts any column name of ComUnternehmen as keyword argument.
        None values are filtered out.

        Returns:
            Created ComUnternehmen instance
        """
        data = {k: v for k, v in kwargs.items() if v is not None}
        unternehmen = ComUnternehmen(**data)
        self.db.add(unternehmen)
        await self.db.commit()
        await self.db.refresh(unternehmen)

        # Reload with full geo hierarchy
        return await self.get_unternehmen_by_id(str(unternehmen.id))

    async def update_unternehmen(
        self,
        unternehmen_id: str,
        **kwargs
    ) -> ComUnternehmen | None:
        """
        Update an existing company.

        Args:
            unternehmen_id: UUID of the company
            **kwargs: Fields to update

        Returns:
            Updated ComUnternehmen or None if not found
        """
        # First get the unternehmen without eager loading
        query = select(ComUnternehmen).where(ComUnternehmen.id == unternehmen_id)
        result = await self.db.execute(query)
        unternehmen = result.scalar_one_or_none()

        if not unternehmen:
            return None

        # Update fields
        for key, value in kwargs.items():
            if value is not None and hasattr(unternehmen, key):
                setattr(unternehmen, key, value)

        await self.db.commit()
        await self.db.refresh(unternehmen)

        # Reload with full geo hierarchy
        return await self.get_unternehmen_by_id(unternehmen_id)

    async def delete_unternehmen(self, unternehmen_id: str) -> bool:
        """
        Hard-delete a company (permanent).

        Also deletes all associated contacts and organisation assignments.

        Args:
            unternehmen_id: UUID of the company

        Returns:
            True if deleted, False if not found
        """
        query = select(ComUnternehmen).where(ComUnternehmen.id == unternehmen_id)
        result = await self.db.execute(query)
        unternehmen = result.scalar_one_or_none()

        if not unternehmen:
            return False

        await self.db.delete(unternehmen)
        await self.db.commit()
        return True

    async def soft_delete_unternehmen(self, unternehmen_id: str) -> bool:
        """
        Soft-delete a company by setting geloescht_am timestamp.

        Cascades to all associated contacts.

        Returns:
            True if soft-deleted, False if not found
        """
        query = select(ComUnternehmen).where(ComUnternehmen.id == unternehmen_id)
        result = await self.db.execute(query)
        unternehmen = result.scalar_one_or_none()

        if not unternehmen:
            return False

        now = datetime.utcnow()
        unternehmen.geloescht_am = now

        # Cascade: soft-delete all contacts
        kontakt_query = select(ComKontakt).where(
            ComKontakt.unternehmen_id == unternehmen_id,
            ComKontakt.geloescht_am == None,  # noqa: E711
        )
        kontakt_result = await self.db.execute(kontakt_query)
        for kontakt in kontakt_result.scalars().all():
            kontakt.geloescht_am = now

        await self.db.commit()
        return True

    async def restore_unternehmen(self, unternehmen_id: str) -> bool:
        """
        Restore a soft-deleted company by clearing geloescht_am.

        Cascades to all associated contacts.

        Returns:
            True if restored, False if not found
        """
        query = select(ComUnternehmen).where(ComUnternehmen.id == unternehmen_id)
        result = await self.db.execute(query)
        unternehmen = result.scalar_one_or_none()

        if not unternehmen:
            return False

        unternehmen.geloescht_am = None

        # Cascade: restore all contacts
        kontakt_query = select(ComKontakt).where(
            ComKontakt.unternehmen_id == unternehmen_id,
            ComKontakt.geloescht_am != None,  # noqa: E711
        )
        kontakt_result = await self.db.execute(kontakt_query)
        for kontakt in kontakt_result.scalars().all():
            kontakt.geloescht_am = None

        await self.db.commit()
        return True

    async def bulk_soft_delete(self, ids: list[str]) -> dict:
        """
        Soft-delete multiple companies.

        Returns:
            Dict with erfolg (success count) and fehler (error count)
        """
        erfolg = 0
        fehler = 0
        for uid in ids:
            if await self.soft_delete_unternehmen(uid):
                erfolg += 1
            else:
                fehler += 1
        return {"erfolg": erfolg, "fehler": fehler}

    async def bulk_restore(self, ids: list[str]) -> dict:
        """
        Restore multiple soft-deleted companies.

        Returns:
            Dict with erfolg (success count) and fehler (error count)
        """
        erfolg = 0
        fehler = 0
        for uid in ids:
            if await self.restore_unternehmen(uid):
                erfolg += 1
            else:
                fehler += 1
        return {"erfolg": erfolg, "fehler": fehler}

    async def bulk_hard_delete(self, ids: list[str]) -> dict:
        """
        Hard-delete multiple companies (permanent, irreversible).

        Returns:
            Dict with erfolg (success count) and fehler (error count)
        """
        erfolg = 0
        fehler = 0
        for uid in ids:
            if await self.delete_unternehmen(uid):
                erfolg += 1
            else:
                fehler += 1
        return {"erfolg": erfolg, "fehler": fehler}
