#!/usr/bin/env python
"""Seed UDO-specific classifications (Klassifikationen) into database.

Usage:
    uv run python scripts/seed_klassifikationen.py
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import ComKlassifikation, BrnGoogleKategorie


SEED_DIR = Path(__file__).parent.parent / "seed"


async def seed_klassifikationen(session: AsyncSession) -> dict:
    """Seed UDO Klassifikationen from all klassifikationen_*.json files.

    Returns:
        dict with counts: created, updated, skipped
    """
    seed_files = sorted(SEED_DIR.glob("klassifikationen_*.json"))

    if not seed_files:
        print("No seed files matching klassifikationen_*.json found")
        return {"created": 0, "updated": 0, "skipped": 0}

    klassifikationen = []
    for seed_file in seed_files:
        print(f"  Loading: {seed_file.name}")
        with open(seed_file, encoding="utf-8") as f:
            data = json.load(f)
        klassifikationen.extend(data.get("klassifikationen", []))

    counts = {"created": 0, "updated": 0, "skipped": 0}

    for item in klassifikationen:
        slug = item["slug"]

        # Check if exists
        result = await session.execute(
            select(ComKlassifikation).where(ComKlassifikation.slug == slug)
        )
        existing = result.scalar_one_or_none()

        # Validate google_mapping_gcid if provided
        gcid = item.get("google_mapping_gcid")
        if gcid:
            result = await session.execute(
                select(BrnGoogleKategorie).where(BrnGoogleKategorie.gcid == gcid)
            )
            google_kat = result.scalar_one_or_none()
            if not google_kat:
                print(f"  Warning: Google category '{gcid}' not found for '{slug}', setting to NULL")
                gcid = None

        if existing:
            # Update
            existing.name_de = item["name_de"]
            existing.dimension = item.get("dimension")
            existing.beschreibung = item.get("beschreibung")
            existing.google_mapping_gcid = gcid
            counts["updated"] += 1
            print(f"  Updated: {slug}")
        else:
            # Create
            klassifikation = ComKlassifikation(
                slug=slug,
                name_de=item["name_de"],
                dimension=item.get("dimension"),
                beschreibung=item.get("beschreibung"),
                google_mapping_gcid=gcid,
                ist_aktiv=True,
            )
            session.add(klassifikation)
            counts["created"] += 1
            print(f"  Created: {slug}")

    await session.commit()
    return counts


async def main():
    """Main entry point."""
    print("Seeding UDO Klassifikationen...")
    print("-" * 50)

    async with async_session_maker() as session:
        counts = await seed_klassifikationen(session)

    print("-" * 50)
    print(f"Done! Created: {counts['created']}, Updated: {counts['updated']}")


if __name__ == "__main__":
    asyncio.run(main())
