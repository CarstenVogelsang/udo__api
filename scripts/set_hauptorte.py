#!/usr/bin/env python3
"""
Script to set ist_hauptort for all places in geo_ort.

Logic:
- For each (kreis_id, name) group, the entry with the lowest PLZ becomes ist_hauptort=1
- All other entries get ist_hauptort=0

Usage:
    uv run python scripts/set_hauptorte.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()


def get_db_session():
    """Creates a synchronous database session."""
    db_url = settings.database_url_sync
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def main():
    """Set ist_hauptort for all places."""
    print("=" * 60)
    print("UDO API - Hauptorte setzen")
    print("=" * 60)

    session, engine = get_db_session()

    # Count current state
    print("\n[1/3] Analysiere aktuellen Stand...")
    total = session.execute(text("SELECT COUNT(*) FROM geo_ort")).scalar()
    current_hauptorte = session.execute(
        text("SELECT COUNT(*) FROM geo_ort WHERE ist_hauptort = true")
    ).scalar()
    unique_combinations = session.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT kreis_id, name FROM geo_ort GROUP BY kreis_id, name
        ) sub
    """)).scalar()

    print(f"      Gesamtzahl Orte: {total:,}")
    print(f"      Aktuelle Hauptorte: {current_hauptorte:,}")
    print(f"      Eindeutige (Kreis, Name) Kombinationen: {unique_combinations:,}")

    # Reset all ist_hauptort to false
    print("\n[2/3] Setze alle ist_hauptort auf false...")
    result = session.execute(text("UPDATE geo_ort SET ist_hauptort = false"))
    print(f"      {result.rowcount:,} Einträge aktualisiert")

    # Set ist_hauptort = true for entry with lowest PLZ per (kreis_id, name)
    print("\n[3/3] Setze ist_hauptort = true für niedrigste PLZ pro (Kreis, Name)...")
    result = session.execute(text("""
        UPDATE geo_ort
        SET ist_hauptort = true
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY kreis_id, name
                           ORDER BY plz ASC NULLS LAST, id ASC
                       ) as rn
                FROM geo_ort
            ) ranked
            WHERE rn = 1
        )
    """))
    updated = result.rowcount
    print(f"      {updated:,} Hauptorte gesetzt")

    session.commit()

    # Verify results
    print("\n" + "=" * 60)
    print("Verifikation")
    print("=" * 60)

    new_hauptorte = session.execute(
        text("SELECT COUNT(*) FROM geo_ort WHERE ist_hauptort = true")
    ).scalar()
    duplicates = session.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT kreis_id, name, COUNT(*) as cnt
            FROM geo_ort
            WHERE ist_hauptort = true
            GROUP BY kreis_id, name
            HAVING COUNT(*) > 1
        ) sub
    """)).scalar()

    print(f"\nNeue Hauptorte: {new_hauptorte:,}")
    print(f"Erwartete Hauptorte: {unique_combinations:,}")
    print(f"Duplikate (mehrere Hauptorte pro Kreis+Name): {duplicates}")

    if new_hauptorte == unique_combinations and duplicates == 0:
        print("\n[OK] Migration erfolgreich!")
    else:
        print("\n[WARNUNG] Unerwartete Ergebnisse!")

    # Show some examples
    print("\n" + "=" * 60)
    print("Beispiele")
    print("=" * 60)

    rows = session.execute(text("""
        SELECT k.name as kreis, o.name as ort, o.plz, o.ist_hauptort
        FROM geo_ort o
        JOIN geo_kreis k ON o.kreis_id = k.id
        WHERE o.name = 'Berlin'
        ORDER BY o.plz
        LIMIT 10
    """)).fetchall()

    print("\nBerlin (erste 10 PLZ):")
    print(f"{'Kreis':<30} {'Ort':<15} {'PLZ':<10} {'Hauptort'}")
    print("-" * 65)
    for row in rows:
        hauptort = "ja" if row[3] else ""
        print(f"{row[0]:<30} {row[1]:<15} {row[2]:<10} {hauptort}")

    rows = session.execute(text("""
        SELECT k.name as kreis, o.name as ort, o.plz, o.ist_hauptort
        FROM geo_ort o
        JOIN geo_kreis k ON o.kreis_id = k.id
        WHERE o.name = 'München'
        ORDER BY o.plz
        LIMIT 10
    """)).fetchall()

    print("\nMünchen (erste 10 PLZ):")
    print(f"{'Kreis':<30} {'Ort':<15} {'PLZ':<10} {'Hauptort'}")
    print("-" * 65)
    for row in rows:
        hauptort = "ja" if row[3] else ""
        print(f"{row[0]:<30} {row[1]:<15} {row[2]:<10} {hauptort}")

    session.close()
    print("\nFertig!")


if __name__ == "__main__":
    main()
