#!/usr/bin/env python3
"""
Script to set ist_hauptort for all places in geo_ort.

Logic:
- For each (kreis_id, name) group, the entry with the lowest PLZ becomes ist_hauptort=1
- All other entries get ist_hauptort=0

Usage:
    uv run python scripts/set_hauptorte.py
"""
import sqlite3
from pathlib import Path


def main():
    """Set ist_hauptort for all places."""
    print("=" * 60)
    print("UDO API - Hauptorte setzen")
    print("=" * 60)

    # Find database
    db_path = Path(__file__).parent.parent / "data" / "geo.db"
    if not db_path.exists():
        print(f"Fehler: Datenbank nicht gefunden: {db_path}")
        return

    print(f"\n[1/4] Verbinde mit Datenbank: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count current state
    print("\n[2/4] Analysiere aktuellen Stand...")
    cursor.execute("SELECT COUNT(*) FROM geo_ort")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM geo_ort WHERE ist_hauptort = 1")
    current_hauptorte = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT kreis_id, name FROM geo_ort GROUP BY kreis_id, name
        )
    """)
    unique_combinations = cursor.fetchone()[0]

    print(f"      Gesamtzahl Orte: {total:,}")
    print(f"      Aktuelle Hauptorte: {current_hauptorte:,}")
    print(f"      Eindeutige (Kreis, Name) Kombinationen: {unique_combinations:,}")

    # Reset all ist_hauptort to 0
    print("\n[3/4] Setze alle ist_hauptort auf 0...")
    cursor.execute("UPDATE geo_ort SET ist_hauptort = 0")
    print(f"      {cursor.rowcount:,} Einträge aktualisiert")

    # Set ist_hauptort = 1 for entry with lowest PLZ per (kreis_id, name)
    print("\n[4/4] Setze ist_hauptort = 1 für niedrigste PLZ pro (Kreis, Name)...")

    # SQLite doesn't support UPDATE with JOIN directly, so we use a subquery
    # This query finds the id of the row with MIN(plz) for each (kreis_id, name) group
    cursor.execute("""
        UPDATE geo_ort
        SET ist_hauptort = 1
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
    """)
    updated = cursor.rowcount
    print(f"      {updated:,} Hauptorte gesetzt")

    # Commit changes
    conn.commit()

    # Verify results
    print("\n" + "=" * 60)
    print("Verifikation")
    print("=" * 60)

    cursor.execute("SELECT COUNT(*) FROM geo_ort WHERE ist_hauptort = 1")
    new_hauptorte = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT kreis_id, name, COUNT(*) as cnt
            FROM geo_ort
            WHERE ist_hauptort = 1
            GROUP BY kreis_id, name
            HAVING COUNT(*) > 1
        )
    """)
    duplicates = cursor.fetchone()[0]

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

    cursor.execute("""
        SELECT k.name as kreis, o.name as ort, o.plz, o.ist_hauptort
        FROM geo_ort o
        JOIN geo_kreis k ON o.kreis_id = k.id
        WHERE o.name = 'Berlin'
        ORDER BY o.plz
        LIMIT 10
    """)

    print("\nBerlin (erste 10 PLZ):")
    print(f"{'Kreis':<30} {'Ort':<15} {'PLZ':<10} {'Hauptort'}")
    print("-" * 65)
    for row in cursor.fetchall():
        hauptort = "ja" if row[3] else ""
        print(f"{row[0]:<30} {row[1]:<15} {row[2]:<10} {hauptort}")

    cursor.execute("""
        SELECT k.name as kreis, o.name as ort, o.plz, o.ist_hauptort
        FROM geo_ort o
        JOIN geo_kreis k ON o.kreis_id = k.id
        WHERE o.name = 'München'
        ORDER BY o.plz
        LIMIT 10
    """)

    print("\nMünchen (erste 10 PLZ):")
    print(f"{'Kreis':<30} {'Ort':<15} {'PLZ':<10} {'Hauptort'}")
    print("-" * 65)
    for row in cursor.fetchall():
        hauptort = "ja" if row[3] else ""
        print(f"{row[0]:<30} {row[1]:<15} {row[2]:<10} {hauptort}")

    conn.close()
    print("\nFertig!")


if __name__ == "__main__":
    main()
