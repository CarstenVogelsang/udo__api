# UDO API - Plugin Marketplace (Plg-Bereich)

## Übersicht

Der Plg-Bereich (Plugin) verwaltet das Plugin-Ökosystem für Satelliten-Projekte. Er ermöglicht die Registrierung, Lizenzierung und Preisgestaltung von Plugins für verschiedene Projekttypen.

```
PlgPlugin ──→ PlgPreis ←── PlgProjekttyp
     │             │              │
     └─────────────┼──────────────┘
                   ▼
              PlgProjekt
                   │
                   ▼
              PlgLizenz ──→ PlgLizenzHistorie
```

## Design-Entscheidungen

### Backend als Single Source of Truth

- Plugin-Metadaten werden initial aus `plugin.json` importiert
- Ab dann ist die Datenbank die Master-Quelle für alle geschäftlichen Daten
- Technischer Code bleibt im Dateisystem (v-flask Plugin-Struktur)

### Tabellenpräfix

- **plg_** analog zu **geo_**, **com_**, **etl_**
- Klassenname: **Plg**Plugin, **Plg**Lizenz, etc.

### Preismodell

- Preise sind **pro Plugin UND pro Projekttyp** definiert
- Ermöglicht unterschiedliche Preise für verschiedene Kundengruppen
- Preis-Snapshot in Lizenz für Abrechnungskonsistenz

### Authentifizierung

- JWT-Token (primär) - konsistent mit bestehendem Auth-System
- API-Key (Fallback) - für schnelle Lizenz-Checks

### Auto-Sync

- Beim API-Start werden neue Plugins automatisch registriert
- Bestehende Plugins werden aktualisiert (Version, Metadaten)

## Projekttypen

Satelliten-Projekte werden in vier Typen klassifiziert:

| Slug | Name | Beschreibung | Kostenlos | Testphase |
|------|------|--------------|-----------|-----------|
| `business_directory` | Business Directory | Branchenverzeichnisse mit hohem Datenvolumen | Nein | 14 Tage |
| `einzelkunde` | Einzelkunde | Normale Unternehmens-Webseiten | Nein | 30 Tage |
| `city_server` | City Server | Stadtportale und kommunale Projekte | Nein | 30 Tage |
| `intern` | Intern | Interne Projekte | Ja | - |

## Datenmodell

### plg_kategorie

Plugin-Kategorien für Organisation im Marketplace.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| slug | String(100) | URL-freundlicher Identifier (unique) |
| name | String(100) | Anzeigename |
| beschreibung | Text | Ausführliche Beschreibung |
| icon | String(50) | Tabler Icon Klasse |
| sortierung | Integer | Reihenfolge in UI |
| ist_aktiv | Boolean | Kategorie sichtbar? |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### plg_plugin

Plugin-Master-Daten. **Single Source of Truth** für Plugin-Metadaten.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| slug | String(100) | Eindeutiger Plugin-Identifier (unique) |
| name | String(255) | Plugin-Name |
| beschreibung | Text | Vollständige Beschreibung (Markdown) |
| beschreibung_kurz | String(500) | Kurzbeschreibung für Listen |
| kategorie_id | UUID | FK → plg_kategorie (nullable) |
| tags | JSON | Tag-Liste für Suche |
| version | String(20) | Aktuelle Version (Semantic Versioning) |
| version_datum | DateTime | Release-Datum der Version |
| status | Enum | aktiv, inaktiv, deprecated, entwicklung |
| dokumentation_url | String(500) | Link zur Dokumentation |
| changelog_url | String(500) | Link zum Changelog |
| min_api_version | String(20) | Mindest-API-Version |
| icon | String(50) | Tabler Icon Klasse |
| thumbnail_url | String(500) | Vorschaubild-URL |
| plugin_json_hash | String(64) | SHA-256 des ursprünglichen plugin.json |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

**Status-Enum:**

| Status | Beschreibung |
|--------|--------------|
| `entwicklung` | In Entwicklung, nicht im Marketplace |
| `aktiv` | Verfügbar für Lizenzierung |
| `inaktiv` | Temporär deaktiviert |
| `deprecated` | Veraltet, keine neuen Lizenzen |

### plg_plugin_version

Versionshistorie für Plugins.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| plugin_id | UUID | FK → plg_plugin |
| version | String(20) | Versionsnummer |
| changelog | Text | Änderungen (Markdown) |
| ist_aktuell | Boolean | Aktuelle Version? |
| ist_breaking_change | Boolean | Major Version Increment? |
| min_api_version | String(20) | Falls geändert |
| veroeffentlicht_am | DateTime | Release-Datum |
| erstellt_am | DateTime | Erstellungszeitpunkt |

### plg_projekttyp

Klassifizierung der Satelliten-Projekte.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| slug | String(50) | Identifier (unique) |
| name | String(100) | Anzeigename |
| beschreibung | Text | Beschreibung |
| ist_kostenlos | Boolean | Interne Projekte? |
| ist_testphase_erlaubt | Boolean | Testphase möglich? |
| standard_testphase_tage | Integer | Standard-Testdauer |
| max_benutzer | Integer | Soft Limit (nullable) |
| max_api_calls_pro_monat | Integer | Soft Limit (nullable) |
| icon | String(50) | Tabler Icon |
| sortierung | Integer | Reihenfolge |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### plg_preis

Preise pro Plugin × Projekttyp.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| plugin_id | UUID | FK → plg_plugin |
| projekttyp_id | UUID | FK → plg_projekttyp |
| modell | Enum | einmalig, monatlich, jaehrlich, nutzungsbasiert |
| preis | Float | Grundpreis in EUR |
| waehrung | String(3) | Währung (default: EUR) |
| staffel_ab_benutzer | Integer | Ab X Benutzern (nullable) |
| staffel_preis | Float | Reduzierter Preis (nullable) |
| preis_pro_api_call | Float | Nutzungsbasiert (nullable) |
| inkludierte_api_calls | Integer | Inkludiert (nullable) |
| einrichtungsgebuehr | Float | Setup-Gebühr (default: 0) |
| gueltig_ab | DateTime | Gültigkeitsstart |
| gueltig_bis | DateTime | Gültigkeitsende (nullable = unbegrenzt) |
| ist_aktiv | Boolean | Preis aktiv? |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

**Preismodell-Enum:**

| Modell | Beschreibung |
|--------|--------------|
| `einmalig` | Einmaliger Kauf |
| `monatlich` | Monatliches Abo |
| `jaehrlich` | Jährliches Abo |
| `nutzungsbasiert` | Pay-per-Use |

### plg_projekt

Satelliten-Installationen (Kunden/Mandanten).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| projekttyp_id | UUID | FK → plg_projekttyp |
| slug | String(100) | Identifier (unique) |
| name | String(255) | Projektname |
| beschreibung | Text | Beschreibung |
| kontakt_name | String(255) | Ansprechpartner |
| kontakt_email | String(255) | E-Mail |
| kontakt_telefon | String(50) | Telefon |
| api_key_hash | String(64) | SHA-256 des API-Keys (unique) |
| base_url | String(500) | URL der Installation |
| geo_ort_id | UUID | FK → geo_ort (nullable) |
| ist_aktiv | Boolean | Projekt aktiv? |
| aktiviert_am | DateTime | Aktivierungsdatum |
| deaktiviert_am | DateTime | Deaktivierungsdatum (nullable) |
| notizen | Text | Interne Notizen |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### plg_lizenz

N:M Beziehung zwischen Projekten und Plugins (Subscriptions).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| projekt_id | UUID | FK → plg_projekt |
| plugin_id | UUID | FK → plg_plugin |
| preis_id | UUID | FK → plg_preis (nullable) |
| lizenz_start | DateTime | Lizenzstart |
| lizenz_ende | DateTime | Lizenzende (nullable = unbefristet) |
| ist_testphase | Boolean | Testlizenz? |
| testphase_ende | DateTime | Testphase-Ende (nullable) |
| testphase_konvertiert | Boolean | In Vollversion umgewandelt? |
| status | Enum | testphase, aktiv, gekuendigt, abgelaufen, pausiert, storniert |
| gekuendigt_am | DateTime | Kündigungsdatum (nullable) |
| kuendigung_grund | Text | Kündigungsgrund (nullable) |
| kuendigung_zum | DateTime | Effektives Kündigungsdatum (nullable) |
| preis_snapshot | Float | Preis bei Vertragsabschluss |
| preis_modell_snapshot | String(20) | Preismodell bei Abschluss |
| plugin_version_bei_lizenzierung | String(20) | Plugin-Version bei Abschluss |
| notizen | Text | Interne Notizen |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

**Lizenz-Status-Enum:**

| Status | Beschreibung |
|--------|--------------|
| `testphase` | Kostenlose Testphase |
| `aktiv` | Aktive, bezahlte Lizenz |
| `gekuendigt` | Gekündigt, aber noch gültig bis Periodende |
| `abgelaufen` | Lizenz abgelaufen |
| `pausiert` | Temporär pausiert |
| `storniert` | Sofort storniert |

**Status-Lifecycle:**

```
                 ┌──────────────────────────────┐
                 ▼                              │
TESTPHASE ──→ AKTIV ──→ GEKÜNDIGT ──→ ABGELAUFEN
    │           │
    │           ▼
    └──→   STORNIERT
            PAUSIERT ←──→ AKTIV
```

### plg_lizenz_historie

Audit-Trail für Lizenz-Statusänderungen.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| lizenz_id | UUID | FK → plg_lizenz |
| alter_status | String(20) | Vorheriger Status |
| neuer_status | String(20) | Neuer Status |
| aenderungsgrund | String(255) | Grund für Änderung |
| notizen | Text | Zusätzliche Notizen |
| geaendert_von | UUID | User/Admin ID (nullable) |
| geaendert_von_typ | String(20) | system, admin, api, kunde |
| erstellt_am | DateTime | Änderungszeitpunkt |

## API-Endpunkte

### Plugin-Verwaltung (Admin)

```
GET    /api/v1/plugins                    # Liste aller Plugins
GET    /api/v1/plugins/{id}               # Plugin-Details
POST   /api/v1/plugins                    # Plugin erstellen
PUT    /api/v1/plugins/{id}               # Plugin aktualisieren
DELETE /api/v1/plugins/{id}               # Plugin löschen (soft delete)
POST   /api/v1/plugins/sync               # Manueller Plugin-Sync
```

### Marketplace (Öffentlich/Auth)

```
GET    /api/v1/marketplace/plugins        # Verfügbare Plugins
GET    /api/v1/marketplace/plugins/{slug} # Plugin-Details
GET    /api/v1/marketplace/kategorien     # Kategorien
GET    /api/v1/marketplace/preise/{plugin_slug}/{projekttyp_slug}  # Preis abrufen
```

### Projekt-Verwaltung (Admin)

```
GET    /api/v1/projekte                   # Liste aller Projekte
GET    /api/v1/projekte/{id}              # Projekt-Details
POST   /api/v1/projekte                   # Projekt erstellen
PUT    /api/v1/projekte/{id}              # Projekt aktualisieren
DELETE /api/v1/projekte/{id}              # Projekt deaktivieren
POST   /api/v1/projekte/{id}/api-key      # Neuen API-Key generieren
```

### Lizenz-Verwaltung

```
GET    /api/v1/lizenzen                   # Alle Lizenzen (Admin)
GET    /api/v1/lizenzen/{id}              # Lizenz-Details
POST   /api/v1/lizenzen                   # Lizenz erstellen
PUT    /api/v1/lizenzen/{id}              # Lizenz aktualisieren
POST   /api/v1/lizenzen/{id}/kuendigen    # Lizenz kündigen
POST   /api/v1/lizenzen/{id}/aktivieren   # Testphase → Aktiv
GET    /api/v1/lizenzen/{id}/historie     # Status-Historie

# Projekt-spezifisch
GET    /api/v1/projekte/{projekt_id}/lizenzen  # Lizenzen eines Projekts
```

### Lizenz-Check (Satelliten)

```
GET    /api/v1/lizenz-check/{plugin_slug}  # Hat aktuelles Projekt Lizenz?
```

Header: `Authorization: Bearer <JWT>` oder `X-API-Key: <key>`

Response:
```json
{
  "lizenziert": true,
  "status": "aktiv",
  "lizenz_ende": "2027-01-17T00:00:00Z",
  "plugin_version": "1.2.3"
}
```

## Indizes

| Tabelle | Index | Spalte(n) | Typ |
|---------|-------|-----------|-----|
| plg_kategorie | PK | id | Primary |
| plg_kategorie | UK | slug | Unique |
| plg_plugin | PK | id | Primary |
| plg_plugin | UK | slug | Unique |
| plg_plugin | IDX | status | B-Tree |
| plg_plugin | IDX | kategorie_id | FK |
| plg_plugin_version | PK | id | Primary |
| plg_plugin_version | IDX | plugin_id | FK |
| plg_plugin_version | UK | plugin_id, version | Unique Composite |
| plg_projekttyp | PK | id | Primary |
| plg_projekttyp | UK | slug | Unique |
| plg_preis | PK | id | Primary |
| plg_preis | IDX | plugin_id | FK |
| plg_preis | IDX | projekttyp_id | FK |
| plg_preis | IDX | ist_aktiv | B-Tree |
| plg_projekt | PK | id | Primary |
| plg_projekt | UK | slug | Unique |
| plg_projekt | UK | api_key_hash | Unique |
| plg_projekt | IDX | projekttyp_id | FK |
| plg_projekt | IDX | ist_aktiv | B-Tree |
| plg_lizenz | PK | id | Primary |
| plg_lizenz | IDX | projekt_id | FK |
| plg_lizenz | IDX | plugin_id | FK |
| plg_lizenz | IDX | status | B-Tree |
| plg_lizenz_historie | PK | id | Primary |
| plg_lizenz_historie | IDX | lizenz_id | FK |
| plg_lizenz_historie | IDX | erstellt_am | B-Tree |

## Beziehungen

```
plg_kategorie (1) ─────────────────> (n) plg_plugin
                                          │
                                          ├──> (n) plg_plugin_version
                                          │
plg_projekttyp (1) ─> (n) plg_preis <──> (n) plg_plugin
       │
       └──> (n) plg_projekt ─────────────> (n) plg_lizenz ──> (n) plg_lizenz_historie
                   │
                   └──> (1) geo_ort [optional]
```

## Geschäftsregeln

### Lizenzierung

1. **Testphase**: Jedes Projekt kann ein Plugin einmal testen (Dauer laut Projekttyp)
2. **Conversion**: Testphase kann in Vollversion umgewandelt werden
3. **Kündigung**: Gekündigte Lizenzen bleiben bis Periodenende aktiv
4. **Stornierung**: Sofortige Beendigung (nur bei Vertragsverletzung)

### Preise

1. **Preis-Snapshot**: Bei Lizenzierung wird der aktuelle Preis gespeichert
2. **Preisänderungen**: Betreffen nur neue Lizenzen
3. **Kostenlose Projekte**: Interne Projekte zahlen nichts

### Plugin-Sync

1. Beim API-Start werden alle `plugin.json` Dateien gescannt
2. Neue Plugins werden mit Status `entwicklung` registriert
3. Bestehende Plugins werden aktualisiert (Version, Metadaten)
4. Gelöschte Plugins werden auf `deprecated` gesetzt (nie löschen!)

## Dateien

| Datei | Beschreibung |
|-------|--------------|
| `app/models/plugin.py` | SQLAlchemy Models für plg_* Tabellen |
| `app/schemas/plugin.py` | Pydantic Schemas |
| `app/services/plugin.py` | Plugin-Management & Auto-Sync |
| `app/services/lizenz.py` | Lizenz-Lifecycle-Management |
| `app/routes/plugin.py` | Admin-CRUD Endpoints |
| `app/routes/marketplace.py` | Öffentliche Marketplace-Endpoints |
| `app/routes/projekt.py` | Projekt-Verwaltung |

## Beispiel: Lizenz-Flow

```python
# 1. Projekt erstellt Testlizenz
POST /api/v1/lizenzen
{
  "projekt_id": "...",
  "plugin_id": "...",
  "ist_testphase": true
}

# 2. Nach 30 Tagen: Testphase beenden → Aktiv
POST /api/v1/lizenzen/{id}/aktivieren

# 3. Nach 1 Jahr: Kündigung
POST /api/v1/lizenzen/{id}/kuendigen
{
  "grund": "Budget-Kürzung",
  "zum": "2027-12-31"
}

# 4. Lizenz-Check im Satelliten
GET /api/v1/lizenz-check/crm-basic
Authorization: Bearer <jwt>
→ {"lizenziert": true, "status": "gekuendigt", "lizenz_ende": "2027-12-31"}
```

## Zukünftige Erweiterungen

### Geplant

| Feature | Beschreibung |
|---------|--------------|
| Nutzungs-Tracking | API-Calls pro Lizenz zählen |
| Rechnungsstellung | Integration mit Buchhaltung |
| Plugin-Abhängigkeiten | Plugin A benötigt Plugin B |
| Plugin-Updates | Automatische Update-Benachrichtigungen |
| Marketplace-UI | Frontend für Plugin-Browsing |

### Nutzungs-Tracking (Konzept)

```python
class PlgNutzung(Base):
    __tablename__ = "plg_nutzung"

    lizenz_id = Column(UUID, ForeignKey("plg_lizenz.id"))
    monat = Column(String(7))  # "2026-01"
    api_calls = Column(Integer, default=0)
    datensaetze = Column(Integer, default=0)
```
