#!/usr/bin/env python3
"""
Generic ETL Runner - Executes imports based on database configuration.

Reads ETL configuration from the database and executes the import
using the configured field mappings and transformations.

Usage:
    uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStore
    uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStore --dry-run

IMPORTANT: Legacy database is READ-ONLY! No writes allowed.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymssql
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
from app.models.etl import EtlSource, EtlTableMapping, EtlFieldMapping, EtlImportLog

settings = get_settings()


# ============ Transformation Registry ============

def _trim(value: Any) -> Any:
    """Strip whitespace from strings."""
    if isinstance(value, str):
        return value.strip()
    return value


def _upper(value: Any) -> Any:
    """Convert to uppercase."""
    if isinstance(value, str):
        return value.upper()
    return value


def _lower(value: Any) -> Any:
    """Convert to lowercase."""
    if isinstance(value, str):
        return value.lower()
    return value


def _to_int(value: Any) -> int | None:
    """Convert to integer."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_float(value: Any) -> float | None:
    """Convert to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _to_str(value: Any) -> str | None:
    """Convert to string."""
    if value is None:
        return None
    return str(value)


TRANSFORMS = {
    "trim": _trim,
    "upper": _upper,
    "lower": _lower,
    "to_int": _to_int,
    "to_float": _to_float,
    "to_str": _to_str,
}


# ============ Database Connections ============

def get_legacy_connection():
    """Creates a connection to the legacy MS SQL Server (READ-ONLY!)."""
    return pymssql.connect(
        server=settings.mssql_host,
        port=settings.mssql_port,
        database=settings.mssql_database,
        user=settings.mssql_user,
        password=settings.mssql_password,
        as_dict=True,
    )


def get_sqlite_session():
    """Creates a synchronous SQLite session."""
    db_url = settings.sqlite_database_url.replace("+aiosqlite", "")
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


# ============ ETL Runner ============

class EtlRunner:
    """Executes ETL imports based on database configuration."""

    def __init__(self, dry_run: bool = False):
        self.session, self.engine = get_sqlite_session()
        self.dry_run = dry_run
        self._fk_caches: dict[str, dict[Any, str]] = {}

    def run(self, source_name: str, source_table: str) -> dict:
        """
        Run ETL import for specified source and table.

        Args:
            source_name: Name of the EtlSource
            source_table: Name of the source table to import

        Returns:
            Dict with import statistics
        """
        print(f"\n{'=' * 70}")
        print(f"ETL Import: {source_name} / {source_table}")
        print(f"Modus: {'DRY-RUN (keine Änderungen)' if self.dry_run else 'LIVE'}")
        print(f"{'=' * 70}")

        # 1. Load configuration
        source, table_mapping, field_mappings = self._load_config(source_name, source_table)
        if not table_mapping:
            return {"success": False, "error": "Konfiguration nicht gefunden"}

        print(f"\nTarget: {table_mapping.target_table}")
        print(f"PK Mapping: {table_mapping.source_pk_field} → {table_mapping.target_pk_field}")
        print(f"Field Mappings: {len(field_mappings)}")

        # 2. Build FK lookup caches
        self._build_fk_caches(field_mappings)

        # 3. Create import log
        import_log = None
        if not self.dry_run:
            import_log = EtlImportLog(
                table_mapping_id=table_mapping.id,
                status="running",
            )
            self.session.add(import_log)
            self.session.flush()

        # 4. Execute import
        try:
            stats = self._execute_import(source, table_mapping, field_mappings)

            if import_log:
                import_log.status = "success"
                import_log.records_read = stats["read"]
                import_log.records_created = stats["created"]
                import_log.records_updated = stats["updated"]
                import_log.records_failed = stats["failed"]
                import_log.finished_at = datetime.utcnow()

            if not self.dry_run:
                self.session.commit()

            return {
                "success": True,
                "records_read": stats["read"],
                "records_created": stats["created"],
                "records_updated": stats["updated"],
                "records_failed": stats["failed"],
            }

        except Exception as e:
            if import_log:
                import_log.status = "failed"
                import_log.error_message = str(e)
                import_log.finished_at = datetime.utcnow()
                self.session.commit()

            raise

    def _load_config(
        self,
        source_name: str,
        source_table: str
    ) -> tuple[EtlSource | None, EtlTableMapping | None, list[EtlFieldMapping]]:
        """Load ETL configuration from database."""
        print("\nLade Konfiguration...")

        # Load source
        source = self.session.execute(
            select(EtlSource).where(
                EtlSource.name == source_name,
                EtlSource.is_active == True,
            )
        ).scalar_one_or_none()

        if not source:
            print(f"   FEHLER: Source '{source_name}' nicht gefunden oder inaktiv")
            return None, None, []

        # Load table mapping
        table_mapping = self.session.execute(
            select(EtlTableMapping).where(
                EtlTableMapping.source_id == source.id,
                EtlTableMapping.source_table == source_table,
                EtlTableMapping.is_active == True,
            )
        ).scalar_one_or_none()

        if not table_mapping:
            print(f"   FEHLER: TableMapping für '{source_table}' nicht gefunden oder inaktiv")
            return source, None, []

        # Load field mappings
        field_mappings = self.session.execute(
            select(EtlFieldMapping).where(
                EtlFieldMapping.table_mapping_id == table_mapping.id
            )
        ).scalars().all()

        print(f"   -> Source: {source.name} ({source.connection_type})")
        print(f"   -> TableMapping: {table_mapping.source_table} → {table_mapping.target_table}")
        print(f"   -> FieldMappings: {len(field_mappings)}")

        return source, table_mapping, list(field_mappings)

    def _build_fk_caches(self, field_mappings: list[EtlFieldMapping]):
        """Build FK lookup caches for all fk_lookup transformations."""
        print("\nBaue FK-Lookup-Caches...")

        for fm in field_mappings:
            if fm.transform and fm.transform.startswith("fk_lookup:"):
                lookup_spec = fm.transform[10:]  # Remove "fk_lookup:"
                if "." in lookup_spec:
                    table, field = lookup_spec.split(".", 1)
                    cache_key = f"{table}.{field}"

                    if cache_key not in self._fk_caches:
                        print(f"   -> Lade {cache_key}...")
                        query = text(f"SELECT {field}, id FROM {table} WHERE {field} IS NOT NULL")
                        result = self.session.execute(query)
                        rows = result.fetchall()
                        self._fk_caches[cache_key] = {row[0]: row[1] for row in rows}
                        print(f"      {len(self._fk_caches[cache_key])} Einträge")

    def _apply_transform(self, value: Any, transform: str | None) -> Any:
        """Apply a transformation to a value."""
        if transform is None:
            return value

        # Handle FK lookup
        if transform.startswith("fk_lookup:"):
            lookup_spec = transform[10:]
            if "." in lookup_spec:
                table, field = lookup_spec.split(".", 1)
                cache_key = f"{table}.{field}"
                if cache_key in self._fk_caches:
                    return self._fk_caches[cache_key].get(value)
            return None

        # Handle standard transforms
        if transform in TRANSFORMS:
            return TRANSFORMS[transform](value)

        return value

    def _execute_import(
        self,
        source: EtlSource,
        table_mapping: EtlTableMapping,
        field_mappings: list[EtlFieldMapping]
    ) -> dict:
        """Execute the actual import."""
        print("\nStarte Import...")

        stats = {"read": 0, "created": 0, "updated": 0, "failed": 0}

        # Build SELECT query for source fields
        source_fields = [fm.source_field for fm in field_mappings]
        source_fields_str = ", ".join(source_fields)
        source_query = f"SELECT {source_fields_str} FROM dbo.{table_mapping.source_table}"

        # Connect to legacy DB
        legacy_conn = get_legacy_connection()
        cursor = legacy_conn.cursor()

        try:
            cursor.execute(source_query)

            batch_size = 1000
            batch_count = 0

            for row in cursor:
                stats["read"] += 1

                try:
                    # Transform row to target format
                    target_data = {}
                    pk_value = None

                    for fm in field_mappings:
                        source_value = row.get(fm.source_field)
                        target_value = self._apply_transform(source_value, fm.transform)

                        # Handle default value
                        if target_value is None and fm.default_value:
                            target_value = fm.default_value

                        target_data[fm.target_field] = target_value

                        # Track PK value
                        if fm.target_field == table_mapping.target_pk_field:
                            pk_value = target_value

                    if pk_value is None:
                        stats["failed"] += 1
                        continue

                    # Check if record exists
                    if not self.dry_run:
                        existing_query = text(
                            f"SELECT id FROM {table_mapping.target_table} "
                            f"WHERE {table_mapping.target_pk_field} = :pk"
                        )
                        existing = self.session.execute(
                            existing_query, {"pk": pk_value}
                        ).fetchone()

                        if existing:
                            # Update existing record
                            update_fields = ", ".join(
                                f"{k} = :{k}" for k in target_data.keys()
                                if k != table_mapping.target_pk_field
                            )
                            update_query = text(
                                f"UPDATE {table_mapping.target_table} "
                                f"SET {update_fields}, aktualisiert_am = :aktualisiert_am "
                                f"WHERE {table_mapping.target_pk_field} = :pk"
                            )
                            self.session.execute(
                                update_query,
                                {**target_data, "pk": pk_value, "aktualisiert_am": datetime.utcnow()}
                            )
                            stats["updated"] += 1
                        else:
                            # Insert new record
                            target_data["id"] = str(uuid4())
                            target_data["erstellt_am"] = datetime.utcnow()
                            target_data["aktualisiert_am"] = datetime.utcnow()

                            columns = ", ".join(target_data.keys())
                            placeholders = ", ".join(f":{k}" for k in target_data.keys())
                            insert_query = text(
                                f"INSERT INTO {table_mapping.target_table} ({columns}) "
                                f"VALUES ({placeholders})"
                            )
                            self.session.execute(insert_query, target_data)
                            stats["created"] += 1
                    else:
                        # Dry run - just count
                        stats["created"] += 1

                except Exception as e:
                    stats["failed"] += 1
                    if stats["failed"] <= 5:
                        print(f"   FEHLER bei Zeile {stats['read']}: {e}")

                # Commit in batches
                batch_count += 1
                if batch_count >= batch_size:
                    if not self.dry_run:
                        self.session.commit()
                    batch_count = 0
                    print(f"   ... {stats['read']} Zeilen verarbeitet")

            # Final commit
            if not self.dry_run:
                self.session.commit()

        finally:
            cursor.close()
            legacy_conn.close()

        print(f"\n{'=' * 70}")
        print("Import abgeschlossen!")
        print(f"{'=' * 70}")
        print(f"Gelesen:     {stats['read']}")
        print(f"Erstellt:    {stats['created']}")
        print(f"Aktualisiert:{stats['updated']}")
        print(f"Fehler:      {stats['failed']}")

        return stats

    def close(self):
        """Close database session."""
        self.session.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ETL Runner - Import data based on database configuration"
    )
    parser.add_argument(
        "--source", "-s",
        required=True,
        help="Name der EtlSource (z.B. toyware_mssql)"
    )
    parser.add_argument(
        "--table", "-t",
        required=True,
        help="Name der Quell-Tabelle (z.B. spi_tStore)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Testlauf ohne Schreiben in die Ziel-Datenbank"
    )

    args = parser.parse_args()

    runner = EtlRunner(dry_run=args.dry_run)

    try:
        result = runner.run(args.source, args.table)

        if not result["success"]:
            print(f"\nFEHLER: {result.get('error', 'Unbekannter Fehler')}")
            sys.exit(1)

    except Exception as e:
        print(f"\nFEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        runner.close()


if __name__ == "__main__":
    main()
