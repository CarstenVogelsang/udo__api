#!/usr/bin/env python3
"""
Migrates geodata from Legacy MS SQL Server to PostgreSQL.

IMPORTANT:
- Legacy-DB: READ-ONLY!
- Target-DB: PostgreSQL

Generates:
- UUIDs as primary keys
- AGS codes from legacy data
- Hierarchical codes (e.g. "DE-BY-091-09162")
"""
import sys
from pathlib import Path
from uuid import uuid4
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymssql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.geo import (
    Base,
    GeoLand,
    GeoBundesland,
    GeoRegierungsbezirk,
    GeoKreis,
    GeoOrt,
    GeoOrtsteil,
)

settings = get_settings()


def get_legacy_connection():
    """Creates a connection to the legacy MS SQL Server."""
    return pymssql.connect(
        server=settings.mssql_host,
        port=settings.mssql_port,
        database=settings.mssql_database,
        user=settings.mssql_user,
        password=settings.mssql_password,
        as_dict=True,
    )


def get_db_session():
    """Creates a synchronous database session."""
    db_url = settings.database_url_sync
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def sanitize_code(text: str) -> str:
    """Sanitizes text for use in hierarchical codes."""
    if not text:
        return ""
    # Remove special characters, keep alphanumeric and hyphens
    text = re.sub(r'[^\w\-]', '', text)
    return text[:30]  # Limit length


class DataMigrator:
    """Handles the data migration from legacy DB to PostgreSQL."""

    def __init__(self):
        self.legacy_conn = get_legacy_connection()
        self.session, self.engine = get_db_session()

        # ID mappings: legacy_id -> (new_uuid, code)
        self.land_map = {}  # kLand_ISO -> (uuid, code)
        self.bundesland_map = {}  # kBundesland -> (uuid, code, land_uuid)
        self.regbez_map = {}  # kRegierungsbezirk -> (uuid, code, bundesland_uuid)
        self.kreis_map = {}  # kKreis -> (uuid, code, bundesland_uuid, regbez_uuid)
        self.ort_map = {}  # kGeoOrt -> (uuid, code, kreis_uuid)

    def migrate_all(self):
        """Migrates all tables in the correct order."""
        print("="*70)
        print("Datenmigration: Legacy MS SQL -> PostgreSQL")
        print("="*70)

        # Clear existing data
        print("\nLösche bestehende Daten...")
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        # Migrate in order (respecting foreign keys)
        self.migrate_laender()
        self.migrate_bundeslaender()
        # Skip Regierungsbezirke - only has dummy data
        self.migrate_kreise()
        self.migrate_orte()
        self.migrate_ortsteile()

        print("\n" + "="*70)
        print("Migration abgeschlossen!")
        print("="*70)

    def migrate_laender(self):
        """Migrates countries."""
        print("\n[1/5] Migriere Länder...")

        cursor = self.legacy_conn.cursor()
        cursor.execute("SELECT * FROM dbo.spi_tGeoLand")

        count = 0
        for row in cursor:
            iso_code = row["kLand_ISO"]
            if not iso_code:
                continue

            new_uuid = str(uuid4())
            code = iso_code.upper()

            land = GeoLand(
                id=new_uuid,
                ags=code,
                code=code,
                name=row.get("cName") or code,
                name_eng=row.get("cNameEng"),
                name_fra=row.get("cNameFra"),
                iso3=row.get("cISO3"),
                kontinent=row.get("cKontinent"),
                ist_eu=bool(row.get("bEU")),
                landesvorwahl=row.get("cLandesvorwahl"),
                legacy_id=iso_code,
            )
            self.session.add(land)
            self.land_map[iso_code] = (new_uuid, code)
            count += 1

        self.session.commit()
        print(f"  -> {count} Länder migriert")

    def migrate_bundeslaender(self):
        """Migrates federal states."""
        print("\n[2/5] Migriere Bundesländer...")

        cursor = self.legacy_conn.cursor()
        cursor.execute("SELECT * FROM dbo.spi_tGeoBundesland")

        count = 0
        for row in cursor:
            legacy_id = row["kBundesland"]
            land_iso = row.get("kLand_ISO")

            if not land_iso or land_iso not in self.land_map:
                continue

            land_uuid, land_code = self.land_map[land_iso]
            new_uuid = str(uuid4())

            # Generate AGS and code
            kuerzel = row.get("cBundeslandKürzel") or ""
            ags = f"{legacy_id:02d}" if isinstance(legacy_id, int) else str(legacy_id)
            code = f"{land_code}-{kuerzel}" if kuerzel else f"{land_code}-{ags}"

            bundesland = GeoBundesland(
                id=new_uuid,
                ags=ags,
                code=code.upper(),
                kuerzel=kuerzel,
                name=row.get("cBundesland") or f"Bundesland {legacy_id}",
                einwohner=row.get("nEinwohner"),
                einwohner_stand=row.get("dEinwohner"),
                land_id=land_uuid,
                legacy_id=legacy_id,
            )
            self.session.add(bundesland)
            self.bundesland_map[legacy_id] = (new_uuid, code.upper(), land_uuid)
            count += 1

        self.session.commit()
        print(f"  -> {count} Bundesländer migriert")

    def migrate_kreise(self):
        """Migrates counties."""
        print("\n[3/5] Migriere Kreise...")

        cursor = self.legacy_conn.cursor()
        cursor.execute("SELECT * FROM dbo.spi_tGeoKreis")

        count = 0
        skipped = 0
        for row in cursor:
            legacy_id = row["kKreis"]
            bundesland_id = row.get("kBundesland")

            if not bundesland_id or bundesland_id not in self.bundesland_map:
                skipped += 1
                continue

            bundesland_uuid, bundesland_code, land_uuid = self.bundesland_map[bundesland_id]
            new_uuid = str(uuid4())

            # AGS from cKreisSchlüssel
            ags = row.get("cKreisSchlüssel") or str(legacy_id)
            # Include legacy_id to ensure uniqueness
            code = f"{bundesland_code}-{ags}-{legacy_id}"

            # Determine type
            typ = None
            if row.get("bIstLandkreis"):
                typ = "Landkreis"
            elif row.get("bIstKreisfreieStadt"):
                typ = "Kreisfreie Stadt"

            kreis = GeoKreis(
                id=new_uuid,
                ags=ags,
                code=code.upper(),
                name=row.get("cKreis") or f"Kreis {legacy_id}",
                typ=typ,
                ist_landkreis=bool(row.get("bIstLandkreis")),
                ist_kreisfreie_stadt=bool(row.get("bIstKreisfreieStadt")),
                autokennzeichen=row.get("cAutoKennzeichen"),
                kreissitz=row.get("cKreissitz"),
                einwohner=row.get("nEinwohner"),
                einwohner_stand=row.get("dEinwohner"),
                einwohner_pro_km2=row.get("nEinwohnerProKm2"),
                flaeche_km2=row.get("nFlächeKm2"),
                beschreibung=row.get("cKreisBeschreibung"),
                wikipedia_url=row.get("cWikipediaUrl_Kreis"),
                website_url=row.get("cUrlOffizielleWebsite"),
                bundesland_id=bundesland_uuid,
                regierungsbezirk_id=None,  # Legacy DB has no real Regierungsbezirke
                legacy_id=legacy_id,
            )
            self.session.add(kreis)
            self.kreis_map[legacy_id] = (new_uuid, code.upper(), bundesland_uuid, None)
            count += 1

            # Commit in batches
            if count % 500 == 0:
                self.session.commit()
                print(f"     {count} Kreise...")

        self.session.commit()
        print(f"  -> {count} Kreise migriert ({skipped} übersprungen)")

    def migrate_orte(self):
        """Migrates cities/municipalities."""
        print("\n[4/5] Migriere Orte...")

        cursor = self.legacy_conn.cursor()
        cursor.execute("SELECT * FROM dbo.spi_tGeoOrt")

        count = 0
        skipped = 0
        for row in cursor:
            legacy_id = row["kGeoOrt"]
            kreis_id = row.get("kKreis")

            if not kreis_id or kreis_id not in self.kreis_map:
                skipped += 1
                continue

            kreis_uuid, kreis_code, bundesland_uuid, regbez_uuid = self.kreis_map[kreis_id]
            new_uuid = str(uuid4())

            # AGS from cGemeindeschlüssel
            ags = row.get("cGemeindeschlüssel") or ""
            plz = row.get("cPLZ") or ""
            name = row.get("cOrt") or f"Ort {legacy_id}"

            # Generate unique code
            name_part = sanitize_code(name)[:20]
            code = f"{kreis_code}-{plz}-{name_part}" if plz else f"{kreis_code}-{legacy_id}"

            # Ensure code is unique by appending legacy_id if needed
            code = f"{code}-{legacy_id}"

            # Determine type
            typ = None
            if row.get("bIstStadt"):
                typ = "Stadt"
            elif row.get("bIstGemeinde"):
                typ = "Gemeinde"

            ort = GeoOrt(
                id=new_uuid,
                ags=ags if ags else None,
                code=code.upper(),
                name=name,
                plz=plz if plz else None,
                typ=typ,
                ist_stadt=bool(row.get("bIstStadt")),
                ist_gemeinde=bool(row.get("bIstGemeinde")),
                ist_hauptort=bool(row.get("bHauptOrt")),
                lat=row.get("Lat"),
                lng=row.get("Lng"),
                einwohner=row.get("nEinwohner"),
                einwohner_stand=row.get("dEinwohner"),
                einwohner_pro_km2=row.get("nEinwohnerProKm2"),
                flaeche_km2=row.get("nFlächeKm2"),
                beschreibung=row.get("cOrtsbeschreibung"),
                wikipedia_url=row.get("cWikipediaUrl"),
                website_url=row.get("cWebsiteURL"),
                kreis_id=kreis_uuid,
                legacy_id=legacy_id,
            )
            self.session.add(ort)
            self.ort_map[legacy_id] = (new_uuid, code.upper(), kreis_uuid)
            count += 1

            # Commit in batches
            if count % 5000 == 0:
                self.session.commit()
                print(f"     {count} Orte...")

        self.session.commit()
        print(f"  -> {count} Orte migriert ({skipped} übersprungen)")

    def migrate_ortsteile(self):
        """Migrates city districts."""
        print("\n[5/5] Migriere Ortsteile...")

        cursor = self.legacy_conn.cursor()
        cursor.execute("SELECT * FROM dbo.spi_tGeoOrtsteil")

        count = 0
        skipped = 0
        for row in cursor:
            legacy_id = row["kGeoOrtsteil"]
            ort_id = row.get("kGeoOrt")

            if not ort_id or ort_id not in self.ort_map:
                skipped += 1
                continue

            ort_uuid, ort_code, kreis_uuid = self.ort_map[ort_id]
            new_uuid = str(uuid4())

            name = row.get("cOrtsteil") or f"Ortsteil {legacy_id}"
            name_part = sanitize_code(name)[:20]
            code = f"{ort_code}-{name_part}-{legacy_id}"

            ortsteil = GeoOrtsteil(
                id=new_uuid,
                ags=None,
                code=code.upper(),
                name=name,
                lat=row.get("Lat"),
                lng=row.get("Lng"),
                einwohner=row.get("nEinwohner"),
                einwohner_stand=row.get("dEinwohner"),
                beschreibung=row.get("cOrtsbeschreibung"),
                ort_id=ort_uuid,
                legacy_id=legacy_id,
            )
            self.session.add(ortsteil)
            count += 1

        self.session.commit()
        print(f"  -> {count} Ortsteile migriert ({skipped} übersprungen)")

    def close(self):
        """Closes all connections."""
        self.session.close()
        self.legacy_conn.close()


def main():
    """Main function."""
    try:
        migrator = DataMigrator()
        migrator.migrate_all()
        migrator.close()
    except Exception as e:
        print(f"\nFehler bei der Migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
