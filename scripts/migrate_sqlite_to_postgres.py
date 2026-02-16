#!/usr/bin/env python3
"""
Einmalige Migration: SQLite → PostgreSQL.

Erstellt das Schema via SQLAlchemy-Modelle in PostgreSQL,
kopiert alle Daten aus der bestehenden SQLite-DB,
und stempelt die aktuelle Alembic-Version.

Usage:
    uv run python scripts/migrate_sqlite_to_postgres.py
    uv run python scripts/migrate_sqlite_to_postgres.py --dry-run
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from sqlalchemy import create_engine, text, inspect, Boolean
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
# Ensure all models are imported for metadata
from app.models import base as _base  # noqa: F401
from app.models import etl as _etl  # noqa: F401
from app.models import com as _com  # noqa: F401
from app.models import partner as _partner  # noqa: F401
from app.models import smart_filter as _sf  # noqa: F401
from app.models import setting as _setting  # noqa: F401

settings = get_settings()

SQLITE_PATH = Path(__file__).parent.parent / "data" / "udo.db"

# Latest Alembic revision (including Märklin import models)
ALEMBIC_HEAD = "b93537e1486f"


def get_sqlite_tables() -> list[str]:
    """Get all table names from SQLite."""
    conn = sqlite3.connect(str(SQLITE_PATH))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_sqlite_data(table: str) -> tuple[list[str], list[tuple]]:
    """Get all data from a SQLite table."""
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(f"SELECT * FROM [{table}]")
    rows = cursor.fetchall()
    if rows:
        columns = list(rows[0].keys())
        data = [tuple(row) for row in rows]
    else:
        columns = []
        data = []
    conn.close()
    return columns, data


def migrate(dry_run: bool = False):
    """Run the full migration."""
    print("=" * 70)
    print("SQLite → PostgreSQL Migration")
    print(f"Modus: {'DRY-RUN (keine Änderungen)' if dry_run else 'LIVE'}")
    print("=" * 70)

    if not SQLITE_PATH.exists():
        print(f"\nFEHLER: SQLite-DB nicht gefunden: {SQLITE_PATH}")
        sys.exit(1)

    pg_url = settings.database_url_sync
    print(f"\nPostgreSQL: {pg_url}")
    print(f"SQLite:     {SQLITE_PATH}")

    # Create PostgreSQL engine
    pg_engine = create_engine(pg_url, echo=False)

    # 1. Create schema
    print("\n[1/4] Erstelle Schema in PostgreSQL...")
    if not dry_run:
        Base.metadata.create_all(pg_engine)
    print("      Schema erstellt (alle Tabellen)")

    # 2. Check which tables exist in both SQLite and PostgreSQL
    print("\n[2/4] Prüfe Tabellen...")
    sqlite_tables = get_sqlite_tables()
    pg_inspector = inspect(pg_engine)
    pg_tables = pg_inspector.get_table_names() if not dry_run else []

    print(f"      SQLite:     {len(sqlite_tables)} Tabellen")
    if not dry_run:
        print(f"      PostgreSQL: {len(pg_tables)} Tabellen")

    # 3. Copy data
    print("\n[3/4] Kopiere Daten...")
    Session = sessionmaker(bind=pg_engine)
    session = Session()

    # Temporarily disable FK constraints for clean bulk import
    if not dry_run:
        session.execute(text("SET session_replication_role = 'replica'"))

    total_records = 0
    table_stats = {}

    # Order tables to respect foreign key constraints
    # Parent tables first, then dependent tables
    table_order = [
        # Base/standalone tables first
        "geo_land",
        "geo_bundesland",
        "geo_regierungsbezirk",
        "geo_kreis",
        "geo_ort",
        "geo_ortsteil",
        "bas_color_palette",
        "api_partner",
        "etl_source",
        # Tables with FKs to above
        "com_unternehmen",
        "com_organisation",
        "com_kontakt",
        "com_external_id",
        "com_unternehmen_identifikation",
        "com_unternehmen_organisation",
        # ETL tables
        "etl_table_mapping",
        "etl_field_mapping",
        "etl_import_log",
        "etl_import_record",
        # Usage/Billing
        "api_usage",
        "api_usage_daily",
        "api_billing_account",
        "api_credit_transaction",
        "api_invoice",
        # Plugin tables
        "plg_kategorie",
        "plg_projekttyp",
        "plg_plugin",
        "plg_plugin_version",
        "plg_preis",
        "plg_projekt",
        "plg_lizenz",
        "plg_lizenz_historie",
        # Other
        "smart_filter",
        "system_setting",
    ]

    # Add any tables not in the order list
    for t in sqlite_tables:
        if t not in table_order:
            table_order.append(t)

    # Build boolean column map for type conversion (SQLite 0/1 → PG bool)
    bool_columns: dict[str, set[str]] = {}
    if not dry_run:
        for table in pg_tables:
            pg_cols = pg_inspector.get_columns(table)
            bools = {
                c["name"] for c in pg_cols
                if isinstance(c["type"], Boolean)
            }
            if bools:
                bool_columns[table] = bools

    for table in table_order:
        if table not in sqlite_tables:
            continue

        columns, rows = get_sqlite_data(table)
        if not rows:
            print(f"   {table:40s} → 0 Zeilen (leer)")
            table_stats[table] = 0
            continue

        # Filter columns that exist in PostgreSQL table
        if not dry_run:
            pg_col_names = [c["name"] for c in pg_inspector.get_columns(table)] \
                if table in pg_tables else columns
            # Only use columns that exist in both
            valid_indices = [
                i for i, c in enumerate(columns) if c in pg_col_names
            ]
            filtered_columns = [columns[i] for i in valid_indices]
            filtered_rows = [
                tuple(row[i] for i in valid_indices) for row in rows
            ]

            # Convert SQLite integer booleans (0/1) to Python bools
            table_bools = bool_columns.get(table, set())
            if table_bools:
                bool_indices = [
                    i for i, c in enumerate(filtered_columns)
                    if c in table_bools
                ]
                if bool_indices:
                    converted = []
                    for row in filtered_rows:
                        row_list = list(row)
                        for idx in bool_indices:
                            val = row_list[idx]
                            if val is not None:
                                row_list[idx] = bool(val)
                        converted.append(tuple(row_list))
                    filtered_rows = converted
        else:
            filtered_columns = columns
            filtered_rows = rows

        if not dry_run:
            try:
                # Build INSERT statement
                cols = ", ".join(f'"{c}"' for c in filtered_columns)
                placeholders = ", ".join(
                    f":{c}" for c in filtered_columns
                )
                insert_sql = text(
                    f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})'
                )

                # Insert in batches
                batch_size = 1000
                for i in range(0, len(filtered_rows), batch_size):
                    batch = filtered_rows[i:i + batch_size]
                    params = [
                        dict(zip(filtered_columns, row)) for row in batch
                    ]
                    session.execute(insert_sql, params)

                session.commit()
            except Exception as e:
                session.rollback()
                print(f"   {table:40s} → FEHLER: {e}")
                table_stats[table] = -1
                continue

        count = len(rows)
        total_records += count
        table_stats[table] = count
        print(f"   {table:40s} → {count:,} Zeilen")

    # Re-enable FK constraints
    if not dry_run:
        session.execute(text("SET session_replication_role = 'origin'"))
        session.commit()

    # 4. Stamp Alembic version
    print(f"\n[4/4] Stempel Alembic-Version: {ALEMBIC_HEAD}")
    if not dry_run:
        session.execute(text(
            "CREATE TABLE IF NOT EXISTS alembic_version ("
            "version_num VARCHAR(32) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        ))
        session.execute(text("DELETE FROM alembic_version"))
        session.execute(text(
            "INSERT INTO alembic_version (version_num) VALUES (:v)"
        ), {"v": ALEMBIC_HEAD})
        session.commit()

    session.close()
    pg_engine.dispose()

    # Summary
    print("\n" + "=" * 70)
    print("Migration abgeschlossen!")
    print("=" * 70)
    print(f"\nTabellen:        {len(table_stats)}")
    print(f"Datensätze:      {total_records:,}")
    errors = sum(1 for v in table_stats.values() if v < 0)
    if errors:
        print(f"Fehler:          {errors} Tabellen")
    if dry_run:
        print("\n[DRY-RUN] Keine Änderungen vorgenommen.")


def main():
    parser = argparse.ArgumentParser(
        description="Migriert SQLite-Daten nach PostgreSQL"
    )
    parser.add_argument(
        "--dry-run", "-d", action="store_true",
        help="Testlauf ohne Schreiben"
    )
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
