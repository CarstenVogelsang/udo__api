"""
Business logic and database queries for Company (Unternehmen) data.
"""
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.com import ComUnternehmen
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
        limit: int = 100
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

        # Count query
        count_query = select(func.count(ComUnternehmen.id))
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
        total = (await self.db.execute(count_query)).scalar()

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

        return {"items": items, "total": total}

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
