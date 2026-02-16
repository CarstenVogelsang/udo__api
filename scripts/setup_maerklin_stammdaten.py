#!/usr/bin/env python3
"""
Seed master data required for Märklin dealer import.

Creates (idempotent):
- bas_sprache: de, en, fr, it, nl
- ComUnternehmen: Märklin (as manufacturer)
- ComMarke: Märklin, Trix, LGB (under Märklin)
- ComSerie: MyWorld, Premium Spur 1 (under Märklin brand)
- ComDienstleistung: Modellbahn-Reparaturservice

Run: uv run python scripts/setup_maerklin_stammdaten.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
from app.models.base import BasSprache, BasStatus
from app.models.com import (
    ComUnternehmen, ComMarke, ComSerie, ComDienstleistung,
)
from app.models import etl as _etl  # noqa: F401

settings = get_settings()


def get_db_session():
    """Creates a synchronous database session."""
    db_url = settings.database_url_sync
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


# ============ Data Definitions ============

SPRACHEN = [
    ("de", "Deutsch", "German"),
    ("en", "Englisch", "English"),
    ("fr", "Französisch", "French"),
    ("it", "Italienisch", "Italian"),
    ("nl", "Niederländisch", "Dutch"),
]

MARKEN = ["Märklin", "Trix", "LGB"]

SERIEN = [
    ("MyWorld", "Märklin"),
    ("Premium Spur 1", "Märklin"),
]

DIENSTLEISTUNGEN = [
    "Modellbahn-Reparaturservice",
]


def seed_sprachen(session) -> dict[str, str]:
    """Seed language lookup table. Returns {code: id} mapping."""
    print("\n1. Sprachen seeden...")
    result = {}
    for code, name, name_eng in SPRACHEN:
        existing = session.execute(
            select(BasSprache).where(BasSprache.code == code)
        ).scalar_one_or_none()

        if existing:
            print(f"   {code}: {name} (bereits vorhanden)")
            result[code] = str(existing.id)
        else:
            sprache = BasSprache(code=code, name=name, name_eng=name_eng)
            session.add(sprache)
            session.flush()
            print(f"   {code}: {name} (neu erstellt)")
            result[code] = str(sprache.id)

    return result


def seed_maerklin(session, sprache_map: dict) -> str:
    """Seed Märklin as manufacturer. Returns Märklin ComUnternehmen.id."""
    print("\n2. Märklin als Hersteller seeden...")
    existing = session.execute(
        select(ComUnternehmen).where(ComUnternehmen.kurzname == "Märklin")
    ).scalar_one_or_none()

    if existing:
        print(f"   Märklin (bereits vorhanden: {existing.id})")
        return str(existing.id)

    # Lookup status_id for 'aktiv' in kontext 'unternehmen'
    status_aktiv = session.execute(
        select(BasStatus).where(
            BasStatus.code == "aktiv",
            BasStatus.kontext == "unternehmen",
        )
    ).scalar_one_or_none()

    maerklin = ComUnternehmen(
        kurzname="Märklin",
        firmierung="Gebr. Märklin & Cie. GmbH",
        status_id=str(status_aktiv.id) if status_aktiv else None,
        strasse="Stuttgarter Str.",
        strasse_hausnr="55-57",
        website="https://www.maerklin.de",
        email="service@maerklin.de",
        telefon="+497161608222",
        sprache_id=sprache_map.get("de"),
    )
    session.add(maerklin)
    session.flush()
    print(f"   Märklin (neu erstellt: {maerklin.id})")
    return str(maerklin.id)


def seed_marken(session, hersteller_id: str) -> dict[str, str]:
    """Seed brands. Returns {name: id} mapping."""
    print("\n3. Marken seeden...")
    result = {}
    for name in MARKEN:
        existing = session.execute(
            select(ComMarke).where(
                ComMarke.hersteller_id == hersteller_id,
                ComMarke.name == name,
            )
        ).scalar_one_or_none()

        if existing:
            print(f"   {name} (bereits vorhanden)")
            result[name] = str(existing.id)
        else:
            marke = ComMarke(hersteller_id=hersteller_id, name=name)
            session.add(marke)
            session.flush()
            print(f"   {name} (neu erstellt)")
            result[name] = str(marke.id)

    return result


def seed_serien(session, marken_map: dict):
    """Seed product series."""
    print("\n4. Serien seeden...")
    for serie_name, marke_name in SERIEN:
        marke_id = marken_map.get(marke_name)
        if not marke_id:
            print(f"   WARNUNG: Marke '{marke_name}' nicht gefunden, überspringe '{serie_name}'")
            continue

        existing = session.execute(
            select(ComSerie).where(
                ComSerie.marke_id == marke_id,
                ComSerie.name == serie_name,
            )
        ).scalar_one_or_none()

        if existing:
            print(f"   {serie_name} (unter {marke_name}, bereits vorhanden)")
        else:
            serie = ComSerie(marke_id=marke_id, name=serie_name)
            session.add(serie)
            session.flush()
            print(f"   {serie_name} (unter {marke_name}, neu erstellt)")


def seed_dienstleistungen(session):
    """Seed service types."""
    print("\n5. Dienstleistungen seeden...")
    for name in DIENSTLEISTUNGEN:
        existing = session.execute(
            select(ComDienstleistung).where(ComDienstleistung.name == name)
        ).scalar_one_or_none()

        if existing:
            print(f"   {name} (bereits vorhanden)")
        else:
            dl = ComDienstleistung(name=name)
            session.add(dl)
            session.flush()
            print(f"   {name} (neu erstellt)")


def main():
    """Run full master data seeding."""
    session, engine = get_db_session()

    print("=" * 70)
    print("Stammdaten-Setup für Märklin-Import")
    print("=" * 70)

    try:
        sprache_map = seed_sprachen(session)
        maerklin_id = seed_maerklin(session, sprache_map)
        marken_map = seed_marken(session, maerklin_id)
        seed_serien(session, marken_map)
        seed_dienstleistungen(session)

        session.commit()

        print("\n" + "=" * 70)
        print("Stammdaten-Setup abgeschlossen!")
        print(f"  Sprachen:         {len(SPRACHEN)}")
        print(f"  Hersteller:       Märklin ({maerklin_id[:8]}...)")
        print(f"  Marken:           {len(MARKEN)}")
        print(f"  Serien:           {len(SERIEN)}")
        print(f"  Dienstleistungen: {len(DIENSTLEISTUNGEN)}")
        print("=" * 70)

    except Exception as e:
        session.rollback()
        print(f"\nFEHLER: {e}")
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
