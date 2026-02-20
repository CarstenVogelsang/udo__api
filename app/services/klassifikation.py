"""
Business logic for UDO Klassifikation (company classification taxonomy).

Handles CRUD operations for classifications and Unternehmen assignments.
"""
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.com import (
    ComKlassifikation,
    ComUnternehmenKlassifikation,
    ComUnternehmen,
)
from app.models.geo import GeoOrt, GeoKreis, GeoBundesland


class KlassifikationService:
    """Service class for UDO Klassifikation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============ Klassifikation CRUD ============

    async def get_klassifikation_list(
        self,
        dimension: str | None = None,
        suche: str | None = None,
        nur_aktiv: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """
        Get classifications with optional filters.

        Args:
            dimension: Filter by dimension (kueche, betriebsart, angebot)
            suche: Search in name_de and slug
            nur_aktiv: Only active classifications
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Dict with items and total count
        """
        base_query = select(ComKlassifikation)

        if dimension:
            base_query = base_query.where(ComKlassifikation.dimension == dimension)

        if nur_aktiv:
            base_query = base_query.where(ComKlassifikation.ist_aktiv == True)  # noqa: E712

        if suche:
            search_pattern = f"%{suche}%"
            base_query = base_query.where(
                (ComKlassifikation.name_de.ilike(search_pattern))
                | (ComKlassifikation.slug.ilike(search_pattern))
            )

        # Count query
        count_query = select(func.count(ComKlassifikation.id))
        if dimension:
            count_query = count_query.where(ComKlassifikation.dimension == dimension)
        if nur_aktiv:
            count_query = count_query.where(ComKlassifikation.ist_aktiv == True)  # noqa: E712
        if suche:
            count_query = count_query.where(
                (ComKlassifikation.name_de.ilike(f"%{suche}%"))
                | (ComKlassifikation.slug.ilike(f"%{suche}%"))
            )
        total = (await self.db.execute(count_query)).scalar()

        # Data query with parent relation
        query = (
            base_query
            .options(joinedload(ComKlassifikation.parent))
            .options(joinedload(ComKlassifikation.google_kategorie))
            .order_by(ComKlassifikation.dimension, ComKlassifikation.name_de)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_klassifikation_by_id(
        self,
        klassifikation_id: str,
    ) -> ComKlassifikation | None:
        """
        Get single Klassifikation by UUID.

        Args:
            klassifikation_id: UUID of the classification

        Returns:
            ComKlassifikation or None
        """
        query = (
            select(ComKlassifikation)
            .where(ComKlassifikation.id == klassifikation_id)
            .options(joinedload(ComKlassifikation.parent))
            .options(joinedload(ComKlassifikation.google_kategorie))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_klassifikation_by_slug(
        self,
        slug: str,
    ) -> ComKlassifikation | None:
        """
        Get Klassifikation by slug.

        Args:
            slug: Unique slug (e.g. "doener_imbiss")

        Returns:
            ComKlassifikation or None
        """
        query = (
            select(ComKlassifikation)
            .where(ComKlassifikation.slug == slug)
            .options(joinedload(ComKlassifikation.parent))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_klassifikation(
        self,
        slug: str,
        name_de: str,
        dimension: str | None = None,
        beschreibung: str | None = None,
        google_mapping_gcid: str | None = None,
        parent_id: str | None = None,
    ) -> ComKlassifikation:
        """
        Create new Klassifikation.

        Args:
            slug: Unique identifier (lowercase, underscore)
            name_de: German display name
            dimension: Category dimension (kueche, betriebsart, angebot)
            beschreibung: Optional description
            google_mapping_gcid: Optional Google category mapping
            parent_id: Optional parent classification UUID

        Returns:
            Created ComKlassifikation
        """
        klassifikation = ComKlassifikation(
            slug=slug,
            name_de=name_de,
            dimension=dimension,
            beschreibung=beschreibung,
            google_mapping_gcid=google_mapping_gcid,
            parent_id=parent_id,
        )
        self.db.add(klassifikation)
        await self.db.commit()
        await self.db.refresh(klassifikation)
        return klassifikation

    async def update_klassifikation(
        self,
        klassifikation_id: str,
        slug: str | None = None,
        name_de: str | None = None,
        dimension: str | None = None,
        beschreibung: str | None = None,
        google_mapping_gcid: str | None = None,
        parent_id: str | None = None,
        ist_aktiv: bool | None = None,
    ) -> ComKlassifikation | None:
        """
        Update Klassifikation.

        Args:
            klassifikation_id: UUID of the classification
            ... (all fields optional)

        Returns:
            Updated ComKlassifikation or None if not found
        """
        klass = await self.get_klassifikation_by_id(klassifikation_id)
        if not klass:
            return None

        if slug is not None:
            klass.slug = slug
        if name_de is not None:
            klass.name_de = name_de
        if dimension is not None:
            klass.dimension = dimension
        if beschreibung is not None:
            klass.beschreibung = beschreibung
        if google_mapping_gcid is not None:
            klass.google_mapping_gcid = google_mapping_gcid
        if parent_id is not None:
            klass.parent_id = parent_id
        if ist_aktiv is not None:
            klass.ist_aktiv = ist_aktiv

        await self.db.commit()
        await self.db.refresh(klass)
        return klass

    async def delete_klassifikation(self, klassifikation_id: str) -> bool:
        """
        Delete Klassifikation (and all assignments via cascade).

        Args:
            klassifikation_id: UUID of the classification

        Returns:
            True if deleted, False if not found
        """
        klass = await self.get_klassifikation_by_id(klassifikation_id)
        if not klass:
            return False

        await self.db.delete(klass)
        await self.db.commit()
        return True

    # ============ Unternehmen Assignments ============

    async def get_klassifikationen_for_unternehmen(
        self,
        unternehmen_id: str,
    ) -> list[ComUnternehmenKlassifikation]:
        """
        Get all classifications assigned to an Unternehmen.

        Args:
            unternehmen_id: UUID of the company

        Returns:
            List of ComUnternehmenKlassifikation with nested klassifikation
        """
        query = (
            select(ComUnternehmenKlassifikation)
            .where(ComUnternehmenKlassifikation.unternehmen_id == unternehmen_id)
            .options(
                joinedload(ComUnternehmenKlassifikation.klassifikation)
                .joinedload(ComKlassifikation.google_kategorie)
            )
            .order_by(ComUnternehmenKlassifikation.ist_primaer.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def assign_klassifikation(
        self,
        unternehmen_id: str,
        klassifikation_id: str,
        ist_primaer: bool = False,
        quelle: str = "manuell",
    ) -> ComUnternehmenKlassifikation | None:
        """
        Assign Klassifikation to Unternehmen.

        Args:
            unternehmen_id: UUID of the company
            klassifikation_id: UUID of the classification
            ist_primaer: Mark as primary for this dimension
            quelle: Source of assignment (manuell, regel, ki)

        Returns:
            Created assignment or None if duplicate
        """
        # Check if assignment already exists
        existing = await self.db.execute(
            select(ComUnternehmenKlassifikation).where(
                ComUnternehmenKlassifikation.unternehmen_id == unternehmen_id,
                ComUnternehmenKlassifikation.klassifikation_id == klassifikation_id,
            )
        )
        if existing.scalar_one_or_none():
            return None  # Already assigned

        assignment = ComUnternehmenKlassifikation(
            unternehmen_id=unternehmen_id,
            klassifikation_id=klassifikation_id,
            ist_primaer=ist_primaer,
            quelle=quelle,
        )
        self.db.add(assignment)
        await self.db.commit()

        # Reload with joined data
        await self.db.refresh(assignment)
        return assignment

    async def remove_klassifikation(
        self,
        unternehmen_id: str,
        klassifikation_id: str,
    ) -> bool:
        """
        Remove Klassifikation from Unternehmen.

        Args:
            unternehmen_id: UUID of the company
            klassifikation_id: UUID of the classification

        Returns:
            True if removed, False if assignment not found
        """
        result = await self.db.execute(
            delete(ComUnternehmenKlassifikation).where(
                ComUnternehmenKlassifikation.unternehmen_id == unternehmen_id,
                ComUnternehmenKlassifikation.klassifikation_id == klassifikation_id,
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_unternehmen_for_klassifikation(
        self,
        klassifikation_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """
        Get all Unternehmen with a specific Klassifikation.

        Args:
            klassifikation_id: UUID of the classification
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Dict with items and total count
        """
        base_query = (
            select(ComUnternehmen)
            .join(ComUnternehmenKlassifikation)
            .where(ComUnternehmenKlassifikation.klassifikation_id == klassifikation_id)
            .where(ComUnternehmen.geloescht_am.is_(None))
            .options(
                joinedload(ComUnternehmen.geo_ort)
                .joinedload(GeoOrt.kreis)
                .joinedload(GeoKreis.bundesland)
                .joinedload(GeoBundesland.land),
            )
        )

        count_query = (
            select(func.count(ComUnternehmen.id))
            .join(ComUnternehmenKlassifikation)
            .where(ComUnternehmenKlassifikation.klassifikation_id == klassifikation_id)
            .where(ComUnternehmen.geloescht_am.is_(None))
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

    # ============ Stats ============

    async def get_klassifikation_count(self, nur_aktiv: bool = True) -> int:
        """Get total number of classifications."""
        query = select(func.count(ComKlassifikation.id))
        if nur_aktiv:
            query = query.where(ComKlassifikation.ist_aktiv == True)  # noqa: E712
        return (await self.db.execute(query)).scalar() or 0

    async def get_dimensions(self) -> list[str]:
        """Get all unique dimension values."""
        query = (
            select(ComKlassifikation.dimension)
            .where(ComKlassifikation.dimension.isnot(None))
            .where(ComKlassifikation.ist_aktiv == True)  # noqa: E712
            .distinct()
            .order_by(ComKlassifikation.dimension)
        )
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]
