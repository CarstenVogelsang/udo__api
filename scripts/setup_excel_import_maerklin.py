#!/usr/bin/env python3
"""
Setup ETL configuration for Märklin Händleradressen Excel import.

Creates:
- EtlSource: maerklin_haendler (connection_type="excel")
- EtlTableMapping: excel_sheet -> com_unternehmen
- EtlTableMapping: excel_sheet -> com_kontakt
- EtlTableMapping: excel_sheet -> com_lieferbeziehung
- EtlTableMapping: excel_sheet -> com_unternehmen_sortiment (3x, per brand flag)
- EtlTableMapping: excel_sheet -> com_unternehmen_dienstleistung
- EtlTableMapping: excel_sheet -> com_bonitaet
- EtlFieldMappings for all column mappings

Run: uv run python scripts/setup_excel_import_maerklin.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import Base
from app.models.etl import EtlSource, EtlTableMapping, EtlFieldMapping
from app.models import com as _com  # noqa: F401
from app.models import base as _base  # noqa: F401

settings = get_settings()


def get_db_session():
    """Creates a synchronous database session."""
    db_url = settings.database_url_sync
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


# ============ Field Mapping Definitions ============
# Format: (source_field, target_field, transform, update_rule)

UNTERNEHMEN_FIELDS = [
    # Status from deletion flag
    ("Löschkennz.", "status_id", "map_loeschkennzeichen", "always"),
    # Company name
    ("Name1", "kurzname", "strip_star_title_case", "if_empty"),
    ("Name1", "firmierung", "build_firmierung:Name2", "if_empty"),
    # Address — raw line for all, parsed only for DACH
    ("Strasse", "adresszeile", "smart_title_case", "always"),
    ("Strasse", "strasse", "split_street_name_dach:Land", "if_empty"),
    ("Strasse", "strasse_hausnr", "split_street_hausnr_dach:Land", "if_empty"),
    # PLZ -> GeoOrt
    ("Postleitzahl", "geo_ort_id", "normalize_plz", "if_empty"),
    # Language
    ("Sprache", "sprache_id", "map_sprache", "if_empty"),
    # Contact info
    ("Telefon-Nr.", "telefon", "normalize_phone_e164:Land", "if_empty"),
    ("Telefax-Nr.", "fax", "normalize_phone_e164:Land", "if_empty"),
    ("Mail-Adresse (Ladenlokal / SAP)", "email", "normalize_email", "if_empty"),
    ("Mail-Adresse (Debitorenstamm SAP)", "email2", "normalize_email", "if_empty"),
    ("Webadresse", "website", "normalize_url", "if_empty"),
    # External ID: Märklin Kunden-Nr.
    ("Kunden-Nr.", "_extid", "external_id:maerklin.kundennr", "always"),
]

KONTAKT_FIELDS = [
    ("Name2", "vorname", "detect_inhaber_vorname:Name1", "always"),
    ("Name2", "nachname", "detect_inhaber_nachname:Name1", "always"),
    ("Name2", "typ", "detect_inhaber_typ:Name1", "always"),
    ("Mail-Adresse (Ladenlokal / SAP)", "email", "normalize_email", "if_empty"),
    ("Telefon-Nr.", "telefon", "normalize_phone_e164:Land", "if_empty"),
]

# Lieferbeziehung: Händler -> Märklin
LIEFERBEZIEHUNG_FIELDS = [
    ("__ref__", "unternehmen_id", "ref_current:id", "always"),
    ("__const__", "lieferant_id", "fk_lookup:com_unternehmen.kurzname", "always"),
    ("Kunden-Nr.", "kundennummer", "to_str", "always"),
    ("Store / SiS / Wandlösung", "store_typ", "map_store_typ", "always"),
    ("Kz.Bonus-Händler", "bonus_haendler", "x_to_bool", "always"),
    ("Kz. \"keine Anzeige in Märklin-Händlersuche\"", "in_haendlersuche", "invert_x_flag", "always"),
    ("Märklin-MHI-Produkte", "ist_mhi", "x_to_bool", "always"),
]

# Sortiment: which brands a dealer carries (each as separate junction)
# Each tuple: (source_flag_field, brand_name)
SORTIMENT_BRANDS = [
    ("Märklin-Produkte", "Märklin"),
    ("Trix-Produkte", "Trix"),
    ("LGB-Produkte", "LGB"),
]

# Dienstleistung: Reparatur-Service
DIENSTLEISTUNG_FIELDS = [
    ("__ref__", "unternehmen_id", "ref_current:id", "always"),
    ("Reparatur-Service", "dienstleistung_id", "x_to_bool", "always"),
]

# Bonität: mapped from Kredit/Auftragssperre
BONITAET_FIELDS = [
    ("__ref__", "unternehmen_id", "ref_current:id", "always"),
    ("Kz. \"Kreditsperre\"", "score", "map_bonitaet_score:Kz. \"Auftragssperre\"", "always"),
]


def create_field_mappings(session, table_mapping_id: str, fields: list, label: str):
    """Create field mappings for a table mapping."""
    for src, tgt, transform, rule in fields:
        fm = EtlFieldMapping(
            table_mapping_id=table_mapping_id,
            source_field=src,
            target_field=tgt,
            transform=transform,
            update_rule=rule,
        )
        # Set default_value for const fields
        if src == "__const__" and "fk_lookup:com_unternehmen.kurzname" in (transform or ""):
            fm.default_value = "Märklin"
        session.add(fm)
        print(f"   {src:50s} -> {tgt:20s} [{transform}] ({rule})")


def setup_maerklin_import():
    """Sets up ETL configuration for Märklin Händler Excel import."""
    session, engine = get_db_session()

    print("=" * 70)
    print("ETL-Setup für Märklin Händleradressen Excel Import")
    print("=" * 70)

    try:
        # 1. Create or get EtlSource
        print("\n1. EtlSource erstellen/aktualisieren...")
        existing = session.execute(
            select(EtlSource).where(EtlSource.name == "maerklin_haendler")
        ).scalar_one_or_none()

        if existing:
            print(f"   -> Source existiert bereits: {existing.id}")
            source = existing
            # Delete existing mappings for clean re-creation
            for tm in source.table_mappings:
                for fm in tm.field_mappings:
                    session.delete(fm)
                session.delete(tm)
            session.flush()
            print("   -> Bestehende Mappings gelöscht für Neuanlage")
        else:
            source = EtlSource(
                name="maerklin_haendler",
                description="Märklin Händleradressen (Excel, Stand 02/2026)",
                connection_type="excel",
                connection_string=None,
                is_active=True,
            )
            session.add(source)
            session.flush()
            print(f"   -> Source erstellt: {source.id}")

        # 2. TableMapping: com_unternehmen
        print("\n2. TableMapping com_unternehmen...")
        tm_u = EtlTableMapping(
            source_id=source.id,
            source_table="excel_sheet",
            source_pk_field="Kunden-Nr.",
            target_table="com_unternehmen",
            target_pk_field="id",
            is_active=True,
        )
        session.add(tm_u)
        session.flush()
        print(f"   -> Mapping erstellt: {tm_u.id}")
        create_field_mappings(session, tm_u.id, UNTERNEHMEN_FIELDS, "Unternehmen")

        # 3. TableMapping: com_kontakt
        print("\n3. TableMapping com_kontakt...")
        tm_k = EtlTableMapping(
            source_id=source.id,
            source_table="excel_sheet",
            source_pk_field="Kunden-Nr.",
            target_table="com_kontakt",
            target_pk_field="id",
            is_active=True,
        )
        session.add(tm_k)
        session.flush()
        print(f"   -> Mapping erstellt: {tm_k.id}")
        create_field_mappings(session, tm_k.id, KONTAKT_FIELDS, "Kontakt")

        # 4. TableMapping: com_lieferbeziehung
        print("\n4. TableMapping com_lieferbeziehung...")
        tm_l = EtlTableMapping(
            source_id=source.id,
            source_table="excel_sheet",
            source_pk_field="Kunden-Nr.",
            target_table="com_lieferbeziehung",
            target_pk_field="id",
            is_active=True,
        )
        session.add(tm_l)
        session.flush()
        print(f"   -> Mapping erstellt: {tm_l.id}")
        create_field_mappings(session, tm_l.id, LIEFERBEZIEHUNG_FIELDS, "Lieferbeziehung")

        # 5. TableMappings: com_unternehmen_sortiment (one per brand)
        for i, (flag_field, brand_name) in enumerate(SORTIMENT_BRANDS):
            print(f"\n5.{i+1}. TableMapping com_unternehmen_sortiment ({brand_name})...")
            tm_s = EtlTableMapping(
                source_id=source.id,
                source_table="excel_sheet",
                source_pk_field="Kunden-Nr.",
                target_table="com_unternehmen_sortiment",
                target_pk_field="id",
                is_active=True,
            )
            session.add(tm_s)
            session.flush()
            print(f"   -> Mapping erstellt: {tm_s.id}")

            # Fields: unternehmen_id from ref, marke_id from x_to_bool + flag
            sort_fields = [
                ("__ref__", "unternehmen_id", "ref_current:id", "always"),
                (flag_field, "marke_id", "x_to_bool", "always"),
            ]
            # The marke_id needs fk_lookup — but we use a default_value trick:
            # x_to_bool returns True/False. We need the actual marke_id.
            # This will be resolved by custom logic in the import service.
            for src, tgt, transform, rule in sort_fields:
                fm = EtlFieldMapping(
                    table_mapping_id=tm_s.id,
                    source_field=src,
                    target_field=tgt,
                    transform=transform,
                    update_rule=rule,
                )
                if tgt == "marke_id":
                    fm.default_value = brand_name  # Used as lookup key
                session.add(fm)
                print(f"   {src:50s} -> {tgt:20s} [{transform}] ({rule})")

        # 6. TableMapping: com_unternehmen_dienstleistung
        print("\n6. TableMapping com_unternehmen_dienstleistung...")
        tm_d = EtlTableMapping(
            source_id=source.id,
            source_table="excel_sheet",
            source_pk_field="Kunden-Nr.",
            target_table="com_unternehmen_dienstleistung",
            target_pk_field="id",
            is_active=True,
        )
        session.add(tm_d)
        session.flush()
        print(f"   -> Mapping erstellt: {tm_d.id}")
        # dienstleistung_id needs fk_lookup to find "Modellbahn-Reparaturservice"
        for src, tgt, transform, rule in DIENSTLEISTUNG_FIELDS:
            fm = EtlFieldMapping(
                table_mapping_id=tm_d.id,
                source_field=src,
                target_field=tgt,
                transform=transform,
                update_rule=rule,
            )
            if tgt == "dienstleistung_id":
                fm.default_value = "Modellbahn-Reparaturservice"
            session.add(fm)
            print(f"   {src:50s} -> {tgt:20s} [{transform}] ({rule})")

        # 7. TableMapping: com_bonitaet
        print("\n7. TableMapping com_bonitaet...")
        tm_b = EtlTableMapping(
            source_id=source.id,
            source_table="excel_sheet",
            source_pk_field="Kunden-Nr.",
            target_table="com_bonitaet",
            target_pk_field="id",
            is_active=True,
        )
        session.add(tm_b)
        session.flush()
        print(f"   -> Mapping erstellt: {tm_b.id}")
        for src, tgt, transform, rule in BONITAET_FIELDS:
            fm = EtlFieldMapping(
                table_mapping_id=tm_b.id,
                source_field=src,
                target_field=tgt,
                transform=transform,
                update_rule=rule,
            )
            if tgt == "quelle":
                fm.default_value = "Lieferantenauskunft"
            session.add(fm)
            print(f"   {src:50s} -> {tgt:20s} [{transform}] ({rule})")

        # Add quelle field with const default
        fm_quelle = EtlFieldMapping(
            table_mapping_id=tm_b.id,
            source_field="__const__",
            target_field="quelle",
            transform=None,
            update_rule="always",
            default_value="Lieferantenauskunft",
        )
        session.add(fm_quelle)
        print(f"   {'__const__':50s} -> {'quelle':20s} [default] (always)")

        session.commit()

        # Summary
        total_fields = (
            len(UNTERNEHMEN_FIELDS) + len(KONTAKT_FIELDS) +
            len(LIEFERBEZIEHUNG_FIELDS) + len(SORTIMENT_BRANDS) * 2 +
            len(DIENSTLEISTUNG_FIELDS) + len(BONITAET_FIELDS) + 1
        )
        print("\n" + "=" * 70)
        print("Setup abgeschlossen!")
        print(f"Source: maerklin_haendler ({source.id})")
        print(f"TableMappings: {2 + 1 + len(SORTIMENT_BRANDS) + 1 + 1}")
        print(f"  - com_unternehmen: {len(UNTERNEHMEN_FIELDS)} Felder")
        print(f"  - com_kontakt: {len(KONTAKT_FIELDS)} Felder")
        print(f"  - com_lieferbeziehung: {len(LIEFERBEZIEHUNG_FIELDS)} Felder")
        print(f"  - com_unternehmen_sortiment: {len(SORTIMENT_BRANDS)} Marken")
        print(f"  - com_unternehmen_dienstleistung: {len(DIENSTLEISTUNG_FIELDS)} Felder")
        print(f"  - com_bonitaet: {len(BONITAET_FIELDS) + 1} Felder")
        print(f"Gesamt: {total_fields} FieldMappings")
        print("=" * 70)

    except Exception as e:
        session.rollback()
        print(f"\nFEHLER: {e}")
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    setup_maerklin_import()
