# UDO API - Unternehmensdaten (Com-Bereich)

## Übersicht

Der Com-Bereich (Company) enthält Unternehmensdaten mit geografischer Verortung. Jedes Unternehmen ist mit einem GeoOrt verknüpft und erhält dadurch die vollständige Geo-Hierarchie.

```
ComUnternehmen ──→ GeoOrt ──→ GeoKreis ──→ GeoBundesland ──→ GeoLand
```

## Design-Entscheidungen

### Tabellenpräfix

- **com_** analog zu **geo_** für Geodaten
- Gruppiert zusammengehörige Tabellen in der Datenbank
- Klassenname: **Com**Unternehmen (konsistent mit **Geo**Ort)

### Legacy-ID als Sync-Key

- `legacy_id` speichert den Original-Primary-Key aus der Quell-Datenbank
- Ermöglicht wiederholte Imports (Update statt Duplikat)
- Unique Index für schnelle Lookups

### Geo-Referenz

- Jedes Unternehmen hat eine optionale Referenz zu `geo_ort`
- Die vollständige Hierarchie wird bei API-Abfragen mitgeliefert
- Eager Loading mit `joinedload` für Performance

## Datenmodell

### com_unternehmen

Unternehmensstammdaten.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| legacy_id | Integer | Original kStore aus Legacy-DB (unique) |
| status_datum | DateTime | Status-Datum (dStatusUnternehmen) |
| kurzname | String(100) | Kurzname des Unternehmens |
| firmierung | String(255) | Vollständige Firmierung |
| strasse | String(255) | Straßenname |
| strasse_hausnr | String(50) | Hausnummer |
| geo_ort_id | UUID | FK → geo_ort (nullable) |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### Legacy-Feld-Mapping

Mapping von der Toyware Legacy-Tabelle `spi_tStore`:

| Legacy (spi_tStore) | Präfix | Neu (com_unternehmen) |
|---------------------|--------|----------------------|
| kStore | k = Key | legacy_id |
| dStatusUnternehmen | d = Datum | status_datum |
| cKurzname | c = Char | kurzname |
| cFirmierung | c = Char | firmierung |
| cStrasse | c = Char | strasse |
| cStrasseHausNr | c = Char | strasse_hausnr |
| kGeoOrt | k = Key | geo_ort_id (via Lookup) |

Die Legacy-Datenbank verwendet Hungarian Notation:
- `k` = Key (Integer, Foreign Key)
- `c` = Char/Varchar (String)
- `d` = Datum (DateTime)
- `n` = Numeric (Integer/Float)

## API-Endpunkte

Alle Endpunkte erfordern Superadmin-Berechtigung.

### Liste & Suche

```
GET /api/v1/unternehmen
```

Query-Parameter:
| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| geo_ort_id | String | Filter nach Ort-UUID |
| suche | String | Textsuche in Kurzname/Firmierung (min. 2 Zeichen) |
| skip | Integer | Pagination Offset (default: 0) |
| limit | Integer | Max. Anzahl (default: 100, max: 1000) |

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "legacy_id": 4359,
      "kurzname": "Kaufhaus Türmli",
      "firmierung": "Kaufhaus Türmli",
      "strasse": "Rathausplatz 3",
      "strasse_hausnr": null,
      "geo_ort": {
        "id": "uuid",
        "name": "Waidhofen an der Ybbs",
        "plz": "3340",
        "kreis": {
          "id": "uuid",
          "name": "Amstetten",
          "bundesland": {
            "id": "uuid",
            "name": "Niederösterreich",
            "land": {
              "id": "uuid",
              "name": "Österreich"
            }
          }
        }
      }
    }
  ],
  "total": 11934
}
```

### Einzelnes Unternehmen

```
GET /api/v1/unternehmen/{id}
```

Gibt das Unternehmen mit allen Details und vollständiger Geo-Hierarchie zurück.

### Nach Legacy-ID

```
GET /api/v1/unternehmen/legacy/{legacy_id}
```

Sucht ein Unternehmen anhand des Original-Primary-Keys (`kStore`).

Nützlich für:
- Verifizierung von Imports
- Integration mit Legacy-Systemen
- Debugging

### Statistiken

```
GET /api/v1/unternehmen/stats/count
```

Response:
```json
{
  "total": 11934
}
```

## Indizes

| Index | Spalte(n) | Beschreibung |
|-------|-----------|--------------|
| PRIMARY | id | Primary Key |
| UNIQUE | legacy_id | Verhindert Duplikate bei Re-Import |
| INDEX | kurzname | Schnelle Namenssuche |
| INDEX | geo_ort_id | FK-Lookup |

## Beziehungen

```
com_unternehmen (n) ─────> (1) geo_ort
                                  │
                                  ↓
                             geo_kreis
                                  │
                                  ↓
                           geo_bundesland
                                  │
                                  ↓
                              geo_land
```

## Datenmenge

| Metrik | Wert |
|--------|------|
| Gesamtanzahl | 11.934 |
| Mit Geo-Referenz | 11.684 (98%) |
| Ohne Geo-Referenz | 250 (2%) |

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `app/models/com.py` | ComUnternehmen SQLAlchemy Model |
| `app/schemas/com.py` | Pydantic Response Schemas |
| `app/services/com.py` | ComService Business Logic |
| `app/routes/com.py` | FastAPI Router |

## Import

Der Import erfolgt über das ETL-System (siehe `04_etl_system.md`):

```bash
# 1. ETL-Konfiguration erstellen (einmalig)
uv run python scripts/setup_etl_toyware.py

# 2. Import ausführen
uv run python scripts/run_etl.py --source toyware_mssql --table spi_tStore
```

## Zukünftige Erweiterungen

### Geplante Felder

Diese Felder aus `spi_tStore` könnten später hinzugefügt werden:

| Legacy-Feld | Beschreibung |
|-------------|--------------|
| kStatusUnternehmen | Status-Referenz (separate Tabelle) |
| cTelefon | Telefonnummer |
| cEmail | E-Mail-Adresse |
| cWebsite | Website-URL |
| kBranche | Branchen-Referenz |
| nUmsatz | Umsatz |
| nMitarbeiter | Mitarbeiterzahl |

### Geplante Tabellen

| Tabelle | Beschreibung |
|---------|--------------|
| com_status | Unternehmens-Status (aktiv, inaktiv, etc.) |
| com_branche | Branchen-Katalog |
| com_kontakt | Kontaktpersonen |
| com_filiale | Filialen/Standorte |

### Partner-API

Für externe Partner könnte später ein eingeschränkter Zugriff bereitgestellt werden:

```
GET /api/v1/partner/unternehmen
```

Mit limitierten Feldern und Kosten-Tracking analog zu den Geodaten.

## Verwendung

### Python-Beispiel

```python
import httpx

headers = {"X-API-Key": "your-superadmin-key"}

# Liste abrufen
response = httpx.get(
    "http://localhost:8000/api/v1/unternehmen",
    headers=headers,
    params={"suche": "Kaufhaus", "limit": 10}
)
data = response.json()

for u in data["items"]:
    print(f"{u['kurzname']} - {u['geo_ort']['name']}, {u['geo_ort']['kreis']['name']}")
```

### cURL-Beispiel

```bash
# Suche nach "Spielwaren"
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:8000/api/v1/unternehmen?suche=Spielwaren&limit=5"

# Nach Legacy-ID
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:8000/api/v1/unternehmen/legacy/4361"
```
