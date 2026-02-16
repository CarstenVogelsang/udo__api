#!/usr/bin/env python3
"""
Seed script for Produktdaten controlled vocabularies.

Loads sortimente, eigenschaften, sortiment-blueprints,
and wertelisten from JSON seed data.

Idempotent: existing entries are updated, new ones created.

Usage:
    uv run python scripts/seed_prod_wertelisten.py
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import init_db, async_session_maker
from app.models.geo import generate_uuid
from app.models.prod import (
    ProdWerteliste,
    ProdSortiment,
    ProdEigenschaft,
    ProdSortimentEigenschaft,
)

SEED_DIR = Path(__file__).parent.parent / "seed"


def load_json(filename: str) -> dict:
    """Load a JSON seed file."""
    filepath = SEED_DIR / filename
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


async def seed_sortimente(db, data: list) -> tuple[int, int]:
    """Seed product sortimente (Moba, Sammler, ...)."""
    created, updated = 0, 0

    for item in data:
        result = await db.execute(
            select(ProdSortiment).where(ProdSortiment.code == item["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = item["name"]
            existing.beschreibung = item.get("beschreibung")
            existing.sortierung = item.get("sortierung", 0)
            updated += 1
        else:
            sortiment = ProdSortiment(
                id=generate_uuid(),
                code=item["code"],
                name=item["name"],
                beschreibung=item.get("beschreibung"),
                sortierung=item.get("sortierung", 0),
            )
            db.add(sortiment)
            created += 1

    return created, updated


async def seed_eigenschaften(db, data: list) -> tuple[int, int]:
    """Seed property definitions (Spurweite, Epoche, Material, ...)."""
    created, updated = 0, 0

    for item in data:
        result = await db.execute(
            select(ProdEigenschaft).where(ProdEigenschaft.code == item["code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = item["name"]
            existing.daten_typ = item["daten_typ"]
            existing.werteliste_typ = item.get("werteliste_typ")
            existing.einheit = item.get("einheit")
            existing.ist_pflicht = item.get("ist_pflicht", False)
            existing.sortierung = item.get("sortierung", 0)
            updated += 1
        else:
            eigenschaft = ProdEigenschaft(
                id=generate_uuid(),
                code=item["code"],
                name=item["name"],
                daten_typ=item["daten_typ"],
                werteliste_typ=item.get("werteliste_typ"),
                einheit=item.get("einheit"),
                ist_pflicht=item.get("ist_pflicht", False),
                sortierung=item.get("sortierung", 0),
            )
            db.add(eigenschaft)
            created += 1

    return created, updated


async def seed_blueprints(db, blueprints: dict) -> tuple[int, int]:
    """Seed sortiment-eigenschaft blueprints (which properties belong to which sortiment)."""
    created, updated = 0, 0

    for sortiment_code, eigenschaft_codes in blueprints.items():
        # Lookup sortiment by code
        result = await db.execute(
            select(ProdSortiment).where(ProdSortiment.code == sortiment_code)
        )
        sortiment = result.scalar_one_or_none()
        if not sortiment:
            print(f"   WARNUNG: Sortiment '{sortiment_code}' nicht gefunden, überspringe.")
            continue

        for idx, eigenschaft_code in enumerate(eigenschaft_codes):
            # Lookup eigenschaft by code
            result = await db.execute(
                select(ProdEigenschaft).where(ProdEigenschaft.code == eigenschaft_code)
            )
            eigenschaft = result.scalar_one_or_none()
            if not eigenschaft:
                print(f"   WARNUNG: Eigenschaft '{eigenschaft_code}' nicht gefunden, überspringe.")
                continue

            # Check if blueprint exists
            result = await db.execute(
                select(ProdSortimentEigenschaft).where(
                    ProdSortimentEigenschaft.sortiment_id == sortiment.id,
                    ProdSortimentEigenschaft.eigenschaft_id == eigenschaft.id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.sortierung = idx + 1
                updated += 1
            else:
                blueprint = ProdSortimentEigenschaft(
                    id=generate_uuid(),
                    sortiment_id=sortiment.id,
                    eigenschaft_id=eigenschaft.id,
                    sortierung=idx + 1,
                )
                db.add(blueprint)
                created += 1

    return created, updated


async def seed_wertelisten(db, wertelisten: dict) -> tuple[int, int]:
    """Seed controlled vocabulary entries (Spurweite, Epoche, ...)."""
    created, updated = 0, 0

    for typ, entries in wertelisten.items():
        for item in entries:
            result = await db.execute(
                select(ProdWerteliste).where(
                    ProdWerteliste.typ == typ,
                    ProdWerteliste.code == item["code"],
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.bezeichnung = item["bezeichnung"]
                existing.sortierung = item.get("sortierung", 0)
                existing.ist_aktiv = item.get("ist_aktiv", True)
                updated += 1
            else:
                eintrag = ProdWerteliste(
                    id=generate_uuid(),
                    typ=typ,
                    code=item["code"],
                    bezeichnung=item["bezeichnung"],
                    sortierung=item.get("sortierung", 0),
                    ist_aktiv=item.get("ist_aktiv", True),
                )
                db.add(eintrag)
                created += 1

    return created, updated


async def main():
    """Run all seed operations."""
    print("=" * 60)
    print("Produktdaten Seed — Wertelisten & Stammdaten")
    print("=" * 60)

    await init_db()

    data = load_json("prod_wertelisten.json")

    async with async_session_maker() as db:
        # 1. Sortimente (FK target for blueprints)
        print("\n1. Sortimente...")
        created, updated = await seed_sortimente(db, data["sortimente"])
        print(f"   {created} erstellt, {updated} aktualisiert")

        # 2. Eigenschaften (FK target for blueprints)
        print("\n2. Eigenschaften...")
        created, updated = await seed_eigenschaften(db, data["eigenschaften"])
        print(f"   {created} erstellt, {updated} aktualisiert")

        # Flush to make IDs available for FK references in blueprints
        await db.flush()

        # 3. Sortiment-Blueprints (depends on sortiment + eigenschaft IDs)
        print("\n3. Sortiment-Blueprints...")
        created, updated = await seed_blueprints(db, data["sortiment_blueprints"])
        print(f"   {created} erstellt, {updated} aktualisiert")

        # 4. Wertelisten (independent)
        print("\n4. Wertelisten...")
        created, updated = await seed_wertelisten(db, data["wertelisten"])
        print(f"   {created} erstellt, {updated} aktualisiert")

        await db.commit()

    print("\n" + "=" * 60)
    print("Seed abgeschlossen!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
