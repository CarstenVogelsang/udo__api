#!/usr/bin/env python3
"""
Setup ETL configuration for Organisation (StoreGruppe) import.

Creates:
- EtlTableMapping: spi_tStoreGruppe → com_organisation
- EtlFieldMappings: kStoreGruppe → legacy_id, cKurzname → kurzname

Prerequisites:
- EtlSource 'toyware_mssql' must exist (run setup_etl_toyware.py first)

Run: uv run python scripts/setup_etl_organisation.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
from app.models.etl import EtlSource, EtlTableMapping, EtlFieldMapping

settings = get_settings()


def get_sqlite_session():
    """Creates a synchronous SQLite session."""
    db_url = settings.sqlite_database_url.replace("+aiosqlite", "")
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def setup_organisation_etl():
    """Sets up ETL configuration for Organisation import."""
    session, engine = get_sqlite_session()

    print("=" * 70)
    print("ETL-Setup für Organisation (StoreGruppe)")
    print("=" * 70)

    try:
        # 1. Get existing toyware_mssql source
        print("\n1. Suche EtlSource 'toyware_mssql'...")
        source = session.execute(
            select(EtlSource).where(EtlSource.name == "toyware_mssql")
        ).scalar_one_or_none()

        if not source:
            print("\nFEHLER: EtlSource 'toyware_mssql' nicht gefunden!")
            print("Bitte zuerst ausführen:")
            print("  uv run python scripts/setup_etl_toyware.py")
            sys.exit(1)

        print(f"   -> Gefunden: {source.name} ({source.id})")

        # 2. Create TableMapping for spi_tStoreGruppe → com_organisation
        print("\n2. TableMapping erstellen...")
        existing_mapping = session.execute(
            select(EtlTableMapping).where(
                EtlTableMapping.source_id == source.id,
                EtlTableMapping.source_table == "spi_tStoreGruppe",
                EtlTableMapping.target_table == "com_organisation",
            )
        ).scalar_one_or_none()

        if existing_mapping:
            print(f"   -> Existiert bereits: {existing_mapping.id}")
            table_mapping = existing_mapping
        else:
            table_mapping = EtlTableMapping(
                source_id=source.id,
                source_table="spi_tStoreGruppe",
                source_pk_field="kStoreGruppe",
                target_table="com_organisation",
                target_pk_field="legacy_id",
                is_active=True,
            )
            session.add(table_mapping)
            session.flush()
            print(f"   -> Neu erstellt: {table_mapping.id}")

        # 3. Create FieldMappings
        print("\n3. FieldMappings erstellen...")

        field_mappings = [
            {
                "source_field": "kStoreGruppe",
                "target_field": "legacy_id",
                "transform": "to_int",
                "is_required": True,
            },
            {
                "source_field": "cKurzname",
                "target_field": "kurzname",
                "transform": "trim",
                "is_required": True,
            },
        ]

        created = 0
        skipped = 0

        for fm_data in field_mappings:
            existing_fm = session.execute(
                select(EtlFieldMapping).where(
                    EtlFieldMapping.table_mapping_id == table_mapping.id,
                    EtlFieldMapping.source_field == fm_data["source_field"],
                )
            ).scalar_one_or_none()

            if existing_fm:
                skipped += 1
                print(f"   -> {fm_data['source_field']} → {fm_data['target_field']}: existiert")
            else:
                field_mapping = EtlFieldMapping(
                    table_mapping_id=table_mapping.id,
                    **fm_data
                )
                session.add(field_mapping)
                created += 1
                print(f"   -> {fm_data['source_field']} → {fm_data['target_field']}: erstellt")

        session.commit()

        print("\n" + "=" * 70)
        print("ETL-Setup abgeschlossen!")
        print("=" * 70)
        print(f"\nTableMapping: {table_mapping.source_table} → {table_mapping.target_table}")
        print(f"FieldMappings: {created} erstellt, {skipped} übersprungen")
        print("\nNächster Schritt:")
        print("  uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStoreGruppe")

    except Exception as e:
        session.rollback()
        print(f"\nFehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    setup_organisation_etl()
