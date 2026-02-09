#!/usr/bin/env python3
"""
Setup ETL configuration for e-vendo Smartmail Excel import.

Creates:
- EtlSource: ev_smartmail (connection_type="excel")
- EtlTableMapping: excel_sheet → com_unternehmen
- EtlTableMapping: excel_sheet → com_kontakt
- EtlFieldMappings for all column mappings

Run: uv run python scripts/setup_excel_import_ev_smartmail.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
from app.models.etl import EtlSource, EtlTableMapping, EtlFieldMapping
# Ensure com models are loaded for table creation
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
    ("Firma", "kurzname", "trim", "always"),
    ("Firma", "firmierung", "trim", "always"),
    ("Straße", "strasse", "split_street_name", "if_empty"),
    ("Straße", "strasse_hausnr", "split_street_hausnr", "if_empty"),
    ("PLZ", "geo_ort_id", "normalize_plz", "if_empty"),
    ("Website", "website", "normalize_url", "if_empty"),
    ("E-Mail", "email", "normalize_email", "if_empty"),
    ("Telefonnummer", "telefon", "normalize_phone", "if_empty"),
    # External IDs (special transform notation)
    ("subscriber_id", "_extid", "external_id:smartmail.subscriber_id", "always"),
    ("e-vendo KundenNr", "_extid", "external_id:evendo.kundennr", "always"),
]

KONTAKT_FIELDS = [
    ("Anrede", "anrede", "extract_anrede", "if_empty"),
    ("Vorname", "vorname", "trim", "always"),
    ("Nachname", "nachname", "trim", "always"),
    ("E-Mail", "email", "normalize_email", "always"),
    ("Telefonnummer", "telefon", "normalize_phone", "if_empty"),
]


def setup_ev_smartmail():
    """Sets up ETL configuration for e-vendo Smartmail Excel import."""
    session, engine = get_sqlite_session()

    print("=" * 70)
    print("ETL-Setup für e-vendo Smartmail Excel Import")
    print("=" * 70)

    try:
        # 1. Create or get EtlSource
        print("\n1. EtlSource erstellen/aktualisieren...")
        existing = session.execute(
            select(EtlSource).where(EtlSource.name == "ev_smartmail")
        ).scalar_one_or_none()

        if existing:
            print(f"   -> Source existiert bereits: {existing.id}")
            source = existing
            # Delete existing mappings for clean re-setup
            for tm in source.table_mappings:
                for fm in tm.field_mappings:
                    session.delete(fm)
                session.delete(tm)
            session.flush()
            print("   -> Bestehende Mappings gelöscht für Neuanlage")
        else:
            source = EtlSource(
                name="ev_smartmail",
                description="e-vendo Smartmail Newsletter-Empfänger (Excel)",
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
            source_pk_field="subscriber_id",
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
            source_pk_field="subscriber_id",
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
        print(f"Source: ev_smartmail ({source.id})")
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
    setup_ev_smartmail()
