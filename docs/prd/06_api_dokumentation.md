# UDO API - API-Dokumentation (OpenAPI/Swagger)

## Übersicht

Die UDO API bietet interaktive API-Dokumentation über Swagger UI und ReDoc. Die Dokumentation ist rollenbasiert gefiltert - verschiedene Benutzergruppen sehen nur die für sie relevanten Endpunkte.

## Dokumentations-URLs

### Swagger UI (interaktiv)

| URL | Zielgruppe | Sichtbare Endpunkte |
|-----|------------|---------------------|
| `/docs` | Öffentlich | Nur System (health, root) |
| `/docs/partner` | Partner | System + Partner Geodaten |
| `/docs/admin` | Superadmin | Alle Endpunkte |

### ReDoc (statisch, übersichtlich)

| URL | Zielgruppe |
|-----|------------|
| `/redoc` | Öffentlich |
| `/redoc/partner` | Partner |
| `/redoc/admin` | Superadmin |

## Authentifizierung in Swagger UI

### Authorize-Button

Die Partner- und Admin-Dokumentation enthält einen **"Authorize"-Button** oben rechts. Darüber können Benutzer ihren API-Key eingeben, um die "Try it out"-Funktion zu nutzen.

**Ablauf:**

1. Dokumentation im Browser öffnen (z.B. `/docs/partner`)
2. Auf **"Authorize"** klicken
3. API-Key in das Textfeld eingeben
4. **"Authorize"** bestätigen, dann **"Close"**
5. Alle "Try it out"-Requests verwenden nun automatisch den API-Key

### Security-Schema

Das OpenAPI-Schema definiert die Authentifizierung:

```yaml
components:
  securitySchemes:
    APIKeyHeader:
      type: apiKey
      in: header
      name: X-API-Key
      description: API-Key für Authentifizierung

security:
  - APIKeyHeader: []
```

## Rollenbasierte Filterung

### Tag-Konfiguration

Endpunkte werden über OpenAPI-Tags gruppiert und gefiltert:

| Rolle | Sichtbare Tags |
|-------|----------------|
| public | System |
| partner | System, Partner Geodaten |
| superadmin | System, Partner Geodaten, Geodaten, Admin, Unternehmen, ETL |

### Endpunkt-Tags

| Tag | Beschreibung | Beispiel-Endpunkte |
|-----|--------------|-------------------|
| System | Basis-Endpunkte | `/`, `/health` |
| Partner Geodaten | Geodaten für Partner | `/api/v1/partner/geodaten/*` |
| Geodaten | Vollständige Geodaten | `/api/v1/geo/*` |
| Unternehmen | Unternehmensdaten | `/api/v1/unternehmen/*` |
| ETL | Import-System | `/api/v1/etl/*` |
| Admin | Partner-Verwaltung | `/api/v1/admin/*` |

## Design-Entscheidungen

### Öffentliche Docs-Seiten

Die Dokumentations-Seiten selbst (`/docs/partner`, `/docs/admin`) sind **ohne Authentifizierung** erreichbar. Gründe:

1. **Usability**: Browser können keine HTTP-Header bei GET-Requests setzen
2. **Discoverability**: Partner können die API erkunden, bevor sie einen Key haben
3. **Standard-Praxis**: Die meisten APIs dokumentieren öffentlich ihre Endpunkte

Die **API-Endpunkte selbst** sind weiterhin geschützt - der Authorize-Button ist für "Try it out" erforderlich.

### Separate OpenAPI-Schemas

Jede Rolle hat ihr eigenes OpenAPI-Schema:

| Schema-URL | Inhalt |
|------------|--------|
| `/openapi.json` | Nur öffentliche Endpunkte |
| `/openapi-partner.json` | Partner-Endpunkte + Security-Schema |
| `/openapi-admin.json` | Alle Endpunkte + Security-Schema |

Das ermöglicht:
- Gefiltertes Schema für Client-Generierung
- Kein Informationsleck über interne Endpunkte

## Implementierung

### Dateien

| Datei | Beschreibung |
|-------|--------------|
| `app/openapi_docs.py` | Dokumentations-Konfiguration |
| `app/auth.py` | API-Key Authentifizierung |

### Code-Struktur

```python
# app/openapi_docs.py

ROLE_TAGS = {
    "public": ["System"],
    "partner": ["System", "Partner Geodaten"],
    "superadmin": ["System", "Partner Geodaten", "Geodaten", "Admin", ...],
}

def get_filtered_openapi(app, allowed_tags, include_security=False):
    """Generiert gefiltertes OpenAPI-Schema basierend auf Tags."""
    # 1. Routen nach Tags filtern
    # 2. Optional: Security-Schema hinzufügen
    # 3. OpenAPI-Spec zurückgeben

def setup_docs(app):
    """Registriert alle Dokumentations-Endpunkte."""
    # /docs, /docs/partner, /docs/admin
    # /redoc, /redoc/partner, /redoc/admin
    # /openapi.json, /openapi-partner.json, /openapi-admin.json
```

### Router-Tags setzen

Beim Erstellen von Routen wird der Tag gesetzt:

```python
# app/routes/partner_geo.py
router = APIRouter(
    prefix="/api/v1/partner/geodaten",
    tags=["Partner Geodaten"]
)

# app/routes/com.py
router = APIRouter(
    prefix="/api/v1/unternehmen",
    tags=["Unternehmen"]
)
```

## Verwendung

### Für Partner

1. **API erkunden**: `https://api.example.com/docs/partner`
2. **API-Key anfordern**: Kontakt zum Admin
3. **Authorize**: Key in Swagger UI eingeben
4. **Testen**: "Try it out" bei gewünschtem Endpunkt

### Für Entwickler (Integration)

1. **OpenAPI-Schema laden**: `GET /openapi-partner.json`
2. **Client generieren**: Mit OpenAPI Generator oder ähnlichen Tools
3. **API-Key konfigurieren**: Im generierten Client als Header

### cURL-Beispiel

```bash
# OpenAPI-Schema für Partner abrufen
curl https://api.example.com/openapi-partner.json -o openapi.json

# Mit openapi-generator Client generieren
openapi-generator generate -i openapi.json -g python -o ./client
```

## Swagger UI vs ReDoc

| Feature | Swagger UI | ReDoc |
|---------|-----------|-------|
| Interaktiv ("Try it out") | ✅ | ❌ |
| Authorize-Button | ✅ | ❌ |
| Übersichtlichkeit | Mittel | Hoch |
| Navigation | Kompakt | Sidebar |
| Schema-Darstellung | Inline | Expandierbar |

**Empfehlung:**
- **Swagger UI** für Tests und Entwicklung
- **ReDoc** für Dokumentation und Übersicht

## Erweiterungsmöglichkeiten

### Geplant

| Feature | Beschreibung |
|---------|--------------|
| OAuth2 | Für Web-Anwendungen mit Benutzer-Login |
| Rate-Limit-Anzeige | Verbleibende Requests im Header |
| Changelog | Versionshistorie in der Dokumentation |

### Beispiel: OAuth2 hinzufügen

```python
openapi_schema["components"]["securitySchemes"]["OAuth2"] = {
    "type": "oauth2",
    "flows": {
        "authorizationCode": {
            "authorizationUrl": "/oauth/authorize",
            "tokenUrl": "/oauth/token",
            "scopes": {
                "read:geodaten": "Geodaten lesen",
                "read:unternehmen": "Unternehmen lesen"
            }
        }
    }
}
```
