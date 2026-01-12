# Insomnia Setup für UDO API

Diese Anleitung beschreibt, wie du die UDO API mit [Insomnia](https://insomnia.rest/) testen kannst.

## Voraussetzungen

- Insomnia installiert
- UDO API läuft lokal
- Gültiger API-Key (Superadmin oder Partner)

## 1. API starten

```bash
cd /path/to/udo__api
fastapi dev app/main.py
```

Die API ist dann erreichbar unter: `http://localhost:8000`

## 2. Insomnia Environment einrichten

Erstelle ein neues Environment mit folgenden Variablen:

```json
{
  "base_url": "http://localhost:8000/api/v1",
  "api_key": "DEIN_API_KEY_HIER"
}
```

### API-Keys

| Rolle | Beschreibung | Zugriff |
|-------|--------------|---------|
| Superadmin | Vollzugriff auf alle Endpunkte | `/geo/*`, `/unternehmen/*`, `/etl/*`, `/admin/*` |
| Partner | Eingeschränkter Zugriff | `/partner/geodaten/*` |

## 3. Request Collection erstellen

### Authentifizierung konfigurieren

Für jeden Request muss der Header gesetzt werden:

| Header | Wert |
|--------|------|
| `X-API-Key` | `{{ api_key }}` |

**Tipp:** In Insomnia kannst du den Header auf Collection-Ebene setzen, dann gilt er für alle Requests.

## 4. Beispiel-Requests

### Unternehmen

#### Liste aller Unternehmen
```
GET {{ base_url }}/unternehmen
```

Query-Parameter:
- `limit` (default: 100, max: 1000)
- `skip` (default: 0)
- `suche` (min. 2 Zeichen)
- `geo_ort_id` (UUID)

#### Suche nach Name
```
GET {{ base_url }}/unternehmen?suche=Spielwaren&limit=10
```

#### Einzelnes Unternehmen (UUID)
```
GET {{ base_url }}/unternehmen/3d12d754-2122-4d69-ac10-93b5c2d509a9
```

#### Unternehmen nach Legacy-ID
```
GET {{ base_url }}/unternehmen/legacy/4361
```

#### Anzahl Unternehmen
```
GET {{ base_url }}/unternehmen/stats/count
```

### Geodaten

#### Länder
```
GET {{ base_url }}/geo/laender
```

#### Bundesländer
```
GET {{ base_url }}/geo/bundeslaender?land_id=UUID
```

#### Kreise
```
GET {{ base_url }}/geo/kreise?bundesland_id=UUID
```

#### Orte
```
GET {{ base_url }}/geo/orte?suche=München&limit=10
```

#### Orte nach PLZ
```
GET {{ base_url }}/geo/orte?plz=80331
```

### ETL (nur Superadmin)

#### Quellen auflisten
```
GET {{ base_url }}/etl/sources
```

#### Einzelne Quelle
```
GET {{ base_url }}/etl/sources/name/toyware_mssql
```

#### Table-Mappings
```
GET {{ base_url }}/etl/table-mappings
```

#### Field-Mappings
```
GET {{ base_url }}/etl/field-mappings?table_mapping_id=UUID
```

#### Import-Logs
```
GET {{ base_url }}/etl/import-logs
```

#### Verfügbare Transformationen
```
GET {{ base_url }}/etl/transforms
```

### Admin (nur Superadmin)

#### Partner auflisten
```
GET {{ base_url }}/admin/partners
```

#### Neuen Partner erstellen
```
POST {{ base_url }}/admin/partners
Content-Type: application/json

{
  "name": "Neuer Partner",
  "email": "partner@example.com",
  "role": "partner"
}
```

## 5. Response-Beispiel

**Request:** `GET /api/v1/unternehmen?suche=Spielwaren&limit=1`

**Response:**
```json
{
  "items": [
    {
      "id": "4d5c1163-41fa-423f-9925-f517532a2576",
      "legacy_id": 7099,
      "kurzname": "",
      "firmierung": "Spielwaren Ebner",
      "strasse": "Hauptplatz 23",
      "strasse_hausnr": null,
      "geo_ort": {
        "id": "2e54e88c-7344-4421-9b42-8ebfab38db36",
        "name": "Kremsmünster",
        "plz": "4540",
        "lat": 48.0529,
        "lng": 14.1292,
        "kreis": {
          "id": "3ac1c526-5001-4d39-a2db-672f99aee6d2",
          "name": "Kremsmünster",
          "bundesland": {
            "id": "936cafc5-a125-49af-9487-734f8a7db6b5",
            "name": "Oberösterreich",
            "land": {
              "id": "1c0ea19f-49f8-445b-a13f-d3c33cfa63ee",
              "name": "Österreich"
            }
          }
        }
      }
    }
  ],
  "total": 741
}
```

## 6. Fehlerbehandlung

### HTTP Status Codes

| Code | Bedeutung |
|------|-----------|
| 200 | Erfolg |
| 201 | Erstellt (POST) |
| 204 | Gelöscht (DELETE) |
| 400 | Ungültige Anfrage |
| 401 | API-Key fehlt |
| 403 | Keine Berechtigung (z.B. Partner auf Admin-Endpunkt) |
| 404 | Nicht gefunden |
| 422 | Validierungsfehler |

### Beispiel Fehlermeldung

```json
{
  "detail": "API-Key fehlt. Bitte X-API-Key Header setzen."
}
```

## 7. Swagger UI Alternative

Die API bietet auch eine interaktive Dokumentation:

| URL | Beschreibung |
|-----|--------------|
| `http://localhost:8000/docs` | Öffentliche Endpunkte |
| `http://localhost:8000/docs/partner` | Partner-Endpunkte (API-Key erforderlich) |
| `http://localhost:8000/docs/admin` | Admin-Endpunkte (Superadmin erforderlich) |

## 8. Collection exportieren

Du kannst deine Insomnia-Collection als JSON exportieren und im Team teilen:

1. Rechtsklick auf Collection → Export
2. Format: Insomnia v4 (JSON)
3. Datei im Repository unter `docs/` speichern
