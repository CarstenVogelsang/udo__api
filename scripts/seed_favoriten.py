#!/usr/bin/env python
"""Set favorites and sort order for Rechtsformen and Länder.

Usage:
    uv run python scripts/seed_favoriten.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import BasRechtsform
from app.models.geo import GeoLand


# Rechtsform favorites: {code: sortierung}
RECHTSFORM_FAVORITEN = {
    # Deutschland
    "gmbh": 1,
    "ag": 2,
    "gmbh_co_kg": 3,
    "ug": 4,
    # Österreich
    "gmbh_at": 1,
    # Schweiz
    "ag_ch": 1,
    "gmbh_ch": 2,
    # USA
    "inc": 1,
    "llc": 2,
}

# Zusätzliche Favoriten-Länder (neben allen EU-Ländern)
EXTRA_FAVORITEN_LAENDER = ["US", "CN", "GB", "NO", "CH"]


async def seed_rechtsform_favoriten(session: AsyncSession) -> int:
    """Set ist_favorit + sortierung on popular Rechtsformen."""
    count = 0
    for code, sort_order in RECHTSFORM_FAVORITEN.items():
        result = await session.execute(
            select(BasRechtsform).where(BasRechtsform.code == code)
        )
        rf = result.scalar_one_or_none()
        if rf:
            rf.ist_favorit = True
            rf.sortierung = sort_order
            count += 1
            print(f"  ★ {rf.name} ({rf.land_code}) → sort={sort_order}")
        else:
            print(f"  ⚠ Code '{code}' nicht gefunden")

    await session.commit()
    return count


async def seed_land_favoriten(session: AsyncSession) -> int:
    """Set ist_favorit on EU countries + key trading partners."""
    # Set all EU countries as favorites
    result = await session.execute(
        update(GeoLand)
        .where(GeoLand.ist_eu == True)  # noqa: E712
        .values(ist_favorit=True)
    )
    eu_count = result.rowcount
    print(f"  ★ {eu_count} EU-Länder als Favoriten markiert")

    # Set extra countries
    extra_count = 0
    for code in EXTRA_FAVORITEN_LAENDER:
        result = await session.execute(
            select(GeoLand).where(GeoLand.code == code)
        )
        land = result.scalar_one_or_none()
        if land:
            land.ist_favorit = True
            extra_count += 1
            print(f"  ★ {land.name} ({land.code})")
        else:
            print(f"  ⚠ Land '{code}' nicht gefunden")

    await session.commit()
    return eu_count + extra_count


async def main():
    """Main entry point."""
    async with async_session_maker() as session:
        print("Rechtsform-Favoriten setzen...")
        print("-" * 50)
        rf_count = await seed_rechtsform_favoriten(session)
        print(f"→ {rf_count} Rechtsformen als Favoriten markiert\n")

        print("Länder-Favoriten setzen...")
        print("-" * 50)
        land_count = await seed_land_favoriten(session)
        print(f"→ {land_count} Länder als Favoriten markiert")


if __name__ == "__main__":
    asyncio.run(main())
