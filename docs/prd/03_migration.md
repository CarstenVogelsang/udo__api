# Legacy-DB Migration

## Migrations-Prozess

### Quelle

- **Server:** `192.168.91.22:1433`
- **Datenbank:** `toyware`
- **Schema:** `dbo`
- **Tabellen-Präfix:** `spi_tGeo*`

### Wichtige Hinweise

- **NUR LESEZUGRIFF** auf die Legacy-Datenbank!
- Credentials in `.env` (nicht committen!)

### Scripts

1. **`scripts/analyze_legacy_db.py`** - Analysiert Tabellenstruktur
2. **`scripts/migrate_data.py`** - Migriert Daten nach SQLite

### Ausführung

```bash
# Analyse der Legacy-DB
uv run python scripts/analyze_legacy_db.py

# Datenmigration
uv run python scripts/migrate_data.py
```

## Spalten-Mapping

### geo_land (← spi_tGeoLand)

| Legacy | Neu | Transformation |
|--------|-----|----------------|
| kLand_ISO | ags, code | ISO-Code wird zu AGS und Code |
| cName | name | - |
| cNameEng | name_eng | - |
| cNameFra | name_fra | - |
| cISO3 | iso3 | - |
| cKontinent | kontinent | - |
| bEU | ist_eu | Boolean |
| cLandesvorwahl | landesvorwahl | - |
| - | id | Neue UUID generiert |
| kLand_ISO | legacy_id | Original-Key behalten |

### geo_bundesland (← spi_tGeoBundesland)

| Legacy | Neu | Transformation |
|--------|-----|----------------|
| kBundesland | legacy_id | Original-Key behalten |
| cBundeslandKürzel | kuerzel | - |
| kLand_ISO | land_id | UUID-Lookup über Mapping |
| cBundesland | name | - |
| nEinwohner | einwohner | - |
| dEinwohner | einwohner_stand | - |
| - | id | Neue UUID generiert |
| - | ags | Format: `{kBundesland:02d}` |
| - | code | Format: `{land_code}-{kuerzel}` |

### geo_kreis (← spi_tGeoKreis)

| Legacy | Neu | Transformation |
|--------|-----|----------------|
| kKreis | legacy_id | Original-Key behalten |
| cKreisSchlüssel | ags | - |
| cKreis | name | - |
| kBundesland | bundesland_id | UUID-Lookup |
| bIstLandkreis | ist_landkreis, typ | Boolean + "Landkreis" |
| bIstKreisfreieStadt | ist_kreisfreie_stadt, typ | Boolean + "Kreisfreie Stadt" |
| cAutoKennzeichen | autokennzeichen | - |
| cKreissitz | kreissitz | - |
| nEinwohner | einwohner | - |
| nFlächeKm2 | flaeche_km2 | - |
| cKreisBeschreibung | beschreibung | - |
| cWikipediaUrl_Kreis | wikipedia_url | - |
| cUrlOffizielleWebsite | website_url | - |
| - | id | Neue UUID generiert |
| - | code | Format: `{bundesland_code}-{ags}-{legacy_id}` |
| - | regierungsbezirk_id | NULL (Legacy-DB hat keine echten Daten) |

### geo_ort (← spi_tGeoOrt)

| Legacy | Neu | Transformation |
|--------|-----|----------------|
| kGeoOrt | legacy_id | Original-Key behalten |
| cGemeindeschlüssel | ags | - |
| cOrt | name | - |
| cPLZ | plz | - |
| kKreis | kreis_id | UUID-Lookup |
| bIstStadt | ist_stadt, typ | Boolean + "Stadt" |
| bIstGemeinde | ist_gemeinde, typ | Boolean + "Gemeinde" |
| bHauptOrt | ist_hauptort | Boolean |
| Lat | lat | - |
| Lng | lng | - |
| nEinwohner | einwohner | - |
| nFlächeKm2 | flaeche_km2 | - |
| cOrtsbeschreibung | beschreibung | - |
| cWikipediaUrl | wikipedia_url | - |
| cWebsiteURL | website_url | - |
| - | id | Neue UUID generiert |
| - | code | Format: `{kreis_code}-{plz}-{name_sanitized}-{legacy_id}` |

### geo_ortsteil (← spi_tGeoOrtsteil)

| Legacy | Neu | Transformation |
|--------|-----|----------------|
| kGeoOrtsteil | legacy_id | Original-Key behalten |
| cOrtsteil | name | - |
| kGeoOrt | ort_id | UUID-Lookup |
| Lat | lat | - |
| Lng | lng | - |
| nEinwohner | einwohner | - |
| cOrtsbeschreibung | beschreibung | - |
| - | id | Neue UUID generiert |
| - | code | Format: `{ort_code}-{name_sanitized}-{legacy_id}` |

## Migrations-Ergebnis

| Tabelle | Legacy | Migriert | Übersprungen |
|---------|--------|----------|--------------|
| geo_land | 238 | 238 | 0 |
| geo_bundesland | 101 | 101 | 0 |
| geo_regierungsbezirk | 1 | 0 | 1 (Dummy-Eintrag) |
| geo_kreis | 5.370 | 5.370 | 0 |
| geo_ort | 56.966 | 56.965 | 1 |
| geo_ortsteil | 149 | 148 | 1 |

---

# Legacy Geodaten Schema

**Quelle:** `192.168.91.22:1433/toyware`

**Generiert am:** 2026-01-10 21:48

---

## Übersicht

| Tabelle | Datensätze | Primary Key |
|---------|------------|-------------|
| spi_tGeoLand | 238 | kLand_ISO |
| spi_tGeoBundesland | 101 | kBundesland |
| spi_tGeoRegierungsbezirk | 1 | kRegierungsbezirk |
| spi_tGeoKreis | 5,370 | kKreis |
| spi_tGeoOrt | 56,966 | kGeoOrt |
| spi_tGeoOrtsteil | 149 | kGeoOrtsteil |

---

## spi_tGeoLand

**Datensätze:** 238

### Spalten

| Spalte | Datentyp | Länge | Nullable | PK | FK |
|--------|----------|-------|----------|----|----|n| kLand_ISO | nvarchar | 5 | NO | ✓ |  |
| cName | nvarchar | 255 | YES |  |  |
| cNameEng | nvarchar | 255 | YES |  |  |
| bEU | bit | - | YES |  |  |
| cKontinent | nvarchar | 255 | YES |  |  |
| cNameFra | nvarchar | 255 | YES |  |  |
| cISO3 | nvarchar | 50 | YES |  |  |
| cLandesvorwahl | nvarchar | 50 | YES |  |  |

---

## spi_tGeoBundesland

**Datensätze:** 101

### Spalten

| Spalte | Datentyp | Länge | Nullable | PK | FK |
|--------|----------|-------|----------|----|----|n| kBundesland | bigint | 19 | NO | ✓ |  |
| cBundeslandKürzel | nvarchar | 10 | NO |  |  |
| kLand_ISO | nvarchar | 5 | YES |  | spi_tGeoLand.kLand_ISO |
| cBundesland | nvarchar | 255 | YES |  |  |
| nEinwohner | int | 10 | YES |  |  |
| dEinwohner | datetime | - | YES |  |  |

### Beziehungen

- `kLand_ISO` → `spi_tGeoLand.kLand_ISO`

---

## spi_tGeoRegierungsbezirk

**Datensätze:** 1

### Spalten

| Spalte | Datentyp | Länge | Nullable | PK | FK |
|--------|----------|-------|----------|----|----|n| kRegierungsbezirk | bigint | 19 | NO | ✓ |  |
| kLand_ISO | nvarchar | 5 | YES |  | spi_tGeoLand.kLand_ISO |
| kBundesland | bigint | 19 | YES |  | spi_tGeoBundesland.kBundesland |
| cRegierungsbezirk | nvarchar | 100 | YES |  |  |

### Beziehungen

- `kLand_ISO` → `spi_tGeoLand.kLand_ISO`
- `kBundesland` → `spi_tGeoBundesland.kBundesland`

---

## spi_tGeoKreis

**Datensätze:** 5,370

### Spalten

| Spalte | Datentyp | Länge | Nullable | PK | FK |
|--------|----------|-------|----------|----|----|n| kKreis | bigint | 19 | NO | ✓ |  |
| kLand_ISO | nvarchar | 5 | YES |  | spi_tGeoLand.kLand_ISO |
| kBundesland | bigint | 19 | YES |  | spi_tGeoBundesland.kBundesland |
| cKreisSchlüssel | nvarchar | 50 | YES |  |  |
| cKreis | nvarchar | 100 | YES |  |  |
| nEinwohner | int | 10 | YES |  |  |
| dEinwohner | datetime | - | YES |  |  |
| cAutoKennzeichen | nvarchar | 10 | YES |  |  |
| cKreisBeschreibung | nvarchar | -1 | YES |  |  |
| bIstLandkreis | bit | - | YES |  |  |
| bIstKreisfreieStadt | bit | - | YES |  |  |
| nFlächeKm2 | int | 10 | YES |  |  |
| nEinwohnerProKm2 | int | 10 | YES |  |  |
| kQuelle_KreisBeschreibung | bigint | 19 | YES |  | spi_tQuelle.kQuelle |
| cKreissitz | nvarchar | 100 | YES |  |  |
| kGeoOrt_Kreissitz | bigint | 19 | YES |  | spi_tGeoOrt.kGeoOrt |
| cWikipediaUrl_Kreis | nvarchar | 255 | YES |  |  |
| cWikipediaUrl_Kreissitz | nvarchar | 255 | YES |  |  |
| kBenutzerMod | bigint | 19 | YES |  | spi_tBenutzer.kBenutzer |
| dMod | datetime | - | YES |  |  |
| cUrlOffizielleWebsite | nvarchar | 255 | YES |  |  |

### Beziehungen

- `kLand_ISO` → `spi_tGeoLand.kLand_ISO`
- `kBundesland` → `spi_tGeoBundesland.kBundesland`
- `kGeoOrt_Kreissitz` → `spi_tGeoOrt.kGeoOrt`
- `kQuelle_KreisBeschreibung` → `spi_tQuelle.kQuelle`
- `kBenutzerMod` → `spi_tBenutzer.kBenutzer`

---

## spi_tGeoOrt

**Datensätze:** 56,966

### Spalten

| Spalte | Datentyp | Länge | Nullable | PK | FK |
|--------|----------|-------|----------|----|----|n| kGeoOrt | bigint | 19 | NO | ✓ |  |
| kLand_ISO | nvarchar | 5 | YES |  | spi_tGeoLand.kLand_ISO |
| cPLZ | nvarchar | 10 | YES |  |  |
| cOrt | nvarchar | 100 | YES |  |  |
| kBundesland | bigint | 19 | YES |  | spi_tGeoBundesland.kBundesland |
| cBundesland | nvarchar | 100 | YES |  |  |
| cBundeslandKürzel | nvarchar | 10 | YES |  |  |
| cRegierungsbezirk | nvarchar | 100 | YES |  |  |
| kRegierungsbezirk | bigint | 19 | YES |  | spi_tGeoRegierungsbezirk.kRegierungsbezirk |
| kKreis | bigint | 19 | YES |  | spi_tGeoKreis.kKreis |
| cKreis | nvarchar | 100 | YES |  |  |
| cKreisKürzel | nvarchar | 10 | YES |  |  |
| cLatitude | nvarchar | 20 | YES |  |  |
| cLongitude | nvarchar | 20 | YES |  |  |
| Lat | float | 53 | YES |  |  |
| Lng | float | 53 | YES |  |  |
| cWebsiteURL | nvarchar | 255 | YES |  |  |
| cKlicktelData | nvarchar | 200 | YES |  |  |
| nKlicktelJahr | int | 10 | YES |  |  |
| bHauptOrt | bit | - | YES |  |  |
| iWappen | image | 2147483647 | YES |  |  |
| iLogo | image | 2147483647 | YES |  |  |
| cOrtsbeschreibung | nvarchar | -1 | YES |  |  |
| cWikipediaUrl | nvarchar | 255 | YES |  |  |
| nEinwohner | int | 10 | YES |  |  |
| dEinwohner | datetime | - | YES |  |  |
| cGemeindeschlüssel | nvarchar | 20 | YES |  |  |
| nEinwohnerProKm2 | int | 10 | YES |  |  |
| nFlächeKm2 | float | 53 | YES |  |  |
| kBenutzerMod | bigint | 19 | YES |  | spi_tBenutzer.kBenutzer |
| dMod | datetime | - | YES |  |  |
| bIstStadt | bit | - | YES |  |  |
| bIstGemeinde | bit | - | YES |  |  |

### Beziehungen

- `kLand_ISO` → `spi_tGeoLand.kLand_ISO`
- `kBundesland` → `spi_tGeoBundesland.kBundesland`
- `kKreis` → `spi_tGeoKreis.kKreis`
- `kRegierungsbezirk` → `spi_tGeoRegierungsbezirk.kRegierungsbezirk`
- `kRegierungsbezirk` → `spi_tGeoRegierungsbezirk.kRegierungsbezirk`
- `kBenutzerMod` → `spi_tBenutzer.kBenutzer`

---

## spi_tGeoOrtsteil

**Datensätze:** 149

### Spalten

| Spalte | Datentyp | Länge | Nullable | PK | FK |
|--------|----------|-------|----------|----|----|n| kGeoOrtsteil | bigint | 19 | NO | ✓ |  |
| cOrtsteil | nvarchar | 100 | YES |  |  |
| kGeoOrt | bigint | 19 | YES |  | spi_tGeoOrt.kGeoOrt |
| cOrtsbeschreibung | nvarchar | -1 | YES |  |  |
| nEinwohner | int | 10 | YES |  |  |
| dEinwohner | datetime | - | YES |  |  |
| iWappen | image | 2147483647 | YES |  |  |
| dMod | datetime | - | YES |  |  |
| kBenutzerMod | bigint | 19 | YES |  |  |
| Lat | float | 53 | YES |  |  |
| Lng | float | 53 | YES |  |  |

### Beziehungen

- `kGeoOrt` → `spi_tGeoOrt.kGeoOrt`

---

