#!/usr/bin/env python3
"""
Migriert Ansprechpartner von Legacy MS SQL Server nach SQLite.

WICHTIG: Legacy-DB ist READ-ONLY!

Usage:
    uv run python scripts/migrate_kontakte.py
    uv run python scripts/migrate_kontakte.py --dry-run
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

import pymssql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base

settings = get_settings()


def get_legacy_connection():
    """Legacy MS SQL Server Verbindung (READ-ONLY!)."""
    return pymssql.connect(
        server=settings.mssql_host,
        port=settings.mssql_port,
        database=settings.mssql_database,
        user=settings.mssql_user,
        password=settings.mssql_password,
        as_dict=True,
    )


def get_sqlite_session():
    """SQLite Session."""
    db_url = settings.sqlite_database_url.replace("+aiosqlite", "")
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def migrate_kontakte(dry_run: bool = False):
    """Migriert Ansprechpartner mit Store-Verknüpfung."""
    print("=" * 70)
    print("Kontakte Migration: Legacy MS SQL → SQLite")
    print(f"Modus: {'DRY-RUN' if dry_run else 'LIVE'}")
    print("=" * 70)

    session, _ = get_sqlite_session()
    legacy_conn = get_legacy_connection()
    cursor = legacy_conn.cursor()

    # 1. Build Unternehmen lookup (legacy_id → uuid)
    print("\n[1/3] Baue Unternehmen-Lookup...")
    unternehmen_map = {}
    result = session.execute(text(
        "SELECT legacy_id, id FROM com_unternehmen WHERE legacy_id IS NOT NULL"
    ))
    for row in result:
        unternehmen_map[row[0]] = row[1]
    print(f"      {len(unternehmen_map)} Unternehmen gefunden")

    # 2. Query Legacy Ansprechpartner
    print("\n[2/3] Lade Legacy-Ansprechpartner...")
    cursor.execute("""
        SELECT
            a.kAnsprechpartner,
            a.kStore,
            a.cVorname,
            a.cNachname,
            a.cAnrede,
            a.cTitel,
            a.cTel,
            a.cTelMobil,
            a.cFax,
            a.cMail,
            a.cAbteilung,
            f.cAnsprechpartnerFunktion,
            a.bIstHauptansprechpartner,
            a.cAnmerkung
        FROM spi_tAnsprechpartner a
        LEFT JOIN spi_tAnsprechpartnerFunktion f
            ON a.kAnsprechpartnerFunktion = f.kAnsprechpartnerFunktion
        WHERE a.kStore IS NOT NULL
          AND a.kStore > 0
          AND (a.bIstGelöscht IS NULL OR a.bIstGelöscht = 0)
    """)

    # 3. Migrate
    print("\n[3/3] Migriere Kontakte...")
    stats = {"read": 0, "created": 0, "skipped": 0, "updated": 0}

    for row in cursor:
        stats["read"] += 1

        kStore = row["kStore"]
        unternehmen_id = unternehmen_map.get(kStore)

        if not unternehmen_id:
            stats["skipped"] += 1
            continue

        vorname = row["cVorname"] or ""
        nachname = row["cNachname"] or ""

        # Validate required fields
        if not vorname and not nachname:
            stats["skipped"] += 1
            continue

        if not dry_run:
            # Check if already exists
            existing = session.execute(text(
                "SELECT id FROM com_kontakt WHERE legacy_id = :legacy_id"
            ), {"legacy_id": row["kAnsprechpartner"]}).fetchone()

            if existing:
                # Update
                session.execute(text("""
                    UPDATE com_kontakt SET
                        vorname = :vorname,
                        nachname = :nachname,
                        anrede = :anrede,
                        titel = :titel,
                        telefon = :telefon,
                        mobil = :mobil,
                        fax = :fax,
                        email = :email,
                        abteilung = :abteilung,
                        typ = :typ,
                        ist_hauptkontakt = :ist_hauptkontakt,
                        notizen = :notizen,
                        aktualisiert_am = :aktualisiert_am
                    WHERE legacy_id = :legacy_id
                """), {
                    "vorname": vorname or None,
                    "nachname": nachname or None,
                    "anrede": row["cAnrede"],
                    "titel": row["cTitel"],
                    "telefon": row["cTel"],
                    "mobil": row["cTelMobil"],
                    "fax": row["cFax"],
                    "email": row["cMail"],
                    "abteilung": row["cAbteilung"],
                    "typ": row["cAnsprechpartnerFunktion"],
                    "ist_hauptkontakt": 1 if row["bIstHauptansprechpartner"] else 0,
                    "notizen": row["cAnmerkung"],
                    "aktualisiert_am": datetime.utcnow(),
                    "legacy_id": row["kAnsprechpartner"],
                })
                stats["updated"] += 1
            else:
                # Create
                session.execute(text("""
                    INSERT INTO com_kontakt (
                        id, unternehmen_id, legacy_id, vorname, nachname,
                        anrede, titel, telefon, mobil, fax, email,
                        abteilung, typ, ist_hauptkontakt, notizen,
                        erstellt_am, aktualisiert_am
                    ) VALUES (
                        :id, :unternehmen_id, :legacy_id, :vorname, :nachname,
                        :anrede, :titel, :telefon, :mobil, :fax, :email,
                        :abteilung, :typ, :ist_hauptkontakt, :notizen,
                        :erstellt_am, :aktualisiert_am
                    )
                """), {
                    "id": str(uuid4()),
                    "unternehmen_id": unternehmen_id,
                    "legacy_id": row["kAnsprechpartner"],
                    "vorname": vorname,
                    "nachname": nachname,
                    "anrede": row["cAnrede"],
                    "titel": row["cTitel"],
                    "telefon": row["cTel"],
                    "mobil": row["cTelMobil"],
                    "fax": row["cFax"],
                    "email": row["cMail"],
                    "abteilung": row["cAbteilung"],
                    "typ": row["cAnsprechpartnerFunktion"],
                    "ist_hauptkontakt": 1 if row["bIstHauptansprechpartner"] else 0,
                    "notizen": row["cAnmerkung"],
                    "erstellt_am": datetime.utcnow(),
                    "aktualisiert_am": datetime.utcnow(),
                })
                stats["created"] += 1

        else:
            stats["created"] += 1

        # Commit in batches
        if stats["read"] % 500 == 0:
            if not dry_run:
                session.commit()
            print(f"      ... {stats['read']} verarbeitet")

    if not dry_run:
        session.commit()

    cursor.close()
    legacy_conn.close()
    session.close()

    print("\n" + "=" * 70)
    print("Migration abgeschlossen!")
    print("=" * 70)
    print(f"Gelesen:     {stats['read']}")
    print(f"Erstellt:    {stats['created']}")
    print(f"Aktualisiert:{stats['updated']}")
    print(f"Übersprungen:{stats['skipped']}")


def main():
    parser = argparse.ArgumentParser(description="Kontakte Migration")
    parser.add_argument("--dry-run", "-d", action="store_true",
                        help="Testlauf ohne Schreiben")
    args = parser.parse_args()

    try:
        migrate_kontakte(dry_run=args.dry_run)
    except Exception as e:
        print(f"\nFEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
