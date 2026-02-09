#!/usr/bin/env python3
"""
Setup ETL configuration for SC3 Händler (Asana export) Excel import.

Creates:
- EtlSource: sc3_haendler_asana (connection_type="excel")
- EtlTableMapping: excel_sheet → com_unternehmen
- EtlTableMapping: excel_sheet → com_kontakt
- EtlFieldMappings for all column mappings

Run: uv run python scripts/setup_excel_import_sc3_haendler.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
from app.models.etl import EtlSource, EtlTableMapping, EtlFieldMapping
from app.models import com  # noqa: F401

settings = get_settings()


def get_sqlite_session():
    """Creates a synchronous SQLite session."""
    db_url = settings.sqlite_database_url.replace("+aiosqlite", "")
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


# Field mapping definitions: (source_field, target_field, transform, update_rule)
UNTERNEHMEN_FIELDS = [
    ("Firmierung", "kurzname", "trim", "always"),
    ("Firmierung", "firmierung", "trim", "always"),
    ("Straße_Zentrale", "strasse", "split_street_name", "if_empty"),
    ("Straße_Zentrale", "strasse_hausnr", "split_street_hausnr", "if_empty"),
    ("Ort_Zentrale", "geo_ort_id", "extract_plz", "if_empty"),
    ("Website_URL", "website", "normalize_url", "if_empty"),
    ("EMail_allgemein", "email", "normalize_email", "if_empty"),
    ("Telefon_allgemein", "telefon", "normalize_phone", "if_empty"),
    # External IDs
    ("Task ID", "_extid", "external_id:asana.task_id", "always"),
    ("BD Kd-Nr.", "_extid", "external_id:buschdata.kundennr", "always"),
]

KONTAKT_FIELDS = [
    ("AP1_Anrede", "anrede", "extract_anrede", "if_empty"),
    ("AP1_Anrede", "vorname", "extract_vorname", "always"),
    ("AP1_Anrede", "nachname", "extract_nachname", "always"),
    ("EMail_allgemein", "email", "normalize_email", "always"),
    ("Telefon_allgemein", "telefon", "normalize_phone", "if_empty"),
]


def setup_sc3_haendler():
    """Sets up ETL configuration for SC3 Händler Excel import."""
    session, engine = get_sqlite_session()

    print("=" * 70)
    print("ETL-Setup für SC3 Händler (Asana Export) Excel Import")
    print("=" * 70)

    try:
        # 1. Create or get EtlSource
        print("\n1. EtlSource erstellen/aktualisieren...")
        existing = session.execute(
            select(EtlSource).where(EtlSource.name == "sc3_haendler_asana")
        ).scalar_one_or_none()

        if existing:
            print(f"   -> Source existiert bereits: {existing.id}")
            source = existing
            for tm in source.table_mappings:
                for fm in tm.field_mappings:
                    session.delete(fm)
                session.delete(tm)
            session.flush()
            print("   -> Bestehende Mappings gelöscht für Neuanlage")
        else:
            source = EtlSource(
                name="sc3_haendler_asana",
                description="SC3 Händler aus Asana-Projekt (Excel)",
                connection_type="excel",
                connection_string=None,
                is_active=True,
            )
            session.add(source)
            session.flush()
            print(f"   -> Source erstellt: {source.id}")

        # 2. Create TableMapping for Unternehmen
        print("\n2. TableMapping Unternehmen erstellen...")
        tm_u = EtlTableMapping(
            source_id=source.id,
            source_table="excel_sheet",
            source_pk_field="Task ID",
            target_table="com_unternehmen",
            target_pk_field="id",
            is_active=True,
        )
        session.add(tm_u)
        session.flush()
        print(f"   -> Mapping erstellt: {tm_u.id}")

        # 3. Create FieldMappings for Unternehmen
        print("\n3. FieldMappings Unternehmen erstellen...")
        for src, tgt, transform, rule in UNTERNEHMEN_FIELDS:
            fm = EtlFieldMapping(
                table_mapping_id=tm_u.id,
                source_field=src,
                target_field=tgt,
                transform=transform,
                update_rule=rule,
            )
            session.add(fm)
            print(f"   {src:25s} → {tgt:20s} [{transform}] ({rule})")

        # 4. Create TableMapping for Kontakt
        print("\n4. TableMapping Kontakt erstellen...")
        tm_k = EtlTableMapping(
            source_id=source.id,
            source_table="excel_sheet",
            source_pk_field="Task ID",
            target_table="com_kontakt",
            target_pk_field="id",
            is_active=True,
        )
        session.add(tm_k)
        session.flush()
        print(f"   -> Mapping erstellt: {tm_k.id}")

        # 5. Create FieldMappings for Kontakt
        print("\n5. FieldMappings Kontakt erstellen...")
        for src, tgt, transform, rule in KONTAKT_FIELDS:
            fm = EtlFieldMapping(
                table_mapping_id=tm_k.id,
                source_field=src,
                target_field=tgt,
                transform=transform,
                update_rule=rule,
            )
            session.add(fm)
            print(f"   {src:25s} → {tgt:20s} [{transform}] ({rule})")

        session.commit()
        print("\n" + "=" * 70)
        print("Setup abgeschlossen!")
        print(f"Source: sc3_haendler_asana ({source.id})")
        print(f"Unternehmen-Mapping: {len(UNTERNEHMEN_FIELDS)} Felder")
        print(f"Kontakt-Mapping: {len(KONTAKT_FIELDS)} Felder")
        print("=" * 70)

    except Exception as e:
        session.rollback()
        print(f"\nFEHLER: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    setup_sc3_haendler()
