#!/usr/bin/env python
"""Seed legal forms (Rechtsformen) into database.

Usage:
    uv run python scripts/seed_rechtsformen.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import BasRechtsform


SEED_DIR = Path(__file__).parent.parent / "seed"


async def seed_rechtsformen(session: AsyncSession) -> dict:
    """Seed Rechtsformen from JSON file."""
    seed_file = SEED_DIR / "rechtsformen.json"

    if not seed_file.exists():
        print(f"Seed file not found: {seed_file}")
        return {"created": 0, "updated": 0}

    with open(seed_file, encoding="utf-8") as f:
        data = json.load(f)

    counts = {"created": 0, "updated": 0}

    for item in data:
        code = item["code"]

        result = await session.execute(
            select(BasRechtsform).where(BasRechtsform.code == code)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = item["name"]
            existing.name_lang = item.get("name_lang")
            existing.land_code = item.get("land_code")
            counts["updated"] += 1
            print(f"  Updated: {code}")
        else:
            rechtsform = BasRechtsform(
                code=code,
                name=item["name"],
                name_lang=item.get("name_lang"),
                land_code=item.get("land_code"),
                ist_aktiv=True,
            )
            session.add(rechtsform)
            counts["created"] += 1
            print(f"  Created: {code}")

    await session.commit()
    return counts


async def main():
    """Main entry point."""
    print("Seeding Rechtsformen...")
    print("-" * 50)

    async with async_session_maker() as session:
        counts = await seed_rechtsformen(session)

    print("-" * 50)
    print(f"Done! Created: {counts['created']}, Updated: {counts['updated']}")


if __name__ == "__main__":
    asyncio.run(main())
