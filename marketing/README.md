# Marketing-Cockpit: Vision & Architektur

## Worum geht es?

startklar.cloud ist eine Plattform, die KMU-Unternehmen (Handwerker, Steuerberater, Friseursalons, Spielwarengeschäfte, Hersteller, …) professionelle Websites liefert — basierend auf branchenspezifischen „Startern". Jeder Starter ist eine vorkonfigurierte Website mit passenden Plugins, Inhalten und Design.

**Das Problem:** Die Website steht im Internet — und dann? Die meisten KMU-Betreiber wissen nicht, wie sie ihre neue Website sichtbar machen. Sie haben weder Marketing-Know-how noch Zeit, sich in Google My Business, Social Media, SEO oder Newsletter-Marketing einzuarbeiten. Die Website existiert, aber niemand findet sie.

**Unsere Lösung:** Ein **Marketing-Cockpit** direkt im Admin-Bereich der Website, das den Kunden Schritt für Schritt führt: „Deine Website ist startklar — und jetzt machen wir sie sichtbar." Das unterscheidet uns fundamental von Jimdo, Wix oder WordPress, die sagen: „Hier ist dein Baukasten, viel Erfolg."

---

## Das Geschäftsmodell: Drei Stufen

Jede Marketing-Maßnahme wird in drei Varianten angeboten:

### Stufe 1 — Selbst machen (kostenlos oder Mikropayment)
Der Kunde sieht eine Checkliste im Backend mit den wichtigsten Maßnahmen. Zu jedem Punkt gibt es eine kurze Erklärung. Wenn er es selbst machen will, kann er eine Schritt-für-Schritt-Anleitung freischalten (1,99–4,99 €) — als Video, PDF oder interaktives Tutorial. Die KI generiert konkrete Texte (Pressemitteilung, Social-Media-Post, Google-Beschreibung) direkt im Backend.

### Stufe 2 — Assisted (Paket-Preise)
Wir machen es gemeinsam oder für ihn. Beispiele: „Google-My-Business-Einrichtung" für 49 €, „Social-Media-Startpaket" (3 Plattformen + 10 Postings) für 149 €, „SEO-Grundpaket" (Search Console + Sitemap + 5 Keywords) für 99 €. Der Kunde bucht direkt im Backend, startklar.cloud oder beauftragte Dritte setzen es um.

### Stufe 3 — Done-for-you (Abo / Retainer)
Laufende Betreuung: „Social-Media-Management" für 199 €/Monat, „Google-Ads-Betreuung" für 149 €/Monat + Werbebudget, „Content-Paket" für 249 €/Monat. Wiederkehrende Einnahmen, der Kunde muss sich um nichts kümmern.

---

## Die vier Phasen nach dem Go-Live

### Phase 1 — Grundlagen: „Sichtbar werden"
Basiseinträge und Grundkonfiguration, die jeder Websitebetreiber als Erstes tun sollte:

- **Google My Business** — Der wichtigste erste Schritt für lokale Unternehmen. Eintrag anlegen, Adresse verifizieren, Öffnungszeiten und Fotos pflegen, Link zur Website setzen. Danach automatische Synchronisation über die Google Business Profile API.
- **Google Search Console** — Damit Google die Website kennt. Sitemap einreichen, Indexierung prüfen, Suchbegriffe und Klicks auswerten. Automatisierbar über die Search Console API.
- **Branchenverzeichnisse** — Je nach Branche relevante Portale: MyHammer, Gelbe Seiten, steuerberater.de, Treatwell etc. Die passenden Verzeichnisse werden branchenspezifisch aus unserer zentralen API (unternehmensdaten.org) geladen.
- **Social-Media-Präsenzen** — Facebook-Seite, Instagram-Account, LinkedIn-Profil. Die richtige Plattformauswahl hängt vom Starter-Typ ab. Für einen Beauty-Salon ist Instagram fast wichtiger als die eigene Website, für einen Steuerberater LinkedIn.

### Phase 2 — Content: „Interessant werden"
Regelmäßiger Content, damit die Website lebt:

- **Social-Media-Postings** — KI generiert Posting-Vorschläge aus Website-Inhalten (neue Produkte, Referenzprojekte, Galerie-Bilder). Der Kunde bestätigt, das System postet.
- **Pressemitteilungen** — Lokale Zeitungen, Stadtteil-Blogs und Branchen-Portale. KI generiert Texte, Presseverteiler-Plugin verwaltet Empfänger.
- **Google My Business Beiträge** — Regelmäßige Updates direkt in der Google-Suche.
- **Blog / News** — Langfristig stärkster SEO-Hebel. KI generiert Themenvorschläge und Entwürfe.

### Phase 3 — Reichweite: „Gefunden werden"
Bezahlte und organische Reichweiten-Steigerung:

- **Google Ads** — Lokale Suchbegriffe mit Kaufabsicht. Kampagnen-Vorlagen pro Starter-Typ.
- **Facebook/Instagram Ads** — Zielgruppen-basierte Kampagnen. Vorschläge aus dem System.
- **Facebook-Gruppen** — Lokale und branchenspezifische Gruppen. Kuratierte Listen mit Posting-Regeln.
- **Bewertungen** — Automatische Bewertungsanfragen nach Termin/Projekt.

### Phase 4 — Wachstum: „Kunden binden und ausbauen"
Langfristige Kundenbindung und Lead-Generierung:

- **Newsletter** — Regelmäßiger Versand, KI-generierte Inhalte.
- **Lead-Generierung** — Branchenabhängig: Projektanfragen, Mandatsanfragen, Händler-Akquise.
- **B2B-Datenanreicherung** — Recherchierte Kontakte ins CRM-Plugin bereitstellen.

---

## Technische Architektur

### Bestehende Plattform
- **Flask + SQLAlchemy + PostgreSQL** — Backend
- **DaisyUI + HTMX + Jinja2** — Frontend
- **Docker auf Coolify** — Deployment (jeder Kunde = eigener Container mit eigener DB)
- **Plugin-System** — Modulare Erweiterungen, registriert beim App-Start
- **Starter-System** — Branchenvorlagen mit TOML-Manifest, Seed-Daten, Templates
- **unternehmensdaten.org** — Zentrale API für Firmendaten, Branchen, Verzeichnisse

### Neue Komponenten für das Marketing-Cockpit

```
Ebene 0 — Fundamente (keine Abhängigkeiten untereinander)
├── Paket A: Hintergrund-Task-System (APScheduler + DB-Queue)
│   → Ermöglicht asynchrone Aufgaben: Newsletter versenden, APIs abrufen, Daten aggregieren
│
├── Paket B: Branchenklassifikation (WZ-2008 Codes + unternehmensdaten.org)
│   → Ermöglicht branchenspezifische Empfehlungen: Verzeichnisse, Gruppen, Plattformen
│
├── Paket C: AVV (Auftragsverarbeitungsvereinbarung)
│   → Rechtliche Grundlage für alle Marketing-Dienstleistungen im Kundenauftrag
│
└── Paket D: Eingebaute Traffic-Analyse (Flask-Middleware)
    → Sofortige Besucherdaten ohne externe Dienste, DSGVO-konform

Ebene 1 — Schaltzentrale (braucht alle Pakete aus Ebene 0)
└── Paket E: Marketing-Cockpit — Die Schaltzentrale (braucht A + B + C + D)
    → Onboarding-Wizard, Dashboard, Checkliste, Dienstleistungs-Buchung, Marketing-Score
    → Definiert das Modul-Registry, in das sich F–I einklinken

Ebene 2 — Kanal-Integrationen (brauchen A + E, teilweise auch B und D)
├── Paket F: Google Search Console Integration (braucht A + D + E)
│   → OAuth-Verbindung, Suchleistungsdaten, Indexierungsstatus, Keyword-Tracking
│
├── Paket G: Google My Business Integration (braucht A + B + E)
│   → Profilverwaltung, Beiträge, Bewertungen, Fotos, Insights
│
├── Paket H: Facebook Integration (braucht A + B + E)
│   → Seitenverwaltung, Posting & Scheduling, KI-Content, Gruppen-Empfehlungen
│
└── Paket I: Branchenverzeichnis-Service (braucht A + B + E)
    → Verzeichnis-Tracking, NAP-Konsistenzprüfung, Drei-Stufen-Buchung
```

### Parallelisierungsplan

**Sprint 1** (parallel, keine Abhängigkeiten): A + B + C + D gleichzeitig
**Sprint 2** (sobald A + B + C + D fertig): E (Marketing-Cockpit als Schaltzentrale)
**Sprint 3** (parallel, sobald E fertig): F + G + H + I gleichzeitig

### Architekturentscheidungen

| Entscheidung | Gewählt | Begründung |
|---|---|---|
| **Hintergrund-Tasks** | APScheduler + PostgreSQL-Queue | Kein Redis/Celery nötig, läuft in bestehender Infrastruktur |
| **Karten** | Leaflet.js + OpenStreetMap | Kostenlos, DSGVO-konform, kein API-Key |
| **Traffic-Analyse** | Eigene Flask-Middleware | Kein Cookie-Banner nötig, keine externen Dienste |
| **Branchendaten** | unternehmensdaten.org als zentrale API | Einmal kuratieren, alle Kunden profitieren |
| **Social Media** | OAuth-basierte API-Integration | Standard-Pattern (wie Buffer, Hootsuite) |
| **KI-Texte** | OpenRouter API | Modell-unabhängig, flexibel |
| **PDF-Export** | WeasyPrint | Reines Python, kein externes Binary |

---

## Sicherheit & Datenschutz

### DSGVO-Konformität
- **AVV** (Auftragsverarbeitungsvereinbarung) muss vor jeder Marketing-Dienstleistung vorliegen
- **Traffic-Analyse** ohne Cookies, ohne Fingerprinting, IP anonymisiert
- **YouTube-Videos** per 2-Klick-Lösung (kein Tracking ohne Einwilligung)
- **Newsletter** mit Double-Opt-In (DSGVO-Pflicht)
- **Social-Media-Integration** über OAuth (Kunde erteilt explizit Zugriff)

### Zugangsdaten-Sicherheit
- Alle Tokens und Passwörter verschlüsselt in der Datenbank (AES-256)
- OAuth-Tokens statt Passwörter wo immer möglich
- Zugriffsprotokolle für jede Aktion im Kundenauftrag
- Kunde kann Zugriff jederzeit widerrufen

### Subunternehmer
Wenn startklar.cloud Dritte beauftragt (z.B. für manuelle Einrichtungen):
- Subunternehmer-Liste in der AVV
- Kunde wird bei Änderungen informiert (Widerspruchsrecht)
- Subunternehmer unterliegen denselben Datenschutzpflichten

---

## Zentrale Datenflüsse

### Website-Daten → Marketing-Kanäle
Die VRS-Datenbank enthält bereits alle relevanten Daten:
- **Öffnungszeiten-Plugin** → Google My Business (automatische Synchronisation)
- **Galerie-Plugin** → Google-Fotos, Social-Media-Postings (Bild-Material)
- **Impressum-Plugin** → Branchenverzeichnisse (NAP-Daten: Name, Address, Phone)
- **Newsletter-Plugin** → E-Mail-Marketing (Abonnenten, Versand)
- **Referenzprojekte/Testimonials** → Social-Media-Content (Posting-Vorschläge)
- **PIM/Shop-Plugins** → Produktneuheiten als Content-Quelle

### unternehmensdaten.org → Kundeninstanz
Die zentrale API liefert branchenspezifische Informationen:
- Welche Branchenverzeichnisse sind relevant?
- Welche Facebook-Gruppen passen zu Branche + Region?
- Welche Google-Kategorien sollen verwendet werden?

### startklar.cloud Backend → Kundeninstanz
Die zentrale Verwaltung steuert:
- Auftragsstatus (offen/in Bearbeitung/erledigt)
- Dienstleistungskatalog und Preise
- Subunternehmer-Zuweisung
- Abrechnungsdaten

---

## Marketing-Score

Im Dashboard sieht der Kunde einen berechneten Wert von 0–100:

| Bereich | Max. Punkte | Kriterien |
|---|---|---|
| Google-Präsenz | 20 | My Business vorhanden, verifiziert, aktuell |
| Social Media | 20 | Mind. 1 Plattform verbunden, regelmäßig aktiv |
| Branchenverzeichnisse | 15 | Mind. 5 relevante Einträge |
| SEO (Search Console) | 10 | Verbunden, Sitemap eingereicht, keine Fehler |
| Newsletter | 10 | Eingerichtet, mind. 1 Newsletter versendet |
| Traffic-Trend | 10 | Positiver Trend vs. Vormonat |
| Bewertungen | 15 | Mind. 5 Google-Bewertungen, Durchschnitt ≥ 4.0 |

Die Gewichtung kann Starter-spezifisch angepasst werden (z.B. für einen Online-Händler ist SEO wichtiger als Google My Business).

---

## Dateien in diesem Verzeichnis

```
marketing/
├── README.md                                       ← Dieses Dokument (Big Picture)
└── arbeitspakete/
    ├── paket-a-hintergrund-tasks.md                ← Ebene 0: APScheduler + DB-Queue
    ├── paket-b-branchenklassifikation.md           ← Ebene 0: WZ-2008 + unternehmensdaten.org
    ├── paket-c-avv.md                              ← Ebene 0: AVV + digitaler Abschluss
    ├── paket-d-traffic-analyse.md                  ← Ebene 0: Flask-Middleware Analytics
    ├── paket-e-marketing-cockpit.md                ← Ebene 1: Die Schaltzentrale (Dashboard, Onboarding, Checkliste)
    ├── paket-f-google-search-console.md            ← Ebene 2: Search Console OAuth + Suchleistung
    ├── paket-g-google-my-business.md               ← Ebene 2: Business Profile + Bewertungen
    ├── paket-h-facebook.md                         ← Ebene 2: Facebook Pages + KI-Content
    └── paket-i-branchenverzeichnis-service.md      ← Ebene 2: Verzeichnis-Tracking + NAP-Prüfung
```

---

## Für die implementierenden KIs

Wenn du eines der Arbeitspakete implementierst, lies zuerst DIESES Dokument, um den Gesamtkontext zu verstehen. Dann lies die spezifische Paket-Spezifikation in `arbeitspakete/`.

**Wichtige Grundregeln:**
1. **Plattformname:** startklar.cloud (nicht „Startler-Cloud")
2. **Architektur:** Flask + SQLAlchemy + PostgreSQL + DaisyUI + HTMX + Jinja2
3. **Deployment:** Docker-Container auf Coolify, jeder Kunde eigene Instanz + DB
4. **Plugin-Struktur:** `/plugins/{name}/` mit `__init__.py`, `models.py`, `routes.py`, `templates/`, `services/`
5. **Models:** Erben von `VRSBaseModel` (aus `app/models.py`)
6. **Soft-FK-Pattern:** Plugin-übergreifende Referenzen als Integer-IDs ohne harte Fremdschlüssel
7. **Kein Redis, kein Celery:** Alles innerhalb Flask + PostgreSQL lösen
8. **DSGVO:** Immer mitdenken — keine personenbezogenen Daten ohne Rechtsgrundlage
9. **Sprache:** Code-Kommentare Englisch oder Deutsch, UI-Texte immer Deutsch
10. **Admin-UI:** DaisyUI-Komponenten, HTMX für dynamisches Nachladen
