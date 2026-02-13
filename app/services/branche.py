"""
Business logic and database queries for Branchenklassifikation.
"""
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.branche import (
    BrnBranche,
    BrnVerzeichnis,
    BrnRegionaleGruppe,
    BrnGoogleKategorie,
    BrnGoogleMapping,
    BrnKostenModell,
    BrnGruppenPlattform,
)


class BranchenService:
    """Service class for Branchenklassifikation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============ Branchen (WZ-Codes) ============

    async def get_branchen(
        self,
        ebene: int | None = None,
        suche: str | None = None,
        nur_aktiv: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """Get WZ codes with optional filters."""
        base_query = select(BrnBranche)
        count_query = select(func.count(BrnBranche.id))

        if nur_aktiv:
            base_query = base_query.where(BrnBranche.ist_aktiv.is_(True))
            count_query = count_query.where(BrnBranche.ist_aktiv.is_(True))

        if ebene is not None:
            base_query = base_query.where(BrnBranche.ebene == ebene)
            count_query = count_query.where(BrnBranche.ebene == ebene)

        if suche:
            search_filter = or_(
                BrnBranche.wz_code.ilike(f"%{suche}%"),
                BrnBranche.bezeichnung.ilike(f"%{suche}%"),
            )
            base_query = base_query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = (await self.db.execute(count_query)).scalar()

        query = base_query.order_by(BrnBranche.wz_code).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_branche_by_wz_code(self, wz_code: str) -> BrnBranche | None:
        """Get a single WZ code with details."""
        query = select(BrnBranche).where(BrnBranche.wz_code == wz_code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_kinder(self, wz_code: str) -> list[BrnBranche]:
        """Get child categories (direct subcategories)."""
        query = (
            select(BrnBranche)
            .where(BrnBranche.parent_wz_code == wz_code)
            .where(BrnBranche.ist_aktiv.is_(True))
            .order_by(BrnBranche.wz_code)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============ Verzeichnisse ============

    async def get_verzeichnisse_fuer_branche(
        self,
        wz_code: str,
        region: str | None = None,
        kosten: str | None = None,
    ) -> list[BrnVerzeichnis]:
        """Get directories for a WZ code (always includes cross-industry ones).

        Results are sorted by relevanz_score DESC.
        """
        query = (
            select(BrnVerzeichnis)
            .where(BrnVerzeichnis.ist_aktiv.is_(True))
            .where(
                or_(
                    BrnVerzeichnis.branche_wz_code == wz_code,
                    BrnVerzeichnis.ist_branchenuebergreifend.is_(True),
                )
            )
        )

        if region:
            query = query.where(BrnVerzeichnis.regionen.contains([region]))

        if kosten:
            query = query.where(BrnVerzeichnis.kosten == kosten)

        query = query.order_by(BrnVerzeichnis.relevanz_score.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_alle_verzeichnisse(
        self,
        branchenuebergreifend: bool | None = None,
        kosten: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """Get all directories with optional filters."""
        base_query = select(BrnVerzeichnis).where(BrnVerzeichnis.ist_aktiv.is_(True))
        count_query = select(func.count(BrnVerzeichnis.id)).where(BrnVerzeichnis.ist_aktiv.is_(True))

        if branchenuebergreifend is not None:
            base_query = base_query.where(
                BrnVerzeichnis.ist_branchenuebergreifend.is_(branchenuebergreifend)
            )
            count_query = count_query.where(
                BrnVerzeichnis.ist_branchenuebergreifend.is_(branchenuebergreifend)
            )

        if kosten:
            base_query = base_query.where(BrnVerzeichnis.kosten == kosten)
            count_query = count_query.where(BrnVerzeichnis.kosten == kosten)

        total = (await self.db.execute(count_query)).scalar()

        query = (
            base_query
            .order_by(BrnVerzeichnis.relevanz_score.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    # ============ Regionale Gruppen ============

    async def get_gruppen_fuer_branche(
        self,
        wz_code: str,
        plz_prefix: str | None = None,
        plattform: str | None = None,
        werbung_erlaubt: bool | None = None,
    ) -> list[BrnRegionaleGruppe]:
        """Get regional groups for a WZ code."""
        query = (
            select(BrnRegionaleGruppe)
            .where(BrnRegionaleGruppe.ist_aktiv.is_(True))
            .where(BrnRegionaleGruppe.branche_wz_code == wz_code)
        )

        if plz_prefix:
            query = query.where(BrnRegionaleGruppe.region_plz_prefix == plz_prefix)

        if plattform:
            query = query.where(BrnRegionaleGruppe.plattform == plattform)

        if werbung_erlaubt is not None:
            query = query.where(BrnRegionaleGruppe.werbung_erlaubt.is_(werbung_erlaubt))

        query = query.order_by(BrnRegionaleGruppe.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_alle_gruppen(
        self,
        bundesland: str | None = None,
        plattform: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """Get all regional groups with optional filters."""
        base_query = select(BrnRegionaleGruppe).where(BrnRegionaleGruppe.ist_aktiv.is_(True))
        count_query = select(func.count(BrnRegionaleGruppe.id)).where(
            BrnRegionaleGruppe.ist_aktiv.is_(True)
        )

        if bundesland:
            base_query = base_query.where(BrnRegionaleGruppe.region_bundesland == bundesland)
            count_query = count_query.where(BrnRegionaleGruppe.region_bundesland == bundesland)

        if plattform:
            base_query = base_query.where(BrnRegionaleGruppe.plattform == plattform)
            count_query = count_query.where(BrnRegionaleGruppe.plattform == plattform)

        total = (await self.db.execute(count_query)).scalar()

        query = base_query.order_by(BrnRegionaleGruppe.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    # ============ Google-Kategorien ============

    async def get_google_kategorien(
        self,
        suche: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """Get Google categories with optional text search."""
        base_query = select(BrnGoogleKategorie).where(BrnGoogleKategorie.ist_aktiv.is_(True))
        count_query = select(func.count(BrnGoogleKategorie.id)).where(
            BrnGoogleKategorie.ist_aktiv.is_(True)
        )

        if suche:
            search_filter = or_(
                BrnGoogleKategorie.gcid.ilike(f"%{suche}%"),
                BrnGoogleKategorie.name_de.ilike(f"%{suche}%"),
                BrnGoogleKategorie.name_en.ilike(f"%{suche}%"),
            )
            base_query = base_query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = (await self.db.execute(count_query)).scalar()

        query = base_query.order_by(BrnGoogleKategorie.name_de).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_google_kategorie_by_gcid(self, gcid: str) -> BrnGoogleKategorie | None:
        """Get a single Google category by GCID."""
        query = select(BrnGoogleKategorie).where(BrnGoogleKategorie.gcid == gcid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_google_kategorien_fuer_branche(
        self,
        wz_code: str,
        nur_primaer: bool = False,
    ) -> list[BrnGoogleMapping]:
        """Get Google category mappings for a WZ code."""
        query = (
            select(BrnGoogleMapping)
            .options(joinedload(BrnGoogleMapping.google_kategorie))
            .where(BrnGoogleMapping.wz_code == wz_code)
        )

        if nur_primaer:
            query = query.where(BrnGoogleMapping.ist_primaer.is_(True))

        query = query.order_by(BrnGoogleMapping.relevanz.desc())
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())
