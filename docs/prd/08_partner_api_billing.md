# UDO API - Partner-API & Billing-System

## Übersicht

Das Partner-API-System ermöglicht externen und internen Partnern den kostenpflichtigen Zugriff auf Unternehmensdaten und Geodaten. Jedes Projekt – auch interne – wird als Kunde behandelt, um Kosten transparent zu erfassen.

```
Partner (API-Client)
    │
    ├── API-Key / JWT Auth
    │
    ├── GET /partner/geodaten/*       → Geodaten abrufen (Kosten pro Einwohner)
    ├── GET /partner/unternehmen/*    → Unternehmen abrufen (Kosten pro Abfrage)
    │
    ├── Usage Tracking                → Jeder Abruf wird geloggt
    ├── Billing Account               → Credits / Rechnung / Stripe
    └── Rate Limiting                 → Schutz vor Missbrauch
```

## Geschäftsmodell

### Drei Abrechnungsmodelle

| Modell | Beschreibung | Zielgruppe |
|--------|-------------|------------|
| **credits** | Vorkasse – Partner lädt Credits auf, Abrufe werden abgezogen | Externe API-Clients, Self-Service |
| **invoice** | Auf Rechnung – monatliche Abrechnung mit Limit | Vertrauenswürdige Partner, Bestandskunden |
| **internal** | Interne Kostenstellenrechnung – keine echte Abrechnung | Eigene Projekte (VZ-Portale, Tests) |

Zukünftig geplant: **Stripe Pay-per-Use** – Echtzeit-Bezahlung vor Datenabruf (Phase 4.6).

### Kostenstruktur (bestehend)

| Abruf-Typ | Feld am Partner | Default | Beschreibung |
|-----------|----------------|---------|--------------|
| Geodaten (Kreise) | `kosten_geoapi_pro_einwohner` | 0.0001 EUR | Preis × gerundete Einwohnerzahl |
| Unternehmen | `kosten_unternehmen_pro_abfrage` | 0.001 EUR | Preis pro zurückgegebenes Unternehmen |

### Referenzimplementierung

**VZ Frühstücken-Klick** als erster interner Partner:
- Billing-Typ: `internal`
- Alle Abrufe werden geloggt und bepreist
- Keine echte Rechnungsstellung, aber volle Kostentransparenz
- Dient als Testbed für den gesamten Billing-Flow

---

## Phase 4.1: Usage Tracking & Kostenberechnung

**Ziel:** Jeder Partner-API-Call wird protokolliert und bepreist.

### Datenmodell

#### api_usage

Einzelne API-Aufrufe mit berechneten Kosten.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| partner_id | UUID | FK → api_partner |
| endpoint | String(100) | API-Endpoint (z.B. `/partner/unternehmen/`) |
| methode | String(10) | HTTP-Methode (GET, POST, etc.) |
| parameter | JSON | Query-Parameter (suche, geo_ort_id, etc.) |
| status_code | Integer | HTTP Response Status |
| anzahl_ergebnisse | Integer | Anzahl zurückgegebener Datensätze |
| kosten | Float | Berechnete Kosten für diesen Abruf |
| antwortzeit_ms | Integer | Response-Zeit in Millisekunden |
| erstellt_am | DateTime | Zeitstempel des Abrufs |

**Indizes:**
- `idx_usage_partner_id` auf partner_id
- `idx_usage_partner_date` auf (partner_id, erstellt_am)
- `idx_usage_endpoint` auf endpoint
- `idx_usage_erstellt_am` auf erstellt_am

#### api_usage_daily (Aggregation)

Tägliche Zusammenfassung pro Partner und Endpoint.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| partner_id | UUID | FK → api_partner |
| datum | Date | Tag der Aggregation |
| endpoint | String(100) | API-Endpoint |
| anzahl_abrufe | Integer | Anzahl Requests an diesem Tag |
| anzahl_ergebnisse_gesamt | Integer | Summe aller Ergebnisse |
| kosten_gesamt | Float | Summe aller Kosten |
| erstellt_am | DateTime | Erstellungszeitpunkt |

**Indizes:**
- `idx_daily_partner_datum` auf (partner_id, datum) – UNIQUE
- `idx_daily_datum` auf datum

### Kostenberechnung

#### Geodaten-Abrufe (bereits teilweise implementiert)

```
Kosten = Einwohner (gerundet auf 1000) × kosten_geoapi_pro_einwohner
```

Aktuell nur bei `/partner/geodaten/kreise` berechnet und angezeigt. Muss:
- Auch bei `/partner/geodaten/orte` und `/partner/geodaten/bundeslaender` Kosten berechnen
- In `api_usage` geloggt werden

#### Unternehmen-Abrufe (NEU)

```
Kosten = Anzahl zurückgegebener Unternehmen × kosten_unternehmen_pro_abfrage
```

Beispiel: Partner ruft 50 Unternehmen ab → 50 × 0.001 = 0.05 EUR

### API-Responses mit Kosten-Metadaten

Jede Partner-Response enthält ein `_meta`-Objekt:

```json
{
  "items": [...],
  "total": 1234,
  "_meta": {
    "kosten_abruf": 0.05,
    "kosten_monat_gesamt": 14.30,
    "guthaben_aktuell": 85.70,
    "abrufe_heute": 42
  }
}
```

### Implementierung

#### Middleware/Dependency

```python
async def track_usage(
    request: Request,
    response: Response,
    partner: ApiPartner,
    db: AsyncSession,
    kosten: float,
    anzahl_ergebnisse: int
):
    """Log API usage after successful response."""
```

Wird als FastAPI-Dependency in jeden Partner-Endpoint eingebaut.

#### Neue Endpoints

```
GET /api/v1/partner/usage/aktuell     → Eigene Nutzung: heute, dieser Monat
GET /api/v1/partner/usage/historie    → Tägliche Nutzungshistorie (paginiert)
```

Admin-Endpoints:
```
GET /api/v1/admin/usage/partner/{id}  → Nutzung eines Partners (Admin)
GET /api/v1/admin/usage/uebersicht    → Nutzungsübersicht aller Partner
```

### Dateien

| Datei | Aktion |
|-------|--------|
| `app/models/usage.py` | NEU: ApiUsage, ApiUsageDaily Models |
| `app/schemas/usage.py` | NEU: Pydantic Schemas |
| `app/services/usage.py` | NEU: UsageService (Logging, Aggregation) |
| `app/routes/partner_usage.py` | NEU: Partner-Usage-Endpoints |
| `app/routes/partner_geo.py` | ÄNDERN: Usage-Tracking einbauen |
| `app/routes/partner_com.py` | ÄNDERN: Usage-Tracking + Kostenberechnung |
| `app/routes/admin.py` | ERWEITERN: Admin-Usage-Endpoints |
| `alembic/versions/` | NEU: Migration für api_usage + api_usage_daily |

---

## Phase 4.2: Billing Accounts & Credit-System

**Ziel:** Drei Abrechnungsmodelle mit automatischer Zugangssteuerung.

### Datenmodell

#### api_billing_account

Abrechnungskonto pro Partner.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| partner_id | UUID | FK → api_partner (UNIQUE – 1:1) |
| billing_typ | String(20) | `credits`, `invoice`, `internal` |
| guthaben_cents | Integer | Aktuelles Guthaben in Cent (bei credits) |
| rechnungs_limit_cents | Integer | Max. monatliches Limit in Cent (bei invoice) |
| warnung_bei_cents | Integer | Warnung senden ab diesem Guthaben (default: 1000 = 10 EUR) |
| warnung_gesendet_am | DateTime | Letzte Warnung-E-Mail (nullable) |
| ist_gesperrt | Boolean | Zugang gesperrt? (default: false) |
| gesperrt_grund | String(255) | Grund der Sperrung (nullable) |
| gesperrt_am | DateTime | Zeitpunkt der Sperrung (nullable) |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

#### api_credit_transaction

Jede Guthabenbewegung (Aufladung, Abbuchung, Gutschrift).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| billing_account_id | UUID | FK → api_billing_account |
| typ | String(20) | `topup`, `usage`, `refund`, `adjustment` |
| betrag_cents | Integer | Betrag in Cent (positiv = Gutschrift, negativ = Abbuchung) |
| saldo_danach_cents | Integer | Kontostand nach Buchung |
| beschreibung | String(255) | z.B. "50 Unternehmen abgerufen" |
| referenz_typ | String(50) | z.B. `api_usage`, `stripe_payment`, `manual` |
| referenz_id | String(100) | z.B. Usage-ID, Stripe Payment-ID |
| erstellt_von | String(100) | `system`, `admin`, `stripe`, Partner-Name |
| erstellt_am | DateTime | Buchungszeitpunkt |

**Indizes:**
- `idx_credit_billing_id` auf billing_account_id
- `idx_credit_erstellt_am` auf erstellt_am
- `idx_credit_typ` auf typ

#### api_invoice (rudimentär)

Monatliche Abrechnungen.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| partner_id | UUID | FK → api_partner |
| rechnungsnummer | String(50) | z.B. `UDO-2026-02-001` (UNIQUE) |
| zeitraum_von | Date | Abrechnungsstart |
| zeitraum_bis | Date | Abrechnungsende |
| summe_netto_cents | Integer | Nettobetrag in Cent |
| summe_brutto_cents | Integer | Bruttobetrag (inkl. MwSt.) |
| mwst_satz | Float | MwSt.-Satz (default: 19.0) |
| status | String(20) | `entwurf`, `versendet`, `bezahlt`, `storniert` |
| positionen | JSON | Detail-Aufstellung |
| erstellt_am | DateTime | Erstellungszeitpunkt |
| aktualisiert_am | DateTime | Letzte Änderung |

### Zugangskontrolle

```
Vor jedem Partner-API-Call:
1. Billing-Account laden
2. Prüfe billing_typ:
   - credits: guthaben_cents > 0?
   - invoice: Monatsverbrauch < rechnungs_limit_cents?
   - internal: immer erlaubt
3. Falls nein → 402 Payment Required
4. Falls guthaben niedrig → X-Credits-Warning Header
```

HTTP Response bei Sperrung:
```json
{
  "detail": "Kein ausreichendes Guthaben. Bitte laden Sie Ihr Konto auf.",
  "guthaben_cents": 0,
  "billing_typ": "credits"
}
```

### Warnungen

| Trigger | Aktion |
|---------|--------|
| Guthaben < `warnung_bei_cents` | Response-Header `X-Credits-Warning: low` |
| Guthaben < `warnung_bei_cents` (erstmals) | E-Mail an Partner |
| Guthaben = 0 (credits) | API-Zugang sperren, 402 Response |
| Monats-Limit erreicht (invoice) | API-Zugang sperren, 402 Response |

### Neue Endpoints

```
GET  /api/v1/partner/billing               → Eigenes Abrechnungskonto
GET  /api/v1/partner/billing/transaktionen  → Credit-Transaktionen (paginiert)
GET  /api/v1/partner/billing/rechnungen     → Eigene Rechnungen
```

Admin-Endpoints:
```
GET    /api/v1/admin/billing/partner/{id}           → Billing-Account eines Partners
POST   /api/v1/admin/billing/partner/{id}/aufladen  → Credits manuell aufladen
POST   /api/v1/admin/billing/partner/{id}/sperren   → Zugang sperren
POST   /api/v1/admin/billing/partner/{id}/entsperren → Zugang entsperren
GET    /api/v1/admin/billing/rechnungen              → Alle Rechnungen
POST   /api/v1/admin/billing/rechnungen/generieren   → Monatsrechnungen erstellen
```

### Dateien

| Datei | Aktion |
|-------|--------|
| `app/models/billing.py` | NEU: ApiBillingAccount, ApiCreditTransaction, ApiInvoice |
| `app/schemas/billing.py` | NEU: Pydantic Schemas |
| `app/services/billing.py` | NEU: BillingService (Credit-Verwaltung, Rechnungen) |
| `app/routes/partner_billing.py` | NEU: Partner-Billing-Endpoints |
| `app/routes/admin.py` | ERWEITERN: Admin-Billing-Endpoints |
| `app/routes/partner_geo.py` | ÄNDERN: Billing-Check vor Abruf |
| `app/routes/partner_com.py` | ÄNDERN: Billing-Check + Credit-Abbuchung |
| `alembic/versions/` | NEU: Migration |

---

## Phase 4.3: Rate Limiting & Abuse Protection

**Ziel:** Technischer Schutz vor API-Missbrauch.

### Konfiguration

Erweiterung von `api_partner`:

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| rate_limit_pro_minute | Integer | Max. Requests/Minute (default: 60) |
| rate_limit_pro_stunde | Integer | Max. Requests/Stunde (default: 1000) |
| rate_limit_pro_tag | Integer | Max. Requests/Tag (default: 10000) |

### Response bei Überschreitung

```
HTTP 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706889600

{
  "detail": "Rate-Limit überschritten. Bitte warten Sie 30 Sekunden.",
  "limit": 60,
  "window": "minute",
  "retry_after_seconds": 30
}
```

### Standard-Headers in jeder Response

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1706889600
```

### Implementierung

Option A: **slowapi** (empfohlen für Start)
- Basiert auf limits-Library
- In-Memory Storage (Development) oder Redis (Production)
- Einfache Integration als FastAPI-Middleware

Option B: **Custom Middleware** mit Redis
- Mehr Kontrolle, aber mehr Aufwand
- Sinnvoll wenn komplexe Regeln nötig (z.B. Burst-Erkennung)

### Abuse Detection (rudimentär)

Täglicher Check via `api_usage_daily`:
- Partner mit > 5x Durchschnitts-Nutzung flaggen
- Admin-Benachrichtigung bei Anomalien

### Dateien

| Datei | Aktion |
|-------|--------|
| `app/middleware/rate_limit.py` | NEU: Rate-Limiting Middleware |
| `app/models/partner.py` | ÄNDERN: Rate-Limit-Felder hinzufügen |
| `app/schemas/partner.py` | ÄNDERN: Rate-Limit-Felder in Schemas |
| `alembic/versions/` | NEU: Migration |

---

## Phase 4.4: Partner-Verwaltung in udo__ui

**Ziel:** Admin-Oberfläche für Partner-Verwaltung und Monitoring.

### Routes

| Route | Methode | Funktion | API-Call |
|-------|---------|----------|----------|
| `/admin/partner/` | GET | Liste aller Partner | `GET /admin/partners` |
| `/admin/partner/neu` | GET/POST | Partner erstellen | `POST /admin/partners` |
| `/admin/partner/<id>` | GET | Detail + Usage + Billing | `GET /admin/partners/{id}` + Usage + Billing |
| `/admin/partner/<id>/bearbeiten` | GET/POST | Partner bearbeiten | `PATCH /admin/partners/{id}` |
| `/admin/partner/<id>/loeschen` | POST | Partner löschen | `DELETE /admin/partners/{id}` |
| `/admin/partner/<id>/key-regenerieren` | POST | Neuer API-Key | `POST /admin/partners/{id}/regenerate-key` |
| `/admin/partner/<id>/aufladen` | POST | Credits aufladen | `POST /admin/billing/partner/{id}/aufladen` |
| `/admin/partner/<id>/sperren` | POST | Zugang sperren | `POST /admin/billing/partner/{id}/sperren` |

### UI-Elemente

**Partner-Liste:**
- Tabelle mit Name, E-Mail, Rolle, Billing-Typ, Guthaben, Status
- HTMX Live-Suche
- Badge für gesperrte/inaktive Partner

**Partner-Detail:**
- Info-Karte (Name, E-Mail, API-Key-Status, Rolle)
- Billing-Karte (Typ, Guthaben, Limit, letzte Aufladung)
- Usage-Chart (Abrufe pro Tag, letzten 30 Tage)
- Kosten-Übersicht (Monat, Trend)
- Transaktionshistorie (letzte 20)

**Dashboard-Erweiterung:**
- Statistik-Kachel: Aktive Partner, Gesamt-Revenue Monat
- Warnung bei Partnern mit niedrigem Guthaben

### Templates

```
templates/admin/partner/
├── list.html
├── _table_body.html
├── form.html
├── detail.html
└── _usage_chart.html      (HTMX-Partial für Chart)
```

### Sidebar-Erweiterung

Neuer Menüpunkt unter "Datenverwaltung":
- **Partner** (ti-users) → /admin/partner/

---

## Phase 4.5: Rechnungsgenerierung

**Ziel:** Periodische Abrechnung für Partner mit Billing-Typ `invoice`.

### Flow

```
1. Monatlich (manuell oder Cron-Job):
   → Alle Partner mit billing_typ="invoice" laden
   → api_usage_daily für den Abrechnungszeitraum aggregieren
   → api_invoice erstellen mit Positionen
   → Status: "entwurf"

2. Admin prüft und versendet:
   → Status: "versendet"
   → Optional: PDF generieren und per E-Mail senden

3. Zahlung eingeht:
   → Status: "bezahlt"
```

### Rechnungspositionen (JSON)

```json
{
  "positionen": [
    {
      "beschreibung": "Geodaten-Abrufe (Kreise)",
      "anzahl": 150,
      "einzelpreis_cents": 10,
      "gesamt_cents": 1500
    },
    {
      "beschreibung": "Unternehmen-Abrufe",
      "anzahl": 3200,
      "einzelpreis_cents": 1,
      "gesamt_cents": 3200
    }
  ]
}
```

### Dateien

Erweitert `app/services/billing.py` um Rechnungsgenerierung.

---

## Phase 4.6: Stripe-Integration (zukünftig)

**Ziel:** Automatisierte Bezahlung über Stripe.

### Konzept

```
Partner-UI (vz_*-Portal)
    │
    ├── "Credits aufladen" → Stripe Checkout Session
    │   → Webhook → Credits gutschreiben
    │
    └── "Pay-per-Use" → Vor Datenabruf Stripe Payment Intent
        → Bei Erfolg → Daten zurückgeben
```

### Nicht in Phase 4.1-4.5 enthalten

- Stripe SDK Integration
- Webhook-Handler
- Checkout-UI in vz_*-Portalen
- Payment-Intent Flow

---

## Bestehendes System (Referenz)

### Bereits implementiert

| Bereich | Status | Dateien |
|---------|--------|---------|
| `api_partner` Model | Fertig | `app/models/partner.py` |
| API-Key Auth (SHA-256) | Fertig | `app/auth.py` |
| JWT Auth (HS256) | Fertig | `app/auth.py`, `app/services/jwt_service.py` |
| Partner-Admin CRUD | Fertig | `app/routes/admin.py`, `app/services/partner.py` |
| Partner Geo-Endpoints | Fertig | `app/routes/partner_geo.py` |
| Partner Com-Endpoints | Fertig | `app/routes/partner_com.py` |
| Auth-Flow (Login/Refresh) | Fertig | `app/routes/auth.py` |
| Rollenbasierte Docs | Fertig | `app/openapi_docs.py` |
| Kosten-Felder am Partner | Fertig | `kosten_geoapi_pro_einwohner`, `kosten_unternehmen_pro_abfrage` |
| Geodaten-Kostenberechnung | Teilweise | Nur bei `/partner/geodaten/kreise` |

### Noch nicht implementiert

| Bereich | Phase |
|---------|-------|
| Usage-Tracking (api_usage) | 4.1 |
| Kosten in Unternehmen-Responses | 4.1 |
| Kosten-Metadaten in Responses (_meta) | 4.1 |
| Billing-Accounts | 4.2 |
| Credit-System | 4.2 |
| Zugangs-Sperre bei 0 Credits | 4.2 |
| Warnungen (Header + E-Mail) | 4.2 |
| Rate Limiting | 4.3 |
| Partner Admin-UI | 4.4 |
| Rechnungsgenerierung | 4.5 |
| Stripe-Integration | 4.6 |

---

## Implementierungsreihenfolge

```
Phase 4.1  ──→  Phase 4.2  ──→  Phase 4.5
(Usage)         (Billing)        (Rechnungen)
    │
    ├──→  Phase 4.3 (Rate Limiting)
    │
    └──→  Phase 4.4 (Admin-UI) ──→ wächst mit jeder Phase
```

**Phase 4.1** ist das Fundament. Alles andere baut darauf auf.

**Phase 4.3** (Rate Limiting) und **Phase 4.4** (Admin-UI) können parallel zu Phase 4.2 beginnen.

**Phase 4.5** (Rechnungen) setzt Phase 4.2 voraus.

**Phase 4.6** (Stripe) ist unabhängig und für einen späteren Zeitpunkt geplant.
