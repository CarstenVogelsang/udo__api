"""
Business logic and database queries for Product (Produktdaten) data.
"""
from datetime import datetime

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prod import (
    ProdArtikel,
    ProdArtikelBild,
    ProdArtikelEigenschaft,
    ProdArtikelSortiment,
    ProdEigenschaft,
    ProdKategorie,
    ProdSortiment,
    ProdSortimentEigenschaft,
    ProdWerteliste,
)


class ProdService:
    """Service class for Product CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== Artikel CRUD ==========

    async def get_artikel_list(
        self,
        hersteller_id: str | None = None,
        marke_id: str | None = None,
        kategorie_id: str | None = None,
        sortiment_code: str | None = None,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """Get paginated article list with filters."""
        base_query = select(ProdArtikel).where(
            ProdArtikel.geloescht_am == None  # noqa: E711
        )

        # Apply filters
        if hersteller_id:
            base_query = base_query.where(ProdArtikel.hersteller_id == hersteller_id)
        if marke_id:
            base_query = base_query.where(ProdArtikel.marke_id == marke_id)
        if kategorie_id:
            base_query = base_query.where(ProdArtikel.kategorie_id == kategorie_id)
        if sortiment_code:
            base_query = base_query.join(
                ProdArtikelSortiment,
                ProdArtikelSortiment.artikel_id == ProdArtikel.id,
            ).join(
                ProdSortiment,
                ProdSortiment.id == ProdArtikelSortiment.sortiment_id,
            ).where(ProdSortiment.code == sortiment_code)
        if suche:
            pattern = f"%{suche}%"
            base_query = base_query.where(
                or_(
                    ProdArtikel.bezeichnung.ilike(pattern),
                    ProdArtikel.artikelnummer_hersteller.ilike(pattern),
                    ProdArtikel.ean_gtin.ilike(pattern),
                )
            )

        # Count
        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_q)).scalar()

        # Data
        query = (
            base_query
            .order_by(ProdArtikel.bezeichnung)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {
            "items": items,
            "total": total,
            "page": (skip // limit) + 1,
            "page_size": limit,
        }

    async def get_artikel_by_id(self, artikel_id: str) -> ProdArtikel | None:
        """Get single article with all relations (selectin loaded)."""
        query = select(ProdArtikel).where(ProdArtikel.id == artikel_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_artikel(self, **kwargs) -> ProdArtikel:
        """Create a new article."""
        artikel = ProdArtikel(**kwargs)
        self.db.add(artikel)
        await self.db.flush()
        await self.db.refresh(artikel)
        return await self.get_artikel_by_id(str(artikel.id))

    async def update_artikel(self, artikel_id: str, **kwargs) -> ProdArtikel | None:
        """Update existing article (partial update)."""
        query = select(ProdArtikel).where(ProdArtikel.id == artikel_id)
        result = await self.db.execute(query)
        artikel = result.scalar_one_or_none()

        if not artikel:
            return None

        for key, value in kwargs.items():
            if hasattr(artikel, key):
                setattr(artikel, key, value)

        await self.db.flush()
        return await self.get_artikel_by_id(artikel_id)

    async def soft_delete_artikel(self, artikel_id: str) -> bool:
        """Soft-delete an article."""
        query = select(ProdArtikel).where(ProdArtikel.id == artikel_id)
        result = await self.db.execute(query)
        artikel = result.scalar_one_or_none()

        if not artikel:
            return False

        artikel.geloescht_am = datetime.utcnow()
        await self.db.flush()
        return True

    # ========== Sortiment-Zuordnung ==========

    async def assign_sortiment(self, artikel_id: str, sortiment_code: str) -> bool:
        """Assign a sortiment to an article."""
        sortiment = await self._get_sortiment_by_code(sortiment_code)
        if not sortiment:
            return False

        # Check if already assigned
        existing = await self.db.execute(
            select(ProdArtikelSortiment).where(
                ProdArtikelSortiment.artikel_id == artikel_id,
                ProdArtikelSortiment.sortiment_id == sortiment.id,
            )
        )
        if existing.scalar_one_or_none():
            return True  # Already assigned

        zuordnung = ProdArtikelSortiment(
            artikel_id=artikel_id,
            sortiment_id=sortiment.id,
        )
        self.db.add(zuordnung)
        await self.db.flush()
        return True

    async def remove_sortiment(self, artikel_id: str, sortiment_code: str) -> bool:
        """Remove a sortiment from an article."""
        sortiment = await self._get_sortiment_by_code(sortiment_code)
        if not sortiment:
            return False

        result = await self.db.execute(
            select(ProdArtikelSortiment).where(
                ProdArtikelSortiment.artikel_id == artikel_id,
                ProdArtikelSortiment.sortiment_id == sortiment.id,
            )
        )
        zuordnung = result.scalar_one_or_none()
        if not zuordnung:
            return False

        await self.db.delete(zuordnung)
        await self.db.flush()
        return True

    # ========== Eigenschaften (EAV) ==========

    async def get_artikel_eigenschaften(self, artikel_id: str) -> list:
        """Get all property values for an article."""
        result = await self.db.execute(
            select(ProdArtikelEigenschaft).where(
                ProdArtikelEigenschaft.artikel_id == artikel_id
            )
        )
        return list(result.scalars().all())

    async def set_artikel_eigenschaften(
        self, artikel_id: str, eigenschaften: list[dict]
    ) -> list:
        """Bulk set property values for an article.

        Each dict: {eigenschaft_code, wert_text, wert_ganzzahl, wert_dezimal, wert_bool}
        """
        results = []

        for item in eigenschaften:
            eigenschaft_code = item.pop("eigenschaft_code")

            # Lookup eigenschaft by code
            eig_result = await self.db.execute(
                select(ProdEigenschaft).where(ProdEigenschaft.code == eigenschaft_code)
            )
            eigenschaft = eig_result.scalar_one_or_none()
            if not eigenschaft:
                continue

            # Upsert: check existing
            existing_result = await self.db.execute(
                select(ProdArtikelEigenschaft).where(
                    ProdArtikelEigenschaft.artikel_id == artikel_id,
                    ProdArtikelEigenschaft.eigenschaft_id == eigenschaft.id,
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.wert_text = item.get("wert_text")
                existing.wert_ganzzahl = item.get("wert_ganzzahl")
                existing.wert_dezimal = item.get("wert_dezimal")
                existing.wert_bool = item.get("wert_bool")
                results.append(existing)
            else:
                ae = ProdArtikelEigenschaft(
                    artikel_id=artikel_id,
                    eigenschaft_id=eigenschaft.id,
                    wert_text=item.get("wert_text"),
                    wert_ganzzahl=item.get("wert_ganzzahl"),
                    wert_dezimal=item.get("wert_dezimal"),
                    wert_bool=item.get("wert_bool"),
                )
                self.db.add(ae)
                results.append(ae)

        await self.db.flush()
        return results

    # ========== Bilder ==========

    async def add_bild(self, artikel_id: str, **kwargs) -> ProdArtikelBild:
        """Add an image to an article."""
        bild = ProdArtikelBild(artikel_id=artikel_id, **kwargs)
        self.db.add(bild)
        await self.db.flush()
        await self.db.refresh(bild)
        return bild

    async def remove_bild(self, artikel_id: str, bild_id: str) -> bool:
        """Remove an image from an article."""
        result = await self.db.execute(
            select(ProdArtikelBild).where(
                ProdArtikelBild.id == bild_id,
                ProdArtikelBild.artikel_id == artikel_id,
            )
        )
        bild = result.scalar_one_or_none()
        if not bild:
            return False

        await self.db.delete(bild)
        await self.db.flush()
        return True

    # ========== Stammdaten (Read-Only Lookups) ==========

    async def get_sortimente(self) -> list:
        """Get all sortimente with eigenschaft blueprints."""
        result = await self.db.execute(
            select(ProdSortiment).order_by(ProdSortiment.sortierung)
        )
        return list(result.scalars().unique().all())

    async def get_sortiment_eigenschaften(self, sortiment_code: str) -> list:
        """Get blueprint: all eigenschaft definitions for a sortiment."""
        result = await self.db.execute(
            select(ProdSortimentEigenschaft)
            .join(ProdSortiment, ProdSortiment.id == ProdSortimentEigenschaft.sortiment_id)
            .where(ProdSortiment.code == sortiment_code)
            .order_by(ProdSortimentEigenschaft.sortierung)
        )
        return list(result.scalars().all())

    async def get_eigenschaften(self) -> list:
        """Get all eigenschaft definitions."""
        result = await self.db.execute(
            select(ProdEigenschaft).order_by(ProdEigenschaft.sortierung)
        )
        return list(result.scalars().all())

    async def get_kategorien(self, parent_id: str | None = None) -> list:
        """Get categories, optionally filtered by parent."""
        query = select(ProdKategorie).where(ProdKategorie.ist_aktiv == True)  # noqa: E712
        if parent_id is None:
            query = query.where(ProdKategorie.parent_id == None)  # noqa: E711
        else:
            query = query.where(ProdKategorie.parent_id == parent_id)
        query = query.order_by(ProdKategorie.sortierung, ProdKategorie.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_kategorie(self, **kwargs) -> ProdKategorie:
        """Create a new category."""
        kategorie = ProdKategorie(**kwargs)
        self.db.add(kategorie)
        await self.db.flush()
        await self.db.refresh(kategorie)
        return kategorie

    async def get_werteliste(self, typ: str) -> list:
        """Get all entries for a werteliste type."""
        result = await self.db.execute(
            select(ProdWerteliste)
            .where(ProdWerteliste.typ == typ, ProdWerteliste.ist_aktiv == True)  # noqa: E712
            .order_by(ProdWerteliste.sortierung)
        )
        return list(result.scalars().all())

    async def create_werteliste_entry(self, typ: str, **kwargs) -> ProdWerteliste:
        """Create a new werteliste entry."""
        entry = ProdWerteliste(typ=typ, **kwargs)
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    # ========== Internal Helpers ==========

    async def _get_sortiment_by_code(self, code: str) -> ProdSortiment | None:
        """Lookup sortiment by code."""
        result = await self.db.execute(
            select(ProdSortiment).where(ProdSortiment.code == code)
        )
        return result.scalar_one_or_none()
