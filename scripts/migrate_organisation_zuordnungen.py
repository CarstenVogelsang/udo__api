#!/usr/bin/env python3
"""
Migrate StoreGruppe assignments from Legacy DB.

Reads kStoreGruppe1 and kStoreGruppe2 from spi_tStore and creates
entries in com_unternehmen_organisation junction table.

WICHTIG: Legacy-DB ist READ-ONLY! Wir lesen nur die Zuordnungen.

Prerequisites:
- com_organisation must be populated (run ETL import first)
- com_unternehmen must be populated

Run:
    uv run python scripts/migrate_organisation_zuordnungen.py --dry-run
    uv run python scripts/migrate_organisation_zuordnungen.py
"""
import argparse
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pymssql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base

settings = get_settings()


def get_legacy_connection():
    """READ-ONLY connection to legacy MS SQL Server."""
    return pymssql.connect(
        server=settings.mssql_host,
        port=settings.mssql_port,
        database=settings.mssql_database,
        user=settings.mssql_user,
        password=settings.mssql_password,
        as_dict=True,
    )


def get_db_session():
    """Creates a synchronous database session."""
    db_url = settings.database_url_sync
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def build_lookup_caches(session):
    """Build lookup caches for Unternehmen and Organisation by legacy_id."""
    print("\nBaue Lookup-Caches...")

    # Unternehmen: legacy_id -> UUID
    result = session.execute(text(
        "SELECT legacy_id, id FROM com_unternehmen WHERE legacy_id IS NOT NULL"
    ))
    unternehmen_cache = {row[0]: row[1] for row in result}
    print(f"   -> {len(unternehmen_cache):,} Unternehmen")

    # Organisation: legacy_id -> UUID
    result = session.execute(text(
        "SELECT legacy_id, id FROM com_organisation WHERE legacy_id IS NOT NULL"
    ))
    organisation_cache = {row[0]: row[1] for row in result}
    print(f"   -> {len(organisation_cache):,} Organisationen")

    return unternehmen_cache, organisation_cache


def migrate_zuordnungen(dry_run: bool = False):
    """Migrate StoreGruppe assignments."""
    print("=" * 70)
    print("Migration: StoreGruppe-Zuordnungen")
    print(f"Modus: {'DRY-RUN (keine Änderungen)' if dry_run else 'LIVE'}")
    print("=" * 70)

    session, engine = get_db_session()

    try:
        # Build caches
        unternehmen_cache, organisation_cache = build_lookup_caches(session)

        if not organisation_cache:
            print("\nFEHLER: Keine Organisationen gefunden!")
            print("Bitte zuerst ausführen:")
            print("  1. uv run python scripts/setup_etl_organisation.py")
            print("  2. uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStoreGruppe")
            sys.exit(1)

        if not unternehmen_cache:
            print("\nFEHLER: Keine Unternehmen gefunden!")
            print("Bitte zuerst Unternehmen importieren.")
            sys.exit(1)

        # Check existing assignments
        print("\nPrüfe bestehende Zuordnungen...")
        existing_assignments = set()
        result = session.execute(text(
            "SELECT unternehmen_id, organisation_id FROM com_unternehmen_organisation"
        ))
        for row in result:
            existing_assignments.add((row[0], row[1]))
        print(f"   -> {len(existing_assignments):,} bestehende Zuordnungen")

        # Connect to legacy DB (READ-ONLY!)
        print("\nVerbinde mit Legacy-Datenbank...")
        try:
            legacy_conn = get_legacy_connection()
            cursor = legacy_conn.cursor()
            print("   -> Verbunden")
        except Exception as e:
            print(f"\nFEHLER: Kann nicht zur Legacy-DB verbinden: {e}")
            print("Prüfe .env Konfiguration (MSSQL_*)")
            sys.exit(1)

        # Read StoreGruppe assignments
        print("\nLese Legacy-Zuordnungen...")
        cursor.execute("""
            SELECT kStore, kStoreGruppe1, kStoreGruppe2
            FROM dbo.spi_tStore
            WHERE kStoreGruppe1 IS NOT NULL OR kStoreGruppe2 IS NOT NULL
        """)

        stats = {
            "read": 0,
            "created": 0,
            "skipped_no_unternehmen": 0,
            "skipped_no_org": 0,
            "skipped_duplicate": 0,
        }

        print("\nVerarbeite Zuordnungen...")

        for row in cursor:
            stats["read"] += 1
            k_store = row["kStore"]

            # Get Unternehmen UUID
            unternehmen_id = unternehmen_cache.get(k_store)
            if not unternehmen_id:
                stats["skipped_no_unternehmen"] += 1
                continue

            # Process both StoreGruppe1 and StoreGruppe2
            for gruppe_key in ["kStoreGruppe1", "kStoreGruppe2"]:
                k_gruppe = row.get(gruppe_key)
                if not k_gruppe:
                    continue

                # Convert to int if needed (might be string in legacy)
                try:
                    k_gruppe = int(k_gruppe)
                except (ValueError, TypeError):
                    stats["skipped_no_org"] += 1
                    continue

                # Get Organisation UUID
                organisation_id = organisation_cache.get(k_gruppe)
                if not organisation_id:
                    stats["skipped_no_org"] += 1
                    continue

                # Check for duplicate
                if (unternehmen_id, organisation_id) in existing_assignments:
                    stats["skipped_duplicate"] += 1
                    continue

                # Create assignment
                if not dry_run:
                    session.execute(text("""
                        INSERT INTO com_unternehmen_organisation
                        (id, unternehmen_id, organisation_id, erstellt_am)
                        VALUES (:id, :u_id, :o_id, :erstellt_am)
                    """), {
                        "id": str(uuid4()),
                        "u_id": unternehmen_id,
                        "o_id": organisation_id,
                        "erstellt_am": datetime.utcnow(),
                    })

                existing_assignments.add((unternehmen_id, organisation_id))
                stats["created"] += 1

            # Progress and commit in batches
            if stats["read"] % 1000 == 0:
                if not dry_run:
                    session.commit()
                print(f"   ... {stats['read']:,} Zeilen verarbeitet, {stats['created']:,} Zuordnungen")

        if not dry_run:
            session.commit()

        cursor.close()
        legacy_conn.close()

        print("\n" + "=" * 70)
        print("Migration abgeschlossen!")
        print("=" * 70)
        print(f"\nStatistik:")
        print(f"  Gelesen:              {stats['read']:,}")
        print(f"  Zuordnungen erstellt: {stats['created']:,}")
        print(f"\nÜbersprungen:")
        print(f"  - Kein Unternehmen:   {stats['skipped_no_unternehmen']:,}")
        print(f"  - Keine Organisation: {stats['skipped_no_org']:,}")
        print(f"  - Duplikat:           {stats['skipped_duplicate']:,}")

        if dry_run:
            print("\n[DRY-RUN] Keine Änderungen wurden gespeichert.")
            print("Führe ohne --dry-run aus, um Daten zu importieren.")

    except Exception as e:
        session.rollback()
        print(f"\nFehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Migriert StoreGruppe-Zuordnungen aus Legacy-DB"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Testlauf ohne Schreiben"
    )
    args = parser.parse_args()

    migrate_zuordnungen(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
