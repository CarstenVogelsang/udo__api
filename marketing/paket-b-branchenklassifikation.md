# Arbeitspaket B: Branchenklassifikation & unternehmensdaten.org-Endpunkte

> **Gesamtkontext:** Lies zuerst [`../README.md`](../README.md) für die Vision, das Geschäftsmodell und die Gesamtarchitektur des Marketing-Cockpits. Dieses Dokument ist eines von 9 Arbeitspaketen — siehe Abhängigkeitsgraph im README.

## 1. Projektkontext

### 1.1 Plattform
startklar.cloud ist eine Plattform für KMU-Unternehmenswebsites. Jeder Kunde bekommt eine branchenspezifische Website basierend auf einem "Starter" (Branchenvorlage). Bestehende Starter sind: baufinanzierungsberater, steuerberater, handwerker, beauty, spielwarengeschaeft, schallplattenhaendler, familienplaner und unternehmenswebsite.

### 1.2 unternehmensdaten.org
Eine bestehende Flask-API, die Unternehmensdaten aggregiert. Wird von allen startklar.cloud-Projekten als zentrale Datenquelle genutzt. Hat bereits Endpunkte für Firmendaten, aber noch KEINEN Endpunkt für Branchenklassifikation, Branchenverzeichnisse oder regionale Gruppen.

### 1.3 Warum dieses Paket
Die Marketing-Automatisierung (Phase 1: "Sichtbar werden") braucht branchenspezifische Empfehlungen: Welche Branchenverzeichnisse sind für einen Steuerberater relevant? Welche Facebook-Gruppen für einen Friseur in Köln? Diese Information muss zentral in unternehmensdaten.org gepflegt werden, damit jede Kundeninstanz sie abfragen kann.

### 1.4 Zwei Codebasen
Dieses Paket betrifft ZWEI getrennte Projekte:
1. **unternehmensdaten.org** — Die zentrale API (neuer Endpunkt für Branchen, Verzeichnisse, Gruppen)
2. **VRS-Marketplace** — Die starter.toml jedes Starters (Erweiterung um Branchenfelder)

## 2. Teil 1: starter.toml Erweiterung

### 2.1 Neuer Block [starter.branche]

Jeder bestehende Starter bekommt in seiner `starter.toml` einen neuen Block:

```toml
[starter.branche]
wz_code = "69.20.1"                    # WZ-2008 Klassifikation (Statistisches Bundesamt)
wz_bezeichnung = "Steuerberatung"
google_kategorie = "Tax Consultant"     # Google Business Profile Kategorie (englisch)
google_kategorie_de = "Steuerberater"   # Google Business Profile Kategorie (deutsch)
weitere_kategorien = ["Buchhalter", "Wirtschaftsprüfer"]  # Verwandte Kategorien (optional)
```

### 2.2 Konkrete WZ-Codes pro Starter

Die KI muss die korrekten WZ-2008-Codes recherchieren und eintragen:

| Starter | WZ-Code | WZ-Bezeichnung | Google-Kategorie |
|---------|---------|----------------|------------------|
| baufinanzierungsberater | 66.19.2 | Sonstige Finanzdienstleistungen | Mortgage Broker |
| steuerberater | 69.20.1 | Buchführung, Steuerberatung | Tax Consultant |
| handwerker | Variabel nach Gewerk | z.B. 43.21 (Elektroinstallation) | Electrician / Plumber / etc. |
| beauty | 96.02.1 / 96.04 | Frisörsalons / Kosmetik | Hair Salon / Beauty Salon |
| spielwarengeschaeft | 47.65 | Einzelhandel mit Spielwaren | Toy Store |
| schallplattenhaendler | 47.63 | Einzelhandel mit Musikinstrumenten | Record Store |
| familienplaner | — | Nicht zutreffend (Personal App) | — |
| unternehmenswebsite | Variabel | Je nach Branche des Kunden | Variabel |

Für Starter mit variablem WZ-Code (handwerker, unternehmenswebsite) wird der WZ-Code beim Checkout dynamisch gesetzt, nicht in der starter.toml hartcodiert. Die starter.toml enthält dann eine Liste möglicher WZ-Codes.

## 3. Teil 2: unternehmensdaten.org — Neue Modelle

### 3.1 Branche (WZ-2008 Klassifikation)

```python
class Branche(db.Model):
    __tablename__ = "branche"
    id = Column(Integer, primary_key=True)
    wz_code = Column(String(10), unique=True, nullable=False, index=True)  # z.B. "69.20.1"
    bezeichnung = Column(String(200), nullable=False)                       # z.B. "Steuerberatung"
    ebene = Column(Integer, nullable=False)                                 # 1=Abschnitt, 2=Abt., 3=Gruppe, 4=Klasse, 5=Unterklasse
    parent_wz_code = Column(String(10), nullable=True)                     # Übergeordneter WZ-Code
    google_kategorie = Column(String(200), nullable=True)                  # Google Business Kategorie
    google_kategorie_de = Column(String(200), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
```

### 3.2 Branchenverzeichnis

```python
class AnmeldeArt(enum.Enum):
    ONLINE_FORMULAR = "online_formular"
    API = "api"
    MANUELL = "manuell"                  # z.B. Kammer-Eintrag
    PARTNER_DIENST = "partner_dienst"    # Über Yext/Uberall etc.

class KostenModell(enum.Enum):
    KOSTENLOS = "kostenlos"
    FREEMIUM = "freemium"               # Basis kostenlos, Premium kostenpflichtig
    KOSTENPFLICHTIG = "kostenpflichtig"

class Branchenverzeichnis(db.Model):
    __tablename__ = "branchenverzeichnis"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)                  # z.B. "Gelbe Seiten"
    url = Column(String(500), nullable=False)                   # z.B. "https://www.gelbeseiten.de"
    beschreibung = Column(Text, nullable=True)
    branche_wz_code = Column(String(10), nullable=True)        # null = branchenübergreifend
    ist_branchenuebergreifend = Column(Boolean, default=False)  # Gelbe Seiten, Das Örtliche, etc.
    hat_api = Column(Boolean, default=False)
    api_dokumentation_url = Column(String(500), nullable=True)
    anmeldeart = Column(Enum(AnmeldeArt), nullable=False)
    anmelde_url = Column(String(500), nullable=True)           # Direkt-Link zum Registrierungsformular
    kosten = Column(Enum(KostenModell), nullable=False)
    kosten_details = Column(String(200), nullable=True)        # z.B. "Premium ab 29€/Monat"
    relevanz_score = Column(Integer, default=5)                # 1-10, höher = wichtiger
    regionen = Column(JSON, default=list)                      # ["DE", "AT", "CH"] oder leer = weltweit
    anleitung_url = Column(String(500), nullable=True)         # Link zu Anleitung "So tragen Sie sich ein"
    logo_url = Column(String(500), nullable=True)
    ist_aktiv = Column(Boolean, default=True)
    zuletzt_geprueft = Column(Date, nullable=True)
    erstellt_am = Column(DateTime, default=func.now())
```

### 3.3 Regionale Gruppe (Facebook, LinkedIn, etc.)

```python
class GruppenPlattform(enum.Enum):
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    XING = "xing"
    NEXTDOOR = "nextdoor"
    SONSTIGE = "sonstige"

class RegionaleGruppe(db.Model):
    __tablename__ = "regionale_gruppe"
    id = Column(Integer, primary_key=True)
    plattform = Column(Enum(GruppenPlattform), nullable=False)
    name = Column(String(200), nullable=False)                     # z.B. "Handwerker gesucht in Berlin"
    url = Column(String(500), nullable=False)
    beschreibung = Column(Text, nullable=True)
    branche_wz_code = Column(String(10), nullable=True)           # null = branchenübergreifend regional
    region_plz_prefix = Column(String(5), nullable=True)          # z.B. "50" für Köln-Raum, "10" für Berlin
    region_name = Column(String(100), nullable=True)              # z.B. "Köln", "Berlin-Mitte"
    region_bundesland = Column(String(50), nullable=True)         # z.B. "NRW", "Bayern"
    mitglieder_anzahl = Column(Integer, nullable=True)
    werbung_erlaubt = Column(Boolean, default=False)
    posting_regeln = Column(Text, nullable=True)                  # Zusammenfassung der Gruppenregeln
    empfohlene_posting_art = Column(String(100), nullable=True)   # z.B. "Nur Vorstellungsposts", "Angebote erlaubt"
    ist_aktiv = Column(Boolean, default=True)
    zuletzt_geprueft = Column(Date, nullable=True)
    erstellt_am = Column(DateTime, default=func.now())
```

### 3.4 GoogleKategorie (Google Business Profile Kategorien)

```python
class GoogleKategorie(db.Model):
    __tablename__ = "google_kategorie"
    id = Column(Integer, primary_key=True)
    gcid = Column(String(100), unique=True, nullable=False, index=True)  # z.B. "gcid:tax_consultant"
    name_de = Column(String(200), nullable=False)                        # z.B. "Steuerberater"
    name_en = Column(String(200), nullable=False)                        # z.B. "Tax consultant"
    ist_aktiv = Column(Boolean, default=True)
    zuletzt_aktualisiert = Column(DateTime, default=func.now())
    erstellt_am = Column(DateTime, default=func.now())
```

**Hintergrund:** Google Business Profile verwendet ein eigenes, proprietäres Kategorie-System mit ca. 4.100 stabilen Kategorien (GCIDs). Diese Kategorien sind NICHT kompatibel mit WZ-2008 oder NACE. Es gibt kein öffentliches Crosswalk-Mapping.

**Datenquelle:** Google Business Profile API v1 `categories.list`
- Endpoint: `https://mybusinessbusinessinformation.googleapis.com/v1/categories`
- Parameter: `regionCode=DE`, `languageCode=de` (und `en` für englische Namen)
- Pagination: `pageSize=100`, `pageToken` für nächste Seite
- Erfordert OAuth2 mit `business.manage` Scope
- Response enthält: `categoryId` (GCID), `displayName`, `serviceTypes[]`

**Referenz-Listen:**
- PlePer Tools: https://pleper.com/index.php?do=tools&sdo=gmb_categories
- Google API Docs: https://developers.google.com/my-business/reference/businessinformation/rest/v1/categories/list

### 3.5 BrancheGoogleMapping (WZ-2008 ↔ Google-Kategorien)

```python
class BrancheGoogleMapping(db.Model):
    __tablename__ = "branche_google_mapping"
    id = Column(Integer, primary_key=True)
    wz_code = Column(String(10), ForeignKey("branche.wz_code"), nullable=False, index=True)
    gcid = Column(String(100), ForeignKey("google_kategorie.gcid"), nullable=False, index=True)
    ist_primaer = Column(Boolean, default=False)  # Primäre Kategorie für diesen WZ-Code?
    relevanz = Column(Integer, default=5)          # 1-10, wie relevant ist die Zuordnung
    erstellt_am = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("wz_code", "gcid", name="uq_branche_google_mapping"),
    )
```

**Mapping-Logik:**
- Many-to-Many: 1 WZ-Code kann mehrere Google-Kategorien haben und umgekehrt
- `ist_primaer=True` markiert DIE Hauptkategorie für einen WZ-Code (max. 1 pro WZ-Code)
- `relevanz` (1-10) gewichtet die Zuordnung für UI-Sortierung
- Initiales Mapping wird manuell/KI-gestützt für die Starter-Branchen erstellt

**Beispiel-Mapping:**
| WZ-Code | GCID | Primär | Relevanz |
|---------|------|--------|----------|
| 69.20.1 | gcid:tax_consultant | Ja | 10 |
| 69.20.1 | gcid:accountant | Nein | 7 |
| 96.02.1 | gcid:hair_salon | Ja | 10 |
| 96.02.1 | gcid:beauty_salon | Nein | 8 |
| 43.21 | gcid:electrician | Ja | 10 |
| 47.65 | gcid:toy_store | Ja | 10 |

## 4. API-Endpunkte (unternehmensdaten.org)

```
# Branchen (WZ-2008)
GET /api/v1/branchen                              # Alle Branchen (hierarchisch oder flach)
    ?ebene=3                                       # Filter nach Ebene
    ?suche=steuer                                  # Textsuche in Bezeichnung
GET /api/v1/branchen/{wz_code}                     # Eine Branche mit Details
GET /api/v1/branchen/{wz_code}/kinder              # Unterkategorien einer Branche

# Branchenverzeichnisse
GET /api/v1/branchen/{wz_code}/verzeichnisse       # Verzeichnisse für diese Branche
    ?region=DE                                      # Optional: Region filtern
    ?kosten=kostenlos                               # Optional: Kostenfilter
GET /api/v1/verzeichnisse                           # Alle Verzeichnisse (branchenübergreifend)
    ?branchenuebergreifend=true                     # Nur allgemeine Verzeichnisse
GET /api/v1/verzeichnisse/{id}                      # Einzelnes Verzeichnis mit Details

# Google-Kategorien (GMB)
GET /api/v1/google-kategorien                        # Alle Google-Kategorien
    ?suche=steuer                                     # Textsuche in Name (de/en)
    ?aktiv=true                                       # Nur aktive Kategorien
GET /api/v1/google-kategorien/{gcid}                  # Einzelne Kategorie (z.B. gcid:tax_consultant)
GET /api/v1/branchen/{wz_code}/google-kategorien      # Gemappte Kategorien für WZ-Code
    ?nur_primaer=true                                 # Nur primäre Kategorien

# Regionale Gruppen
GET /api/v1/branchen/{wz_code}/gruppen              # Gruppen für Branche
    ?plz_prefix=50                                  # PLZ-Filter (Raum Köln)
    ?plattform=facebook                             # Plattform-Filter
    ?werbung_erlaubt=true                           # Nur Gruppen wo Werbung OK ist
GET /api/v1/gruppen                                 # Alle Gruppen
    ?region_bundesland=NRW                          # Bundesland-Filter
GET /api/v1/gruppen/{id}                            # Einzelne Gruppe mit Details
```

### 4.1 Response-Beispiel: Verzeichnisse für Steuerberater

```json
GET /api/v1/branchen/69.20.1/verzeichnisse

{
  "branche": {
    "wz_code": "69.20.1",
    "bezeichnung": "Steuerberatung"
  },
  "verzeichnisse": [
    {
      "id": 1,
      "name": "steuerberater.de",
      "url": "https://www.steuerberater.de",
      "anmeldeart": "online_formular",
      "anmelde_url": "https://www.steuerberater.de/kanzlei-eintragen",
      "kosten": "freemium",
      "kosten_details": "Basis kostenlos, Premium ab 49€/Monat",
      "relevanz_score": 9,
      "ist_branchenuebergreifend": false
    },
    {
      "id": 2,
      "name": "Gelbe Seiten",
      "url": "https://www.gelbeseiten.de",
      "anmeldeart": "online_formular",
      "anmelde_url": "https://www.gelbeseiten.de/eintrag-erstellen",
      "kosten": "freemium",
      "relevanz_score": 7,
      "ist_branchenuebergreifend": true
    }
  ],
  "gesamt": 8
}
```

## 5. Seed-Daten

### 5.1 WZ-2008 Klassifikation

Die vollständige WZ-2008 Klassifikation ist öffentlich verfügbar beim Statistischen Bundesamt. Für den Initial-Seed reichen die relevanten Branchen der bestehenden Starter (ca. 50-100 WZ-Codes). Die KI soll die WZ-2008-Daten recherchieren und als Seed-JSON erstellen.

### 5.2 Branchenverzeichnisse — initiale Kuration

Mindestens folgende Verzeichnisse als Seed:

**Branchenübergreifend (allgemein):**
- Gelbe Seiten (gelbeseiten.de)
- Das Örtliche (dasoertliche.de)
- 11880 (11880.com)
- GoYellow (goyellow.de)
- Yelp (yelp.de)
- Google My Business (business.google.com) — ja, auch das ist ein "Verzeichnis"
- Bing Places (bingplaces.com)
- Apple Maps Connect (mapsconnect.apple.com)

**Steuerberater:**
- steuerberater.de
- DATEV-Kanzleisuche
- Steuerberaterkammer-Verzeichnisse (pro Bundesland)
- WLW (wer-liefert-was.de) — wenn auch B2B-Dienstleistungen

**Handwerker:**
- MyHammer (myhammer.de)
- Handwerkerverzeichnis der HWK (pro Kammer)
- Check24 Handwerker
- Blauarbeit (blauarbeit.de)

**Beauty/Friseur:**
- Treatwell (treatwell.de)
- Friseur.com
- Jameda (für Kosmetik/Wellness)

**Spielwaren:**
- Spielzeug.de
- idealo.de (Preisvergleich)

**Baufinanzierung:**
- WhoFinance (whofinance.de)
- CHECK24 Baufinanzierung

### 5.3 Regionale Gruppen — initiale Kuration

Pro Starter-Branche mindestens 10-15 Facebook-Gruppen für verschiedene Regionen (Berlin, München, Köln, Hamburg, Frankfurt, Stuttgart etc.)

Beispiel-Format:
```json
{
  "plattform": "facebook",
  "name": "Handwerker gesucht in Berlin",
  "url": "https://www.facebook.com/groups/handwerker-berlin",
  "branche_wz_code": "43",
  "region_plz_prefix": "10",
  "region_name": "Berlin",
  "region_bundesland": "Berlin",
  "mitglieder_anzahl": 15000,
  "werbung_erlaubt": true,
  "posting_regeln": "Vorstellung erlaubt, keine reinen Werbeposts, Bilder erwünscht",
  "empfohlene_posting_art": "Vorstellung + Referenzprojekt"
}
```

### 5.4 Google-Kategorien Sync

Ein CLI-Command oder Script zum Synchronisieren der Google-Kategorien:

```bash
# Initial-Sync aller ~4.100 Kategorien
python -m scripts.sync_google_kategorien --region DE --language de,en

# Monatlicher Update (nur geänderte/neue Kategorien)
python -m scripts.sync_google_kategorien --update-only
```

**Workflow:**
1. OAuth2-Token für Google Business Profile API beschaffen
2. `categories.list` aufrufen mit `regionCode=DE`, `languageCode=de` (und `en`)
3. Durch alle Seiten paginieren (pageSize=100, pageToken)
4. Pro Kategorie: `categoryId` (GCID), `displayName` speichern
5. Bestehende Einträge aktualisieren, neue anlegen, gelöschte als `ist_aktiv=False` markieren
6. Sollte monatlich laufen (Google ändert Kategorien regelmäßig)

### 5.5 Initiales WZ→Google Mapping (Seed)

Für die Starter-Branchen manuell/KI-gestützt erstellen und als `seed/branche_google_mapping.json` ablegen:

```json
[
  {"wz_code": "69.20.1", "gcid": "gcid:tax_consultant", "ist_primaer": true, "relevanz": 10},
  {"wz_code": "69.20.1", "gcid": "gcid:accountant", "ist_primaer": false, "relevanz": 7},
  {"wz_code": "96.02.1", "gcid": "gcid:hair_salon", "ist_primaer": true, "relevanz": 10},
  {"wz_code": "96.02.1", "gcid": "gcid:beauty_salon", "ist_primaer": false, "relevanz": 8},
  {"wz_code": "43.21", "gcid": "gcid:electrician", "ist_primaer": true, "relevanz": 10},
  {"wz_code": "47.65", "gcid": "gcid:toy_store", "ist_primaer": true, "relevanz": 10},
  {"wz_code": "47.63", "gcid": "gcid:record_store", "ist_primaer": true, "relevanz": 10},
  {"wz_code": "66.19.2", "gcid": "gcid:mortgage_broker", "ist_primaer": true, "relevanz": 10}
]
```

**WICHTIG:** Die Gruppen-URLs und Mitgliederzahlen müssen REALISTISCH sein, aber die KI soll sie NICHT live recherchieren (kein Web-Scraping von Facebook). Stattdessen sollen die Seed-Daten als BEISPIELE gekennzeichnet werden, die manuell verifiziert und ergänzt werden müssen. Die Struktur und das Format müssen stimmen, die konkreten Daten sind initial Platzhalter.

## 6. Verzeichnisstruktur (unternehmensdaten.org)

```
# Neue Dateien in unternehmensdaten.org
models/
├── branche.py                  # Branche Model
├── branchenverzeichnis.py      # Branchenverzeichnis Model
├── regionale_gruppe.py         # RegionaleGruppe Model
├── google_kategorie.py         # GoogleKategorie Model
└── branche_google_mapping.py   # BrancheGoogleMapping Model

routes/
├── branchen.py                 # /api/v1/branchen/... Endpunkte
├── verzeichnisse.py            # /api/v1/verzeichnisse/... Endpunkte
├── gruppen.py                  # /api/v1/gruppen/... Endpunkte
└── google_kategorien.py        # /api/v1/google-kategorien/... Endpunkte

scripts/
└── sync_google_kategorien.py   # Google Categories API Sync-Script

seed/
├── wz_2008_branchen.json       # WZ-Klassifikation
├── verzeichnisse_seed.json     # Kuratierte Branchenverzeichnisse
├── gruppen_seed.json           # Kuratierte regionale Gruppen
└── branche_google_mapping.json # WZ→Google Kategorie Mapping
```

## 7. Implementierungshinweise

### 7.1 Datenbankmigrationen

Für jedes neue Model ist eine Alembic-Migration zu erstellen. Diese Migrationen müssen die folgenden Tabellen anlegen:
- `branche` mit Index auf `wz_code`
- `branchenverzeichnis` mit Foreign-Key zu `branche` (falls parent-child-Beziehung)
- `regionale_gruppe` mit Foreign-Key zu `branche`

Die Migrations-Scripts sollten konsistent mit den bestehenden Patterns in unternehmensdaten.org sein.

### 7.2 API-Implementierung

Die neuen Endpunkte folgen dem RESTful-Muster der bestehenden API:
- JSON-Response mit `data` und `meta`-Feldern
- Pagination für große Datenmengen
- Fehlerbehandlung mit konsistenten HTTP-Status-Codes
- Logging aller Anfragen

### 7.3 WZ-2008-Daten

Das Statistische Bundesamt (DESTATIS) veröffentlicht die WZ-2008-Klassifikation regelmäßig. Für den Initial-Seed:
1. Relevante WZ-Codes der bestehenden Starter manuell recherchieren
2. Hierarchie-Beziehungen (parent_wz_code) dokumentieren
3. Als JSON-Seed-Datei strukturieren
4. Mit Python-Script in die Datenbank laden

Nicht alle 2000+ WZ-Codes importieren, sondern nur die für diese Plattform relevanten.

### 7.4 Text-Lokalisierung

Alle Texte in Seed-Daten und Responses sind auf Deutsch. API-Feldnamen bleiben englisch, Werte sind deutsch (z.B. `"bezeichnung": "Steuerberatung"`).

## 8. Abnahmekriterien

1. **starter.toml Erweiterung:** Alle bestehenden Starter haben korrekte WZ-Codes in ihrer starter.toml mit den obligatorischen Feldern (wz_code, wz_bezeichnung, google_kategorie, google_kategorie_de)

2. **Branchen-API:** Der Endpunkt `GET /api/v1/branchen/69.20.1/verzeichnisse` liefert mindestens 8 relevante Verzeichnisse für Steuerberater, sortiert nach Relevanz-Score

3. **Regionale Gruppen:** Der Endpunkt `GET /api/v1/branchen/96.02.1/gruppen?plz_prefix=50` liefert mindestens 5 Facebook-Gruppen für Friseure im Raum Köln mit realistischen Mitgliederzahlen

4. **Branchenübergreifende Verzeichnisse:** Branchenübergreifende Verzeichnisse (Gelbe Seiten, Das Örtliche) werden IMMER zusätzlich zu branchenspezifischen Verzeichnissen mit zurückgegeben

5. **Seed-Daten Vollständigkeit:** Seed-Daten enthalten mindestens 8 allgemeine + 15 branchenspezifische Verzeichnisse mit korrekten Metadaten

6. **Regionale Gruppen Vielfalt:** Seed-Daten enthalten mindestens 30 regionale Gruppen über verschiedene Branchen und Regionen (mindestens 5 Bundesländer und 3 Plattformen)

7. **WZ-Hierarchie:** WZ-2008-Hierarchie ist navigierbar über Endpunkte wie `GET /api/v1/branchen/{wz_code}/kinder`

8. **Fehlerbehandlung:** API gibt sinnvolle Fehlermeldungen für ungültige WZ-Codes oder nicht vorhandene Ressourcen zurück (404, 400)

9. **Performance:** Endpunkte mit großen Datenmengen sind gepaginiert, Responses unter 5 Sekunden

10. **Konsistenz:** Neue API folgt den Code-Standards und Mustern von unternehmensdaten.org

11. **Google-Kategorien Model:** GoogleKategorie-Tabelle ist implementiert mit GCID, name_de, name_en und kann über API abgefragt werden

12. **WZ→Google Mapping:** BrancheGoogleMapping ist implementiert als Many-to-Many mit ist_primaer und relevanz. Initiale Seed-Daten für alle Starter-Branchen vorhanden

13. **Google-Kategorien Sync:** CLI-Script zum Synchronisieren der Google-Kategorien via Business Profile API ist implementiert und dokumentiert

14. **Mapping-API:** `GET /api/v1/branchen/{wz_code}/google-kategorien` liefert gemappte Google-Kategorien sortiert nach Relevanz, mit primärer Kategorie zuerst

## 9. Hinweise für die implementierende KI

- Die bestehende unternehmensdaten.org-Codebasis hat ihre eigenen Conventions — bitte vorhandene Models und Routes analysieren, bevor neue Endpunkte geschrieben werden
- Die starter.toml Dateien liegen im VRS-Marketplace unter `/starters/{name}-starter/starter.toml`
- Für WZ-2008-Daten: Das Statistische Bundesamt (DESTATIS) bietet Klassifikationen als downloadbare XML oder CSV an — die KI soll die relevanten Codes manuell recherchieren und zuordnen
- Alle Beschreibungen und Texte sind auf Deutsch zu verfassen
- Response-Format orientiert sich an bestehenden unternehmensdaten.org-Endpunkten
- Foreign-Keys und Constraints müssen in Migrationen definiert sein
- Seed-Daten sind idempotent (mehrfaches Laden ändert nichts)
- Tests für alle neuen Endpunkte mit pytest schreiben

## 10. Zeitrahmen & Ressourcen

Dieses Arbeitspaket umfasst zwei getrennte Codebasen und sollte systematisch angegangen werden:

**Phase 1: Vorbereitung (Tag 1-2)**
- starter.toml Struktur analysieren
- unternehmensdaten.org Code studieren
- WZ-2008-Codes für bestehende Starter recherchieren

**Phase 2: Modelle & Migrations (Tag 3-4)**
- Drei Models (Branche, Branchenverzeichnis, RegionaleGruppe) implementieren
- Alembic-Migrationen erstellen und testen
- Seed-Daten strukturieren

**Phase 3: API-Endpunkte (Tag 5-7)**
- Sechs Haupt-Endpunkte implementieren
- Filterung, Pagination, Fehlerbehandlung
- Tests schreiben

**Phase 4: Integration & QA (Tag 8)**
- starter.toml aller Starter aktualisieren
- Seed-Daten laden
- End-to-End-Tests durchführen
- Abnahmekriterien überprüfen

---

**Dokument Version:** 1.1 (erweitert um Google Business Kategorien + WZ-Mapping)
**Zuletzt aktualisiert:** 2026-02-12
**Status:** Zur Implementierung bereit
**Verantwortlicher:** Claude Code Agent
