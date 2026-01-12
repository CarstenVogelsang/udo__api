# UDO API - Claude Code Anweisungen

## Projektübersicht

FastAPI-Anwendung für deutsche Geodaten mit 6-stufiger Hierarchie:
- Land → Bundesland → Regierungsbezirk → Kreis → Ort → Ortsteil

## Wichtige Regeln

### Legacy-Datenbank (MS SQL Server)

⚠️ **KRITISCH: NUR LESEZUGRIFF auf die Legacy-Datenbank!**

- Server: 192.168.91.22:1433
- Datenbank: toyware
- **NIEMALS** INSERT, UPDATE oder DELETE auf dieser Datenbank ausführen
- Nur SELECT-Queries erlaubt
- Credentials in `.env` (nicht committen!)

### Datenmodell

- **Primary Key**: UUID (für Synchronisation)
- **Business Keys**: AGS (Amtlicher Gemeindeschlüssel) + hierarchischer Code
- Hierarchischer Code wird automatisch generiert (z.B. `DE-BY-091-09162`)

### Tabellen-Präfix

Alle Geodaten-Tabellen verwenden den Präfix `geo_`:
- `geo_land`
- `geo_bundesland`
- `geo_regierungsbezirk`
- `geo_kreis`
- `geo_ort`
- `geo_ortsteil`

### API-Design

- Jeder Abruf eines Elements liefert die komplette übergeordnete Hierarchie mit
- API-Prefix: `/api/v1`
- Deutsche Endpunkt-Namen: `/geo/laender`, `/geo/bundeslaender`, etc.

## Entwicklung

### Lokaler Start

```bash
cd udo__api
uv sync
fastapi dev app/main.py
```

### Dependencies installieren

```bash
uv add <package>
```

### Legacy-DB Analyse

```bash
uv run python scripts/analyze_legacy_db.py
```

### Daten-Migration

```bash
uv run python scripts/migrate_data.py
```

## Dokumentation

- PRD-Dateien: `docs/prd/`
- API-Dokumentation: Automatisch unter `/docs` (Swagger UI)

## Dateien nicht committen

- `.env` (enthält Passwörter)
- `data/*.db` (SQLite-Datenbanken)
- `.venv/`
