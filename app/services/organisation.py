"""
Business logic for Organisation (Unternehmensgruppen) data.

Handles CRUD operations and Unternehmen assignments.
"""
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.com import ComOrganisation, ComUnternehmen, ComUnternehmenOrganisation
from app.models.geo import GeoOrt, GeoKreis, GeoBundesland


class OrganisationService:
    """Service class for Organisation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_organisation_list(
        self,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """
        Get organisations with optional search.

        Args:
            suche: Search in kurzname
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Dict with items and total count
        """
        base_query = select(ComOrganisation)

        if suche:
            search_pattern = f"%{suche}%"
            base_query = base_query.where(
                ComOrganisation.kurzname.ilike(search_pattern)
            )

        # Count query
        count_query = select(func.count(ComOrganisation.id))
        if suche:
            count_query = count_query.where(
                ComOrganisation.kurzname.ilike(f"%{suche}%")
            )
        total = (await self.db.execute(count_query)).scalar()

        # Data query
        query = (
            base_query
            .order_by(ComOrganisation.kurzname)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_organisation_by_id(
        self,
        organisation_id: str,
        include_unternehmen: bool = False
    ) -> ComOrganisation | None:
        """
        Get single Organisation by UUID.

        Args:
            organisation_id: UUID of the organisation
            include_unternehmen: If True, load associated Unternehmen

        Returns:
            ComOrganisation or None
        """
        query = select(ComOrganisation).where(ComOrganisation.id == organisation_id)

        if include_unternehmen:
            query = query.options(
                selectinload(ComOrganisation.unternehmen_zuordnungen)
                .joinedload(ComUnternehmenOrganisation.unternehmen)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_organisation_by_legacy_id(self, legacy_id: int) -> ComOrganisation | None:
        """
        Get Organisation by legacy kStoreGruppe.

        Useful for:
        - Looking up organisations by their original spi_tStoreGruppe key
        - Migration and import verification
        """
        query = select(ComOrganisation).where(ComOrganisation.legacy_id == legacy_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_organisation(
        self,
        kurzname: str,
        legacy_id: int | None = None
    ) -> ComOrganisation:
        """
        Create new Organisation.

        Args:
            kurzname: Name of the organisation
            legacy_id: Optional legacy kStoreGruppe ID

        Returns:
            Created ComOrganisation
        """
        org = ComOrganisation(kurzname=kurzname, legacy_id=legacy_id)
        self.db.add(org)
        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def update_organisation(
        self,
        organisation_id: str,
        kurzname: str | None = None
    ) -> ComOrganisation | None:
        """
        Update Organisation.

        Args:
            organisation_id: UUID of the organisation
            kurzname: New name (optional)

        Returns:
            Updated ComOrganisation or None if not found
        """
        org = await self.get_organisation_by_id(organisation_id)
        if not org:
            return None

        if kurzname is not None:
            org.kurzname = kurzname

        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def delete_organisation(self, organisation_id: str) -> bool:
        """
        Delete Organisation (and all assignments via cascade).

        Args:
            organisation_id: UUID of the organisation

        Returns:
            True if deleted, False if not found
        """
        org = await self.get_organisation_by_id(organisation_id)
        if not org:
            return False

        await self.db.delete(org)
        await self.db.commit()
        return True

    async def assign_unternehmen(
        self,
        organisation_id: str,
        unternehmen_id: str
    ) -> ComUnternehmenOrganisation | None:
        """
        Assign Unternehmen to Organisation.

        Args:
            organisation_id: UUID of the organisation
            unternehmen_id: UUID of the company

        Returns:
            Created assignment or None if duplicate
        """
        # Check if assignment already exists
        existing = await self.db.execute(
            select(ComUnternehmenOrganisation).where(
                ComUnternehmenOrganisation.organisation_id == organisation_id,
                ComUnternehmenOrganisation.unternehmen_id == unternehmen_id,
            )
        )
        if existing.scalar_one_or_none():
            return None  # Already assigned

        assignment = ComUnternehmenOrganisation(
            organisation_id=organisation_id,
            unternehmen_id=unternehmen_id,
        )
        self.db.add(assignment)
        await self.db.commit()
        return assignment

    async def remove_unternehmen(
        self,
        organisation_id: str,
        unternehmen_id: str
    ) -> bool:
        """
        Remove Unternehmen from Organisation.

        Args:
            organisation_id: UUID of the organisation
            unternehmen_id: UUID of the company

        Returns:
            True if removed, False if assignment not found
        """
        result = await self.db.execute(
            delete(ComUnternehmenOrganisation).where(
                ComUnternehmenOrganisation.organisation_id == organisation_id,
                ComUnternehmenOrganisation.unternehmen_id == unternehmen_id,
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_unternehmen_for_organisation(
        self,
        organisation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """
        Get all Unternehmen in an Organisation with full geo hierarchy.

        Args:
            organisation_id: UUID of the organisation
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Dict with items and total count
        """
        base_query = (
            select(ComUnternehmen)
            .join(ComUnternehmenOrganisation)
            .where(ComUnternehmenOrganisation.organisation_id == organisation_id)
            .options(
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
            )
        )

        count_query = (
            select(func.count(ComUnternehmen.id))
            .join(ComUnternehmenOrganisation)
            .where(ComUnternehmenOrganisation.organisation_id == organisation_id)
        )
        total = (await self.db.execute(count_query)).scalar()

        query = (
            base_query
            .order_by(ComUnternehmen.kurzname)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_organisation_count(self) -> int:
        """Get total number of organisations."""
        query = select(func.count(ComOrganisation.id))
        return (await self.db.execute(query)).scalar() or 0

    async def get_unternehmen_count_for_organisation(
        self,
        organisation_id: str
    ) -> int:
        """Get number of Unternehmen in an Organisation."""
        query = (
            select(func.count(ComUnternehmenOrganisation.id))
            .where(ComUnternehmenOrganisation.organisation_id == organisation_id)
        )
        return (await self.db.execute(query)).scalar() or 0
