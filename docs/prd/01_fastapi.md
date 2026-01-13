# UDO API - FastAPI Dokumentation

## Übersicht

Die UDO API ist eine FastAPI-Anwendung für deutsche Geodaten. Sie bietet REST-Endpoints für die Abfrage von Verwaltungseinheiten mit hierarchischer Struktur.

## Technologie-Stack

- **Framework**: FastAPI 0.122+
- **Datenbank**: SQLite (Entwicklung), PostgreSQL (Produktion)
- **ORM**: SQLAlchemy 2.0 (async)
- **Validierung**: Pydantic v2
- **Server**: Uvicorn (ASGI)

## API-Basis

- **Basis-URL**: `http://localhost:8000`
- **API-Prefix**: `/api/v1`
- **Dokumentation**: `/docs` (Swagger UI), `/redoc` (ReDoc)

## Endpoints

### Systemendpoints

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/` | Welcome-Message |
| GET | `/health` | Health-Check |

### Geodaten-Endpoints

Alle Geodaten-Endpoints befinden sich unter `/api/v1/geo/`.

#### Länder

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/geo/laender` | Liste aller Länder |
| GET | `/geo/laender/{id}` | Land nach UUID |
| GET | `/geo/laender/code/{code}` | Land nach ISO-Code (z.B. "DE") |

#### Bundesländer

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/geo/bundeslaender` | Liste aller Bundesländer |
| GET | `/geo/bundeslaender/{id}` | Bundesland nach UUID |
| GET | `/geo/bundeslaender/code/{code}` | Bundesland nach Code (z.B. "DE-BY") |

**Query-Parameter:**
- `land_id`: Filter nach Land-UUID
- `skip`: Pagination Offset (default: 0)
- `limit`: Maximale Anzahl (default: 100, max: 1000)

#### Regierungsbezirke

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/geo/regierungsbezirke` | Liste aller Regierungsbezirke |
| GET | `/geo/regierungsbezirke/{id}` | Regierungsbezirk nach UUID |

**Query-Parameter:**
- `bundesland_id`: Filter nach Bundesland-UUID

#### Kreise

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/geo/kreise` | Liste aller Kreise |
| GET | `/geo/kreise/{id}` | Kreis nach UUID |
| GET | `/geo/kreise/ags/{ags}` | Kreis nach AGS-Code |

**Query-Parameter:**
- `bundesland_id`: Filter nach Bundesland-UUID
- `regierungsbezirk_id`: Filter nach Regierungsbezirk-UUID
- `autokennzeichen`: Filter nach KFZ-Kennzeichen

#### Orte

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/geo/orte` | Liste aller Orte |
| GET | `/geo/orte/{id}` | Ort nach UUID |

**Query-Parameter:**
- `kreis_id`: Filter nach Kreis-UUID
- `plz`: Filter nach Postleitzahl
- `suche`: Volltextsuche im Ortsnamen

#### Ortsteile

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/geo/ortsteile` | Liste aller Ortsteile |
| GET | `/geo/ortsteile/{id}` | Ortsteil nach UUID |

**Query-Parameter:**
- `ort_id`: Filter nach Ort-UUID

## Response-Format

Alle Responses sind JSON-formatiert.

### Einzelobjekt

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ags": "09162",
  "code": "DE-BY-09162-1234",
  "name": "München, Landkreis",
  ...
}
```

### Listen

```json
{
  "items": [...],
  "total": 5370
}
```

### Hierarchie

Jeder Abruf enthält automatisch alle übergeordneten Ebenen:

```json
{
  "id": "...",
  "name": "Berlin",
  "kreis": {
    "id": "...",
    "name": "Kreisfreie Stadt Berlin",
    "bundesland": {
      "id": "...",
      "name": "Berlin",
      "land": {
        "id": "...",
        "name": "Deutschland"
      }
    }
  }
}
```

## Fehler-Responses

| Status | Beschreibung |
|--------|--------------|
| 404 | Ressource nicht gefunden |
| 422 | Validierungsfehler |
| 500 | Server-Fehler |

## Entwicklung

### Lokaler Start

```bash
cd udo__api
uv sync
uv run fastapi dev app/main.py
```

### Produktion

```bash
uv run fastapi run app/main.py --port 3000
```

## Konfiguration

Umgebungsvariablen in `.env`:

```env
SQLITE_DATABASE_URL=sqlite+aiosqlite:///./data/udo.db
API_PREFIX=/api/v1
DEBUG=false
```
