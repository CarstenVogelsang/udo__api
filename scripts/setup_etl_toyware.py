#!/usr/bin/env python3
"""
Setup ETL configuration for Toyware Legacy Database.

Creates:
- EtlSource: toyware_mssql
- EtlTableMapping: spi_tStore → com_unternehmen
- EtlFieldMappings: All field mappings with transformations

Run: uv run python scripts/setup_etl_toyware.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
from app.models.etl import EtlSource, EtlTableMapping, EtlFieldMapping

settings = get_settings()


def get_db_session():
    """Creates a synchronous database session."""
    db_url = settings.database_url_sync
    engine = create_engine(db_url, echo=False)

    # Create ETL tables if they don't exist
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return Session(), engine


def setup_toyware_etl():
    """Sets up ETL configuration for Toyware import."""
    session, engine = get_db_session()

    print("=" * 70)
    print("ETL-Setup für Toyware Legacy-Datenbank")
    print("=" * 70)

    try:
        # 1. Create or get EtlSource
        print("\n1. EtlSource erstellen/aktualisieren...")
        existing_source = session.execute(
            select(EtlSource).where(EtlSource.name == "toyware_mssql")
        ).scalar_one_or_none()

        if existing_source:
            print(f"   -> Source existiert bereits: {existing_source.id}")
            source = existing_source
        else:
            source = EtlSource(
                name="toyware_mssql",
                description="Legacy Toyware MS SQL Server Datenbank",
                connection_type="mssql",
                connection_string="env:MSSQL_*",  # Use env variables
                is_active=True,
            )
            session.add(source)
            session.flush()
            print(f"   -> Neue Source erstellt: {source.id}")

        # 2. Create or get EtlTableMapping for spi_tStore → com_unternehmen
        print("\n2. TableMapping erstellen/aktualisieren...")
        existing_mapping = session.execute(
            select(EtlTableMapping).where(
                EtlTableMapping.source_id == source.id,
                EtlTableMapping.source_table == "spi_tStore",
                EtlTableMapping.target_table == "com_unternehmen",
            )
        ).scalar_one_or_none()

        if existing_mapping:
            print(f"   -> TableMapping existiert bereits: {existing_mapping.id}")
            table_mapping = existing_mapping
        else:
            table_mapping = EtlTableMapping(
                source_id=source.id,
                source_table="spi_tStore",
                source_pk_field="kStore",
                target_table="com_unternehmen",
                target_pk_field="legacy_id",
                is_active=True,
            )
            session.add(table_mapping)
            session.flush()
            print(f"   -> Neues TableMapping erstellt: {table_mapping.id}")

        # 3. Create FieldMappings
        print("\n3. FieldMappings erstellen...")

        field_mappings = [
            {
                "source_field": "kStore",
                "target_field": "legacy_id",
                "transform": "to_int",
                "is_required": True,
            },
            {
                "source_field": "dStatusUnternehmen",
                "target_field": "status_datum",
                "transform": None,
                "is_required": False,
            },
            {
                "source_field": "cKurzname",
                "target_field": "kurzname",
                "transform": "trim",
                "is_required": False,
            },
            {
                "source_field": "cFirmierung",
                "target_field": "firmierung",
                "transform": "trim",
                "is_required": False,
            },
            {
                "source_field": "cStrasse",
                "target_field": "strasse",
                "transform": "trim",
                "is_required": False,
            },
            {
                "source_field": "cStrasseHausNr",
                "target_field": "strasse_hausnr",
                "transform": "trim",
                "is_required": False,
            },
            {
                "source_field": "kGeoOrt",
                "target_field": "geo_ort_id",
                "transform": "fk_lookup:geo_ort.legacy_id",
                "is_required": False,
            },
        ]

        created = 0
        skipped = 0

        for fm_data in field_mappings:
            # Check if field mapping already exists
            existing_fm = session.execute(
                select(EtlFieldMapping).where(
                    EtlFieldMapping.table_mapping_id == table_mapping.id,
                    EtlFieldMapping.source_field == fm_data["source_field"],
                )
            ).scalar_one_or_none()

            if existing_fm:
                skipped += 1
                continue

            field_mapping = EtlFieldMapping(
                table_mapping_id=table_mapping.id,
                **fm_data
            )
            session.add(field_mapping)
            created += 1

        session.commit()
        print(f"   -> {created} FieldMappings erstellt, {skipped} übersprungen")

        # 4. Summary
        print("\n" + "=" * 70)
        print("ETL-Setup abgeschlossen!")
        print("=" * 70)
        print(f"\nSource:       {source.name} ({source.id})")
        print(f"TableMapping: {table_mapping.source_table} → {table_mapping.target_table}")
        print(f"FieldMappings: {created + skipped} total")
        print("\nNächster Schritt:")
        print("  uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStore")

    except Exception as e:
        session.rollback()
        print(f"\nFehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    setup_toyware_etl()
