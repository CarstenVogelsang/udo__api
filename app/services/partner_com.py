"""
Business logic for Partner Company (Unternehmen) API.

Provides filtered access based on partner's assigned countries.
"""
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.com import ComUnternehmen
from app.models.geo import GeoOrt, GeoKreis, GeoBundesland, GeoLand
from app.models.partner import ApiPartner


class PartnerComService:
    """Service class for Partner Company operations with country filtering."""

    def __init__(self, db: AsyncSession, partner: ApiPartner):
        self.db = db
        self.partner = partner

    def _get_base_query(self):
        """
        Build base query with geo hierarchy eager loading.

        Returns query with all necessary joins for geo hierarchy.
        """
        return (
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

    def _apply_country_filter(self, query):
        """
        Apply country filter based on partner's zugelassene_laender_ids.

        If partner has no country restrictions (None or empty list),
        all companies are returned.
        """
        laender_ids = self.partner.zugelassene_laender_ids
        if laender_ids:
            # Join through the geo hierarchy to filter by country
            query = (
                query
                .join(ComUnternehmen.geo_ort)
                .join(GeoOrt.kreis)
                .join(GeoKreis.bundesland)
                .where(GeoBundesland.land_id.in_(laender_ids))
            )
        return query

    def _build_count_query(self):
        """
        Build count query with country filter.
        """
        laender_ids = self.partner.zugelassene_laender_ids
        if laender_ids:
            # Count with country filter
            return (
                select(func.count(ComUnternehmen.id))
                .join(ComUnternehmen.geo_ort)
                .join(GeoOrt.kreis)
                .join(GeoKreis.bundesland)
                .where(GeoBundesland.land_id.in_(laender_ids))
            )
        else:
            # Count all companies
            return select(func.count(ComUnternehmen.id))

    async def get_unternehmen_list(
        self,
        geo_ort_id: str | None = None,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """
        Get companies with full geo hierarchy, filtered by partner's allowed countries.

        Args:
            geo_ort_id: Filter by GeoOrt UUID
            suche: Search in kurzname and firmierung (min 2 chars)
            skip: Pagination offset
            limit: Pagination limit (max 1000)

        Returns:
            Dict with items and total count
        """
        # Base query with eager loading
        base_query = self._get_base_query()

        # Apply country filter
        base_query = self._apply_country_filter(base_query)

        # Apply additional filters
        if geo_ort_id:
            base_query = base_query.where(ComUnternehmen.geo_ort_id == geo_ort_id)
        if suche and len(suche) >= 2:
            search_pattern = f"%{suche}%"
            base_query = base_query.where(
                or_(
                    ComUnternehmen.kurzname.ilike(search_pattern),
                    ComUnternehmen.firmierung.ilike(search_pattern),
                )
            )

        # Count query
        count_query = self._build_count_query()
        if geo_ort_id:
            count_query = count_query.where(ComUnternehmen.geo_ort_id == geo_ort_id)
        if suche and len(suche) >= 2:
            search_pattern = f"%{suche}%"
            count_query = count_query.where(
                or_(
                    ComUnternehmen.kurzname.ilike(search_pattern),
                    ComUnternehmen.firmierung.ilike(search_pattern),
                )
            )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Data query with pagination
        query = (
            base_query
            .order_by(ComUnternehmen.kurzname)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_unternehmen_by_id(self, unternehmen_id: str) -> ComUnternehmen | None:
        """
        Get a single company by UUID with full geo hierarchy.

        Returns None if:
        - Company doesn't exist
        - Company is not in partner's allowed countries
        """
        query = self._get_base_query().where(ComUnternehmen.id == unternehmen_id)
        query = self._apply_country_filter(query)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_unternehmen_count(self) -> int:
        """
        Get total number of companies the partner can access.

        Returns count filtered by partner's allowed countries.
        """
        query = self._build_count_query()
        return (await self.db.execute(query)).scalar() or 0

    def is_country_allowed(self, land_id: str) -> bool:
        """
        Check if a country is in partner's allowed list.

        Args:
            land_id: UUID of the country

        Returns:
            True if allowed or partner has no restrictions
        """
        laender_ids = self.partner.zugelassene_laender_ids
        if not laender_ids:
            return True  # No restrictions
        return land_id in laender_ids
