#!/usr/bin/env python3
"""
Seed script for Branchenklassifikation data.

Loads WZ-2008 codes, business directories, regional groups,
Google Business categories and WZ→Google mappings from JSON files.

Idempotent: existing entries are updated, new ones created.

Usage:
    uv run python scripts/seed_branchen.py
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
from app.models.branche import (
    BrnBranche,
    BrnVerzeichnis,
    BrnRegionaleGruppe,
    BrnGoogleKategorie,
    BrnGoogleMapping,
)

SEED_DIR = Path(__file__).parent.parent / "seed"


def load_json(filename: str) -> list | dict:
    """Load a JSON seed file."""
    filepath = SEED_DIR / filename
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


async def seed_branchen(db) -> tuple[int, int]:
    """Seed WZ-2008 industry codes."""
    data = load_json("wz_2008_branchen.json")
    created, updated = 0, 0

    for item in data:
        result = await db.execute(
            select(BrnBranche).where(BrnBranche.wz_code == item["wz_code"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.bezeichnung = item["bezeichnung"]
            existing.ebene = item["ebene"]
            existing.parent_wz_code = item.get("parent_wz_code")
            updated += 1
        else:
            branche = BrnBranche(
                id=generate_uuid(),
                wz_code=item["wz_code"],
                bezeichnung=item["bezeichnung"],
                ebene=item["ebene"],
                parent_wz_code=item.get("parent_wz_code"),
            )
            db.add(branche)
            created += 1

    return created, updated


async def seed_verzeichnisse(db) -> tuple[int, int]:
    """Seed business directories."""
    data = load_json("verzeichnisse.json")
    created, updated = 0, 0

    for item in data:
        result = await db.execute(
            select(BrnVerzeichnis).where(
                BrnVerzeichnis.name == item["name"],
                BrnVerzeichnis.url == item["url"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in item.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            updated += 1
        else:
            verzeichnis = BrnVerzeichnis(
                id=generate_uuid(),
                name=item["name"],
                url=item["url"],
                beschreibung=item.get("beschreibung"),
                branche_wz_code=item.get("branche_wz_code"),
                ist_branchenuebergreifend=item.get("ist_branchenuebergreifend", False),
                hat_api=item.get("hat_api", False),
                api_dokumentation_url=item.get("api_dokumentation_url"),
                anmeldeart=item["anmeldeart"],
                anmelde_url=item.get("anmelde_url"),
                kosten=item["kosten"],
                kosten_details=item.get("kosten_details"),
                relevanz_score=item.get("relevanz_score", 5),
                regionen=item.get("regionen", []),
                anleitung_url=item.get("anleitung_url"),
                logo_url=item.get("logo_url"),
            )
            db.add(verzeichnis)
            created += 1

    return created, updated


async def seed_gruppen(db) -> tuple[int, int]:
    """Seed regional social media groups."""
    data = load_json("regionale_gruppen.json")
    created, updated = 0, 0

    for item in data:
        result = await db.execute(
            select(BrnRegionaleGruppe).where(
                BrnRegionaleGruppe.name == item["name"],
                BrnRegionaleGruppe.url == item["url"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in item.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            updated += 1
        else:
            gruppe = BrnRegionaleGruppe(
                id=generate_uuid(),
                plattform=item["plattform"],
                name=item["name"],
                url=item["url"],
                beschreibung=item.get("beschreibung"),
                branche_wz_code=item.get("branche_wz_code"),
                region_plz_prefix=item.get("region_plz_prefix"),
                region_name=item.get("region_name"),
                region_bundesland=item.get("region_bundesland"),
                mitglieder_anzahl=item.get("mitglieder_anzahl"),
                werbung_erlaubt=item.get("werbung_erlaubt", False),
                posting_regeln=item.get("posting_regeln"),
                empfohlene_posting_art=item.get("empfohlene_posting_art"),
            )
            db.add(gruppe)
            created += 1

    return created, updated


async def seed_google_kategorien_und_mappings(db) -> dict:
    """Seed Google categories and WZ→Google mappings."""
    data = load_json("google_mapping.json")
    stats = {"kategorien_created": 0, "kategorien_updated": 0,
             "mappings_created": 0, "mappings_updated": 0}

    # 1. Google-Kategorien
    for item in data["kategorien"]:
        result = await db.execute(
            select(BrnGoogleKategorie).where(BrnGoogleKategorie.gcid == item["gcid"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.name_de = item["name_de"]
            existing.name_en = item["name_en"]
            stats["kategorien_updated"] += 1
        else:
            kategorie = BrnGoogleKategorie(
                id=generate_uuid(),
                gcid=item["gcid"],
                name_de=item["name_de"],
                name_en=item["name_en"],
            )
            db.add(kategorie)
            stats["kategorien_created"] += 1

    # Flush to make GCIDs available for FK references
    await db.flush()

    # 2. Mappings
    for item in data["mappings"]:
        result = await db.execute(
            select(BrnGoogleMapping).where(
                BrnGoogleMapping.wz_code == item["wz_code"],
                BrnGoogleMapping.gcid == item["gcid"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.ist_primaer = item.get("ist_primaer", False)
            existing.relevanz = item.get("relevanz", 5)
            stats["mappings_updated"] += 1
        else:
            mapping = BrnGoogleMapping(
                id=generate_uuid(),
                wz_code=item["wz_code"],
                gcid=item["gcid"],
                ist_primaer=item.get("ist_primaer", False),
                relevanz=item.get("relevanz", 5),
            )
            db.add(mapping)
            stats["mappings_created"] += 1

    return stats


async def main():
    """Run all seed operations."""
    print("=" * 60)
    print("Branchenklassifikation Seed")
    print("=" * 60)

    await init_db()

    async with async_session_maker() as db:
        # 1. Branchen (WZ-Codes) — must be first (FK target)
        print("\n1. WZ-2008 Branchencodes...")
        created, updated = await seed_branchen(db)
        print(f"   {created} erstellt, {updated} aktualisiert")

        # 2. Verzeichnisse
        print("\n2. Branchenverzeichnisse...")
        created, updated = await seed_verzeichnisse(db)
        print(f"   {created} erstellt, {updated} aktualisiert")

        # 3. Regionale Gruppen
        print("\n3. Regionale Gruppen...")
        created, updated = await seed_gruppen(db)
        print(f"   {created} erstellt, {updated} aktualisiert")

        # 4. Google-Kategorien + Mappings
        print("\n4. Google-Kategorien und WZ-Mappings...")
        stats = await seed_google_kategorien_und_mappings(db)
        print(f"   Kategorien: {stats['kategorien_created']} erstellt, {stats['kategorien_updated']} aktualisiert")
        print(f"   Mappings:   {stats['mappings_created']} erstellt, {stats['mappings_updated']} aktualisiert")

        await db.commit()

    print("\n" + "=" * 60)
    print("Seed abgeschlossen!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
