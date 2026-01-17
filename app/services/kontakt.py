"""
Business logic for Kontakt (contact persons) data.

Handles CRUD operations for contacts belonging to companies.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.com import ComKontakt, ComUnternehmen


class KontaktService:
    """Service class for Kontakt operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_kontakte_for_unternehmen(
        self,
        unternehmen_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """
        Get all contacts for a company.

        Args:
            unternehmen_id: UUID of the company
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            Dict with items and total count
        """
        base_query = select(ComKontakt).where(
            ComKontakt.unternehmen_id == unternehmen_id
        )

        # Count query
        count_query = select(func.count(ComKontakt.id)).where(
            ComKontakt.unternehmen_id == unternehmen_id
        )
        total = (await self.db.execute(count_query)).scalar()

        # Data query with ordering (Hauptkontakt first, then by name)
        query = (
            base_query
            .order_by(
                ComKontakt.ist_hauptkontakt.desc(),
                ComKontakt.nachname,
                ComKontakt.vorname
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_kontakt_by_id(
        self,
        kontakt_id: str,
        unternehmen_id: str | None = None
    ) -> ComKontakt | None:
        """
        Get single Kontakt by UUID.

        Args:
            kontakt_id: UUID of the contact
            unternehmen_id: If provided, ensures contact belongs to this company

        Returns:
            ComKontakt or None
        """
        query = select(ComKontakt).where(ComKontakt.id == kontakt_id)

        if unternehmen_id:
            query = query.where(ComKontakt.unternehmen_id == unternehmen_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_kontakt(
        self,
        unternehmen_id: str,
        vorname: str,
        nachname: str,
        typ: str | None = None,
        titel: str | None = None,
        position: str | None = None,
        abteilung: str | None = None,
        telefon: str | None = None,
        mobil: str | None = None,
        fax: str | None = None,
        email: str | None = None,
        notizen: str | None = None,
        ist_hauptkontakt: bool = False,
        legacy_id: int | None = None
    ) -> ComKontakt:
        """
        Create new Kontakt for a company.

        Args:
            unternehmen_id: UUID of the company
            vorname: First name (required)
            nachname: Last name (required)
            ... other optional fields

        Returns:
            Created ComKontakt
        """
        kontakt = ComKontakt(
            unternehmen_id=unternehmen_id,
            vorname=vorname,
            nachname=nachname,
            typ=typ,
            titel=titel,
            position=position,
            abteilung=abteilung,
            telefon=telefon,
            mobil=mobil,
            fax=fax,
            email=email,
            notizen=notizen,
            ist_hauptkontakt=ist_hauptkontakt,
            legacy_id=legacy_id
        )
        self.db.add(kontakt)
        await self.db.commit()
        await self.db.refresh(kontakt)
        return kontakt

    async def update_kontakt(
        self,
        kontakt_id: str,
        unternehmen_id: str,
        **kwargs
    ) -> ComKontakt | None:
        """
        Update Kontakt with partial data.

        Args:
            kontakt_id: UUID of the contact
            unternehmen_id: UUID of the company (for validation)
            **kwargs: Fields to update

        Returns:
            Updated ComKontakt or None if not found
        """
        kontakt = await self.get_kontakt_by_id(kontakt_id, unternehmen_id)
        if not kontakt:
            return None

        # Update only provided non-None fields
        for field, value in kwargs.items():
            if value is not None and hasattr(kontakt, field):
                setattr(kontakt, field, value)

        await self.db.commit()
        await self.db.refresh(kontakt)
        return kontakt

    async def delete_kontakt(
        self,
        kontakt_id: str,
        unternehmen_id: str
    ) -> bool:
        """
        Delete Kontakt.

        Args:
            kontakt_id: UUID of the contact
            unternehmen_id: UUID of the company (for validation)

        Returns:
            True if deleted, False if not found
        """
        kontakt = await self.get_kontakt_by_id(kontakt_id, unternehmen_id)
        if not kontakt:
            return False

        await self.db.delete(kontakt)
        await self.db.commit()
        return True

    async def get_kontakt_count_for_unternehmen(
        self,
        unternehmen_id: str
    ) -> int:
        """Get number of contacts for a company."""
        query = select(func.count(ComKontakt.id)).where(
            ComKontakt.unternehmen_id == unternehmen_id
        )
        return (await self.db.execute(query)).scalar() or 0

    async def unternehmen_exists(self, unternehmen_id: str) -> bool:
        """Check if Unternehmen exists."""
        query = select(func.count(ComUnternehmen.id)).where(
            ComUnternehmen.id == unternehmen_id
        )
        count = (await self.db.execute(query)).scalar()
        return count > 0
