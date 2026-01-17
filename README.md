# UDO API

FastAPI Backend für den Unternehmensdaten SaaS-Service.

---

## Schnellstart (TL;DR)

> **Wichtig**: Dieses Projekt verwendet **uv** als Package Manager. Es gibt kein virtuelles Environment zum Aktivieren - stattdessen wird `uv run` vor jeden Befehl gesetzt!

```bash
# 1. Ins Projektverzeichnis wechseln
cd udo__api

# 2. Dependencies installieren (nur beim ersten Mal oder nach Änderungen)
uv sync

# 3. API-Server starten
uv run fastapi dev app/main.py --port 8001
```

**API erreichbar unter:** http://localhost:8001
**Swagger-Dokumentation:** http://localhost:8001/docs/admin

### Beide Projekte starten (API + UI)

```bash
# Terminal 1: API Backend
cd udo__api
uv run fastapi dev app/main.py --port 8001

# Terminal 2: UI Frontend
cd udo__ui
uv run flask run --port 5050
```

**UI erreichbar unter:** http://localhost:5050
**Login:** `test@example.com` / `testpassword123`

---

## Einrichtung

Dieses Projekt verwendet **uv** als Package Manager.

### 1. Abhängigkeiten installieren

```bash
cd udo__api
uv sync
```

### 2. Umgebungsvariablen

Die `.env`-Datei enthält die Konfiguration für die Legacy-Datenbank (MS SQL Server).
Für die Entwicklung wird automatisch SQLite verwendet.

## API starten

### Entwicklungsserver

```bash
uv run fastapi dev app/main.py --port 8001
```

Die API ist dann verfügbar unter:
- **API**: http://localhost:8001
- **Dokumentation (öffentlich)**: http://localhost:8001/docs
- **Dokumentation (Partner)**: http://localhost:8001/docs/partner (API-Key erforderlich)
- **Dokumentation (Admin)**: http://localhost:8001/docs/admin (Superadmin erforderlich)

### Produktionsserver

```bash
uv run fastapi run app/main.py --port 8001
```

## Authentifizierung

Die API verwendet API-Key-basierte Authentifizierung über den `X-API-Key` Header.

### Rollen

| Rolle | Zugang |
|-------|--------|
| **Partner** | `/api/v1/partner/geodaten/*` - Eingeschränkte Geodaten |
| **Superadmin** | Alle Endpunkte inkl. `/api/v1/geo/*` und `/api/v1/admin/*` |

### Superadmin erstellen

```bash
uv run python scripts/create_superadmin.py
```

**Wichtig**: Der API-Key wird nur einmal angezeigt und kann nicht wiederhergestellt werden!

### Test-API-Keys (nur Entwicklung)

> ⚠️ **Achtung**: Diese Keys sind nur für lokale Entwicklung. In Produktion neue Keys generieren!

| Rolle | API-Key |
|-------|---------|
| Superadmin | `64wyVOJIQMPOLKTZ-mpULUw4wlwAz1dwizmy0KKQrEU` |
| Testpartner | `RSPz5CSKZ7oSAAiqXCOraADg3eJUvlm7S3MjCwJOuJ4` |

### Beispiel-Aufrufe

```bash
# Partner-Endpunkt (mit Partner- oder Superadmin-Key)
curl -H "X-API-Key: RSPz5CSKZ7oSAAiqXCOraADg3eJUvlm7S3MjCwJOuJ4" \
     http://localhost:8001/api/v1/partner/geodaten/laender

# Admin-Endpunkt (nur Superadmin)
curl -H "X-API-Key: 64wyVOJIQMPOLKTZ-mpULUw4wlwAz1dwizmy0KKQrEU" \
     http://localhost:8001/api/v1/admin/partners
```

## Verfügbare Endpoints

### Allgemein

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /` | API-Information |
| `GET /health` | Health-Check |

### Partner-Geodaten (`/api/v1/partner/geodaten/`) - Partner + Superadmin

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /api/v1/partner/geodaten/laender` | Alle Länder (eingeschränkte Felder) |
| `GET /api/v1/partner/geodaten/bundeslaender?land_code=DE` | Bundesländer eines Landes |
| `GET /api/v1/partner/geodaten/kreise?bundesland_code=DE-BY` | Kreise mit Abrufkosten |
| `GET /api/v1/partner/geodaten/orte?kreis_code=...` | Orte eines Kreises |

### Admin (`/api/v1/admin/`) - Nur Superadmin

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /api/v1/admin/partners` | Liste aller Partner |
| `POST /api/v1/admin/partners` | Neuen Partner erstellen |
| `GET /api/v1/admin/partners/{id}` | Partner-Details |
| `PATCH /api/v1/admin/partners/{id}` | Partner aktualisieren |
| `DELETE /api/v1/admin/partners/{id}` | Partner löschen |

### Geodaten (`/api/v1/geo/`) - Nur Superadmin

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /api/v1/geo/laender` | Alle Länder (vollständige Daten) |
| `GET /api/v1/geo/laender/{id}` | Land nach ID |
| `GET /api/v1/geo/bundeslaender` | Alle Bundesländer |
| `GET /api/v1/geo/bundeslaender/{id}` | Bundesland nach ID (inkl. Land) |
| `GET /api/v1/geo/kreise` | Alle Kreise |
| `GET /api/v1/geo/kreise/{id}` | Kreis nach ID (inkl. Bundesland → Land) |
| `GET /api/v1/geo/orte` | Alle Orte |
| `GET /api/v1/geo/orte/{id}` | Ort nach ID (inkl. Kreis → Bundesland → Land) |
| `GET /api/v1/geo/ortsteile` | Alle Ortsteile |
| `GET /api/v1/geo/ortsteile/{id}` | Ortsteil nach ID (inkl. komplette Hierarchie) |

## Datenmigration

Um Daten aus der Legacy-Datenbank zu migrieren:

```bash
# Legacy-Datenbank analysieren
uv run python scripts/analyze_legacy_db.py

# Daten migrieren
uv run python scripts/migrate_data.py
```

**Hinweis**: Die Legacy-Datenbank ist READ-ONLY! Es werden keine Änderungen vorgenommen.

## Projektstruktur

```
udo__api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI App
│   ├── config.py            # Konfiguration
│   ├── database.py          # SQLAlchemy Setup
│   ├── auth.py              # API-Key Authentifizierung
│   ├── openapi_docs.py      # Rollenbasierte Dokumentation
│   ├── models/
│   │   ├── geo.py           # Geodaten-Modelle
│   │   └── partner.py       # ApiPartner-Modell
│   ├── schemas/
│   │   ├── geo.py           # Pydantic Schemas
│   │   └── partner.py       # Partner-Schemas
│   ├── services/
│   │   ├── geo.py           # Geodaten Business Logic
│   │   └── partner.py       # Partner-Service
│   └── routes/
│       ├── geo.py           # Geodaten-Endpoints (Superadmin)
│       ├── partner_geo.py   # Partner-Geodaten-Endpoints
│       └── admin.py         # Admin-Endpoints
├── scripts/
│   ├── analyze_legacy_db.py # Legacy-DB Analyse
│   ├── migrate_data.py      # Datenmigration
│   └── create_superadmin.py # Superadmin erstellen
├── docs/
│   └── prd/                 # Produktdokumentation
├── data/
│   └── udo.db               # SQLite Entwicklungsdatenbank
├── pyproject.toml           # Dependencies (uv)
├── uv.lock
└── .env                     # Umgebungsvariablen
```

## Testen mit UDO_UI

Die API kann mit dem UDO_UI Frontend getestet werden.

### Voraussetzungen

Beide Projekte müssen lokal vorhanden sein:
- `udo__api` - FastAPI Backend (dieses Repository)
- `udo__ui` - Flask Frontend ([GitHub](https://github.com/CarstenVogelsang/udo__ui))

### Beide Server starten

```bash
# Terminal 1: API Backend starten
cd udo__api
uv run fastapi dev app/main.py --port 8001

# Terminal 2: UI Frontend starten
cd udo__ui
FLASK_APP=udo_ui:app uv run flask run --port 5050
```

### Im Browser testen

1. Öffne http://localhost:5050
2. Login mit den Test-Zugangsdaten:

| Feld | Wert |
|------|------|
| E-Mail | `test@example.com` |
| Passwort | `testpassword123` |

3. Nach dem Login kannst du die API-Funktionen über die UI testen

### Troubleshooting

- **API nicht erreichbar**: Prüfe ob Port 8001 läuft (`curl http://localhost:8001/health`)
- **Login fehlgeschlagen**: Prüfe ob der Test-User in der DB existiert
- **CORS-Fehler**: Die API erlaubt alle Origins in der Entwicklung

## Dokumentation

Ausführliche Dokumentation findet sich in `docs/prd/`:

- [01_fastapi.md](docs/prd/01_fastapi.md) - API-Dokumentation
- [02_datenmodell.md](docs/prd/02_datenmodell.md) - Datenmodell
- [03_migration.md](docs/prd/03_migration.md) - Migrationsprozess

## Repository

Git Repository: git@github.com:CarstenVogelsang/udo__api.git
