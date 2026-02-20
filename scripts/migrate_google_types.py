#!/usr/bin/env python
"""Migrate existing Google Types from metadaten JSON to junction table.

This script processes all existing companies (ComUnternehmen) that have
Google category data stored in their metadaten JSON field and:
1. Extracts Google category IDs (gcid format)
2. Creates entries in com_unternehmen_google_type junction table
3. Derives WZ-Code from primary Google type via brn_google_mapping

Usage:
    uv run python scripts/migrate_google_types.py
    uv run python scripts/migrate_google_types.py --dry-run
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import (
    ComUnternehmen,
    ComUnternehmenGoogleType,
    BrnGoogleKategorie,
    BrnGoogleMapping,
)


async def migrate_google_types(
    session: AsyncSession,
    dry_run: bool = False,
) -> dict:
    """Migrate Google Types from metadaten to junction table.

    Args:
        session: Async database session
        dry_run: If True, don't commit changes

    Returns:
        dict with counts: processed, types_created, wz_derived, skipped
    """
    counts = {
        "processed": 0,
        "types_created": 0,
        "wz_derived": 0,
        "skipped": 0,
        "no_metadaten": 0,
    }

    # Load all companies with metadaten
    result = await session.execute(
        select(ComUnternehmen).where(
            ComUnternehmen.metadaten.isnot(None),
            ComUnternehmen.geloescht_am.is_(None),
        )
    )
    unternehmen_list = list(result.scalars().all())
    print(f"Found {len(unternehmen_list)} companies with metadaten")

    for unternehmen in unternehmen_list:
        counts["processed"] += 1

        # Extract Google data from metadaten
        metadaten = unternehmen.metadaten or {}
        google_data = metadaten.get("google", {})

        # Try category_ids first, then fallback to categories
        category_ids = google_data.get("category_ids", [])

        if not category_ids:
            # Fallback: try to construct gcid from categories
            categories = google_data.get("categories", [])
            if categories:
                category_ids = [
                    f"gcid:{cat.lower().replace(' ', '_').replace('-', '_')}"
                    for cat in categories
                ]

        if not category_ids:
            counts["no_metadaten"] += 1
            continue

        wz_code_gefunden = None

        for i, gcid in enumerate(category_ids):
            # Normalize gcid format
            if not gcid.startswith("gcid:"):
                gcid = f"gcid:{gcid}"

            # Check if category exists in brn_google_kategorie
            kat_result = await session.execute(
                select(BrnGoogleKategorie).where(BrnGoogleKategorie.gcid == gcid)
            )
            google_kat = kat_result.scalar_one_or_none()

            if not google_kat:
                # Category not in database, skip
                continue

            # Check if entry already exists
            existing = await session.execute(
                select(ComUnternehmenGoogleType).where(
                    ComUnternehmenGoogleType.unternehmen_id == unternehmen.id,
                    ComUnternehmenGoogleType.gcid == gcid,
                )
            )
            if existing.scalar_one_or_none():
                counts["skipped"] += 1
                continue

            # Create junction entry
            google_type = ComUnternehmenGoogleType(
                unternehmen_id=unternehmen.id,
                gcid=gcid,
                ist_primaer=(i == 0),
                ist_abgeleitet=False,
                quelle="migration",
            )
            session.add(google_type)
            counts["types_created"] += 1

            # Derive WZ code from first (primary) Google type
            if i == 0 and not wz_code_gefunden and not unternehmen.wz_code:
                mapping_result = await session.execute(
                    select(BrnGoogleMapping).where(
                        BrnGoogleMapping.gcid == gcid,
                        BrnGoogleMapping.ist_primaer == True,  # noqa: E712
                    )
                )
                mapping = mapping_result.scalar_one_or_none()
                if mapping:
                    wz_code_gefunden = mapping.wz_code

        # Set WZ code on company if found
        if wz_code_gefunden and not unternehmen.wz_code:
            unternehmen.wz_code = wz_code_gefunden
            counts["wz_derived"] += 1

        # Progress indicator
        if counts["processed"] % 100 == 0:
            print(f"  Processed {counts['processed']} companies...")

    if not dry_run:
        await session.commit()
        print("Changes committed.")
    else:
        print("DRY RUN - no changes committed.")

    return counts


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate Google Types from metadaten to junction table"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't commit changes, just show what would be done",
    )
    args = parser.parse_args()

    print("Migrating Google Types from metadaten to junction table...")
    print("-" * 60)

    async with async_session_maker() as session:
        counts = await migrate_google_types(session, dry_run=args.dry_run)

    print("-" * 60)
    print(f"Processed:     {counts['processed']} companies")
    print(f"No metadaten:  {counts['no_metadaten']} (skipped)")
    print(f"Types created: {counts['types_created']}")
    print(f"Types skipped: {counts['skipped']} (already exist)")
    print(f"WZ derived:    {counts['wz_derived']}")


if __name__ == "__main__":
    asyncio.run(main())
