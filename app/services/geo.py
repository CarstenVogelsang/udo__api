"""
Business logic and database queries for Geodata.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.geo import (
    GeoLand,
    GeoBundesland,
    GeoRegierungsbezirk,
    GeoKreis,
    GeoOrt,
    GeoOrtsteil,
)


class GeoService:
    """Service class for Geodata operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============ Länder ============

    async def get_laender(self, skip: int = 0, limit: int = 100) -> dict:
        """Get all countries."""
        # Count
        count_query = select(func.count(GeoLand.id))
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = (
            select(GeoLand)
            .order_by(GeoLand.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_land_by_id(self, land_id: str) -> GeoLand | None:
        """Get a single country by ID."""
        query = select(GeoLand).where(GeoLand.id == land_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_land_by_code(self, code: str) -> GeoLand | None:
        """Get a single country by code (e.g. 'DE')."""
        query = select(GeoLand).where(GeoLand.code == code.upper())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============ Bundesländer ============

    async def get_bundeslaender(
        self,
        land_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get federal states, optionally filtered by country."""
        # Base query with eager loading of parent
        base_query = select(GeoBundesland).options(joinedload(GeoBundesland.land))

        if land_id:
            base_query = base_query.where(GeoBundesland.land_id == land_id)

        # Count
        count_query = select(func.count(GeoBundesland.id))
        if land_id:
            count_query = count_query.where(GeoBundesland.land_id == land_id)
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(GeoBundesland.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_bundesland_by_id(self, bundesland_id: str) -> GeoBundesland | None:
        """Get a single federal state by ID with parent."""
        query = (
            select(GeoBundesland)
            .options(joinedload(GeoBundesland.land))
            .where(GeoBundesland.id == bundesland_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_bundesland_by_code(self, code: str) -> GeoBundesland | None:
        """Get a single federal state by code (e.g. 'DE-BY')."""
        query = (
            select(GeoBundesland)
            .options(joinedload(GeoBundesland.land))
            .where(GeoBundesland.code == code.upper())
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============ Regierungsbezirke ============

    async def get_regierungsbezirke(
        self,
        bundesland_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get government districts."""
        base_query = (
            select(GeoRegierungsbezirk)
            .options(
                joinedload(GeoRegierungsbezirk.bundesland)
                .joinedload(GeoBundesland.land)
            )
        )

        if bundesland_id:
            base_query = base_query.where(GeoRegierungsbezirk.bundesland_id == bundesland_id)

        # Count
        count_query = select(func.count(GeoRegierungsbezirk.id))
        if bundesland_id:
            count_query = count_query.where(GeoRegierungsbezirk.bundesland_id == bundesland_id)
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(GeoRegierungsbezirk.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_regierungsbezirk_by_id(self, regbez_id: str) -> GeoRegierungsbezirk | None:
        """Get a single government district by ID."""
        query = (
            select(GeoRegierungsbezirk)
            .options(
                joinedload(GeoRegierungsbezirk.bundesland)
                .joinedload(GeoBundesland.land)
            )
            .where(GeoRegierungsbezirk.id == regbez_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============ Kreise ============

    async def get_kreise(
        self,
        bundesland_id: str | None = None,
        regierungsbezirk_id: str | None = None,
        autokennzeichen: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get counties with full parent hierarchy."""
        base_query = (
            select(GeoKreis)
            .options(
                joinedload(GeoKreis.bundesland).joinedload(GeoBundesland.land),
                joinedload(GeoKreis.regierungsbezirk),
            )
        )

        if bundesland_id:
            base_query = base_query.where(GeoKreis.bundesland_id == bundesland_id)
        if regierungsbezirk_id:
            base_query = base_query.where(GeoKreis.regierungsbezirk_id == regierungsbezirk_id)
        if autokennzeichen:
            base_query = base_query.where(GeoKreis.autokennzeichen == autokennzeichen.upper())

        # Count
        count_query = select(func.count(GeoKreis.id))
        if bundesland_id:
            count_query = count_query.where(GeoKreis.bundesland_id == bundesland_id)
        if regierungsbezirk_id:
            count_query = count_query.where(GeoKreis.regierungsbezirk_id == regierungsbezirk_id)
        if autokennzeichen:
            count_query = count_query.where(GeoKreis.autokennzeichen == autokennzeichen.upper())
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(GeoKreis.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_kreis_by_id(self, kreis_id: str) -> GeoKreis | None:
        """Get a single county by ID with full hierarchy."""
        query = (
            select(GeoKreis)
            .options(
                joinedload(GeoKreis.bundesland).joinedload(GeoBundesland.land),
                joinedload(GeoKreis.regierungsbezirk),
            )
            .where(GeoKreis.id == kreis_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_kreis_by_ags(self, ags: str) -> GeoKreis | None:
        """Get a single county by AGS code."""
        query = (
            select(GeoKreis)
            .options(
                joinedload(GeoKreis.bundesland).joinedload(GeoBundesland.land),
                joinedload(GeoKreis.regierungsbezirk),
            )
            .where(GeoKreis.ags == ags)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============ Orte ============

    async def get_orte(
        self,
        kreis_id: str | None = None,
        plz: str | None = None,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get cities/municipalities with full parent hierarchy."""
        base_query = (
            select(GeoOrt)
            .options(
                joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
                joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.regierungsbezirk),
            )
        )

        if kreis_id:
            base_query = base_query.where(GeoOrt.kreis_id == kreis_id)
        if plz:
            base_query = base_query.where(GeoOrt.plz == plz)
        if suche:
            base_query = base_query.where(GeoOrt.name.ilike(f"%{suche}%"))

        # Count
        count_query = select(func.count(GeoOrt.id))
        if kreis_id:
            count_query = count_query.where(GeoOrt.kreis_id == kreis_id)
        if plz:
            count_query = count_query.where(GeoOrt.plz == plz)
        if suche:
            count_query = count_query.where(GeoOrt.name.ilike(f"%{suche}%"))
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(GeoOrt.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_ort_by_id(self, ort_id: str) -> GeoOrt | None:
        """Get a single city by ID with full hierarchy."""
        query = (
            select(GeoOrt)
            .options(
                joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
                joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.regierungsbezirk),
            )
            .where(GeoOrt.id == ort_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============ Ortsteile ============

    async def get_ortsteile(
        self,
        ort_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get city districts with full parent hierarchy."""
        base_query = (
            select(GeoOrtsteil)
            .options(
                joinedload(GeoOrtsteil.ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
                joinedload(GeoOrtsteil.ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.regierungsbezirk),
            )
        )

        if ort_id:
            base_query = base_query.where(GeoOrtsteil.ort_id == ort_id)

        # Count
        count_query = select(func.count(GeoOrtsteil.id))
        if ort_id:
            count_query = count_query.where(GeoOrtsteil.ort_id == ort_id)
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = base_query.order_by(GeoOrtsteil.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_ortsteil_by_id(self, ortsteil_id: str) -> GeoOrtsteil | None:
        """Get a single city district by ID with full hierarchy."""
        query = (
            select(GeoOrtsteil)
            .options(
                joinedload(GeoOrtsteil.ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
                joinedload(GeoOrtsteil.ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.regierungsbezirk),
            )
            .where(GeoOrtsteil.id == ortsteil_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
