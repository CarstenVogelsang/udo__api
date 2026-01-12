# UDO API - ETL-System

## Übersicht

Das ETL-System (Extract-Transform-Load) ermöglicht konfigurationsgetriebene Datenimporte aus verschiedenen Quellen. Die Konfiguration wird in der Datenbank gespeichert und kann über die API verwaltet werden.

```
EtlSource (Datenquelle)
    ↓
EtlTableMapping (Quell-Tabelle → Ziel-Tabelle)
    ↓
EtlFieldMapping (Quell-Feld → Ziel-Feld + Transformation)
    ↓
EtlImportLog (Audit-Trail)
```

## Design-Entscheidungen

### Konfiguration in Datenbank

- Alle Mappings werden in der Datenbank gespeichert, nicht im Code
- Ermöglicht Verwaltung über API und später Admin-UI
- Neue Imports ohne Code-Deployment möglich

### Transformation-Registry

- Einfache Funktionsnamen statt komplexer Expressions
- Erweiterbar durch neue Funktionen im Code
- Spezielle `fk_lookup:table.field` Syntax für Foreign-Key-Auflösung

### Batch-Verarbeitung

- Commits alle 1.000 Zeilen für Memory-Effizienz
- Fortschrittsanzeige während des Imports
- Fehlertoleranz: Einzelne Fehler stoppen nicht den gesamten Import

## Tabellen

### etl_source

Datenquellen-Konfiguration.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| name | String(100) | Eindeutiger Name (z.B. "toyware_mssql") |
| description | String(255) | Beschreibung |
| connection_type | String(20) | Typ: "mssql", "mysql", "postgres", "csv" |
| connection_string | String(500) | Verbindung oder "env:PREFIX_*" |
| is_active | Boolean | Aktiv/Inaktiv |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### etl_table_mapping

Tabellen-Mapping (Quelle → Ziel).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| source_id | UUID | FK → etl_source |
| source_table | String(100) | Quell-Tabelle (z.B. "spi_tStore") |
| source_pk_field | String(100) | Primary Key der Quelle (z.B. "kStore") |
| target_table | String(100) | Ziel-Tabelle (z.B. "com_unternehmen") |
| target_pk_field | String(100) | Sync-Key im Ziel (z.B. "legacy_id") |
| is_active | Boolean | Aktiv/Inaktiv |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### etl_field_mapping

Feld-Mapping mit Transformation.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| table_mapping_id | UUID | FK → etl_table_mapping |
| source_field | String(100) | Quell-Feld (z.B. "cKurzname") |
| target_field | String(100) | Ziel-Feld (z.B. "kurzname") |
| transform | String(100) | Transformation (optional) |
| is_required | Boolean | Pflichtfeld |
| default_value | String(255) | Fallback-Wert |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### etl_import_log

Audit-Trail für Import-Läufe.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| table_mapping_id | UUID | FK → etl_table_mapping |
| started_at | DateTime | Startzeit |
| finished_at | DateTime | Endzeit |
| status | String(20) | "running", "success", "failed" |
| records_read | Integer | Gelesene Zeilen |
| records_created | Integer | Neu erstellte Datensätze |
| records_updated | Integer | Aktualisierte Datensätze |
| records_failed | Integer | Fehlerhafte Zeilen |
| error_message | Text | Fehlermeldung (bei Status "failed") |

## Transformationen

### Standard-Transformationen

| Name | Beschreibung | Beispiel |
|------|--------------|----------|
| `trim` | Whitespace entfernen | `"  Test  "` → `"Test"` |
| `upper` | Großbuchstaben | `"test"` → `"TEST"` |
| `lower` | Kleinbuchstaben | `"TEST"` → `"test"` |
| `to_int` | In Integer konvertieren | `"42"` → `42` |
| `to_float` | In Float konvertieren | `"3.14"` → `3.14` |
| `to_str` | In String konvertieren | `42` → `"42"` |

### FK-Lookup Transformation

Für Foreign-Key-Auflösung:

```
fk_lookup:geo_ort.legacy_id
```

- Sucht in Tabelle `geo_ort` nach Feld `legacy_id`
- Gibt die `id` (UUID) des gefundenen Datensatzes zurück
- Wird beim Import gecached für Performance

## API-Endpunkte

Alle Endpunkte erfordern Superadmin-Berechtigung.

### Sources

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/etl/sources` | Liste aller Quellen |
| GET | `/api/v1/etl/sources/{id}` | Einzelne Quelle |
| GET | `/api/v1/etl/sources/name/{name}` | Quelle nach Name |
| POST | `/api/v1/etl/sources` | Neue Quelle anlegen |
| PATCH | `/api/v1/etl/sources/{id}` | Quelle aktualisieren |
| DELETE | `/api/v1/etl/sources/{id}` | Quelle löschen |

### Table Mappings

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/etl/table-mappings` | Liste (Filter: source_id) |
| GET | `/api/v1/etl/table-mappings/{id}` | Einzelnes Mapping |
| POST | `/api/v1/etl/table-mappings` | Neues Mapping anlegen |
| PATCH | `/api/v1/etl/table-mappings/{id}` | Mapping aktualisieren |
| DELETE | `/api/v1/etl/table-mappings/{id}` | Mapping löschen |

### Field Mappings

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/etl/field-mappings` | Liste (Filter: table_mapping_id) |
| GET | `/api/v1/etl/field-mappings/{id}` | Einzelnes Feld-Mapping |
| POST | `/api/v1/etl/field-mappings` | Neues Feld-Mapping |
| PATCH | `/api/v1/etl/field-mappings/{id}` | Feld-Mapping aktualisieren |
| DELETE | `/api/v1/etl/field-mappings/{id}` | Feld-Mapping löschen |

### Import Logs & Utilities

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/etl/import-logs` | Import-Historie |
| GET | `/api/v1/etl/transforms` | Verfügbare Transformationen |

## Scripts

### Setup-Script

Erstellt die ETL-Konfiguration für eine Datenquelle:

```bash
uv run python scripts/setup_etl_toyware.py
```

### Import-Runner

Führt einen konfigurierten Import aus:

```bash
# Dry-Run (keine Änderungen)
uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStore --dry-run

# Echter Import
uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStore
```

## Beispiel: Toyware-Konfiguration

### EtlSource

```json
{
  "name": "toyware_mssql",
  "description": "Legacy Toyware MS SQL Server",
  "connection_type": "mssql",
  "connection_string": "env:MSSQL_*"
}
```

### EtlTableMapping

```json
{
  "source_table": "spi_tStore",
  "source_pk_field": "kStore",
  "target_table": "com_unternehmen",
  "target_pk_field": "legacy_id"
}
```

### EtlFieldMappings

| source_field | target_field | transform |
|--------------|--------------|-----------|
| kStore | legacy_id | to_int |
| dStatusUnternehmen | status_datum | - |
| cKurzname | kurzname | trim |
| cFirmierung | firmierung | trim |
| cStrasse | strasse | trim |
| cStrasseHausNr | strasse_hausnr | trim |
| kGeoOrt | geo_ort_id | fk_lookup:geo_ort.legacy_id |

## Beziehungen

```
etl_source (1) ─────< (n) etl_table_mapping
etl_table_mapping (1) ─────< (n) etl_field_mapping
etl_table_mapping (1) ─────< (n) etl_import_log
```

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `app/models/etl.py` | SQLAlchemy Models |
| `app/schemas/etl.py` | Pydantic Schemas |
| `app/services/etl.py` | Service-Layer mit Transformationen |
| `app/routes/etl.py` | FastAPI Router |
| `scripts/setup_etl_toyware.py` | Toyware-Konfiguration |
| `scripts/run_etl.py` | Generischer Import-Runner |

## Erweiterbarkeit

### Neue Transformation hinzufügen

In `app/services/etl.py`:

```python
def _my_transform(value: Any) -> Any:
    # Transformation implementieren
    return transformed_value

TRANSFORMS["my_transform"] = _my_transform
```

### Neue Datenquelle

1. EtlSource über API anlegen
2. EtlTableMapping(s) konfigurieren
3. EtlFieldMapping(s) für jedes Feld
4. Import-Runner ausführen

Für nicht-MSSQL-Quellen muss `scripts/run_etl.py` erweitert werden.
