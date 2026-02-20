#!/usr/bin/env python
"""Seed media license types (Medienlizenzen) into database.

Usage:
    uv run python scripts/seed_medien_lizenzen.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import BasMedienLizenz


SEED_DIR = Path(__file__).parent.parent / "seed"


async def seed_medien_lizenzen(session: AsyncSession) -> dict:
    """Seed Medienlizenzen from JSON file."""
    seed_file = SEED_DIR / "medien_lizenzen.json"

    if not seed_file.exists():
        print(f"Seed file not found: {seed_file}")
        return {"created": 0, "updated": 0}

    with open(seed_file, encoding="utf-8") as f:
        data = json.load(f)

    counts = {"created": 0, "updated": 0}

    for item in data:
        code = item["code"]

        result = await session.execute(
            select(BasMedienLizenz).where(BasMedienLizenz.code == code)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = item["name"]
            existing.beschreibung = item.get("beschreibung")
            existing.kategorie = item["kategorie"]
            existing.url = item.get("url")
            counts["updated"] += 1
            print(f"  Updated: {code}")
        else:
            lizenz = BasMedienLizenz(
                code=code,
                name=item["name"],
                beschreibung=item.get("beschreibung"),
                kategorie=item["kategorie"],
                url=item.get("url"),
                ist_aktiv=True,
            )
            session.add(lizenz)
            counts["created"] += 1
            print(f"  Created: {code}")

    await session.commit()
    return counts


async def main():
    """Main entry point."""
    print("Seeding Medienlizenzen...")
    print("-" * 50)

    async with async_session_maker() as session:
        counts = await seed_medien_lizenzen(session)

    print("-" * 50)
    print(f"Done! Created: {counts['created']}, Updated: {counts['updated']}")


if __name__ == "__main__":
    asyncio.run(main())
