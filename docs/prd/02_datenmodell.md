# UDO API - Geodaten-Datenmodell

## Übersicht

Das Datenmodell bildet die deutsche Verwaltungshierarchie ab:

```
Land → Bundesland → Regierungsbezirk → Kreis → Ort → Ortsteil
```

## Design-Entscheidungen

### Primary Keys

- **UUID** als Primary Key für alle Tabellen
- Ermöglicht konfliktfreie Synchronisation zwischen Systemen
- Consumer können Daten lokal speichern ohne ID-Mapping

### Business Keys

- **AGS**: Amtlicher Gemeindeschlüssel (offizieller deutscher Standard)
- **Code**: Hierarchischer Code (z.B. `DE-BY-091-09162`)
- Der Code ist global eindeutig und enthält die Hierarchie

### Nullable Felder

- `regierungsbezirk_id` bei Kreisen ist nullable
- Nicht alle Bundesländer haben Regierungsbezirke

## Tabellen

### geo_land

Länder (oberste Ebene).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| ags | String(5) | ISO 3166-1 alpha-2 (z.B. "DE") |
| code | String(10) | Gleich wie AGS für Länder |
| name | String(255) | Deutscher Name |
| name_eng | String(255) | Englischer Name |
| name_fra | String(255) | Französischer Name |
| iso3 | String(3) | ISO 3166-1 alpha-3 (z.B. "DEU") |
| kontinent | String(100) | Kontinent |
| ist_eu | Boolean | EU-Mitglied |
| landesvorwahl | String(20) | Telefonvorwahl |
| legacy_id | String(10) | Original-ID aus Legacy-DB |

### geo_bundesland

Bundesländer / Kantone / Regionen.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| ags | String(10) | Bundesland-Code (z.B. "09") |
| code | String(20) | Hierarchisch (z.B. "DE-BY") |
| kuerzel | String(10) | Kürzel (z.B. "BY", "NW") |
| name | String(255) | Name |
| einwohner | Integer | Einwohnerzahl |
| einwohner_stand | DateTime | Stand der Einwohnerzahl |
| land_id | UUID | FK → geo_land |
| legacy_id | Integer | Original-ID aus Legacy-DB |

### geo_regierungsbezirk

Regierungsbezirke (optional, nicht in allen Ländern).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| ags | String(10) | Bezirks-Code (z.B. "091") |
| code | String(30) | Hierarchisch (z.B. "DE-BY-091") |
| name | String(255) | Name |
| bundesland_id | UUID | FK → geo_bundesland |
| legacy_id | Integer | Original-ID aus Legacy-DB |

### geo_kreis

Landkreise und kreisfreie Städte.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| ags | String(20) | Kreisschlüssel (z.B. "09162") |
| code | String(60) | Hierarchisch mit Legacy-ID |
| name | String(255) | Name |
| typ | String(50) | "Landkreis", "Kreisfreie Stadt" |
| ist_landkreis | Boolean | Flag |
| ist_kreisfreie_stadt | Boolean | Flag |
| autokennzeichen | String(10) | KFZ-Kennzeichen |
| kreissitz | String(100) | Verwaltungssitz |
| einwohner | Integer | Einwohnerzahl |
| flaeche_km2 | Integer | Fläche in km² |
| beschreibung | Text | Beschreibungstext |
| wikipedia_url | String(255) | Wikipedia-Link |
| website_url | String(255) | Offizielle Website |
| bundesland_id | UUID | FK → geo_bundesland |
| regierungsbezirk_id | UUID | FK → geo_regierungsbezirk (nullable) |
| legacy_id | Integer | Original-ID aus Legacy-DB |

### geo_ort

Städte und Gemeinden.

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| ags | String(12) | Gemeindeschlüssel |
| code | String(60) | Hierarchisch mit PLZ und Legacy-ID |
| name | String(255) | Name |
| plz | String(10) | Haupt-Postleitzahl |
| typ | String(50) | "Stadt", "Gemeinde" |
| ist_stadt | Boolean | Flag |
| ist_gemeinde | Boolean | Flag |
| ist_hauptort | Boolean | Hauptort für PLZ |
| lat | Float | Breitengrad |
| lng | Float | Längengrad |
| einwohner | Integer | Einwohnerzahl |
| flaeche_km2 | Float | Fläche in km² |
| beschreibung | Text | Beschreibungstext |
| wikipedia_url | String(255) | Wikipedia-Link |
| website_url | String(255) | Offizielle Website |
| kreis_id | UUID | FK → geo_kreis |
| legacy_id | Integer | Original-ID aus Legacy-DB |

### geo_ortsteil

Ortsteile (unterste Ebene).

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | UUID | Primary Key |
| ags | String(20) | Code (falls vorhanden) |
| code | String(80) | Hierarchisch |
| name | String(255) | Name |
| lat | Float | Breitengrad |
| lng | Float | Längengrad |
| einwohner | Integer | Einwohnerzahl |
| beschreibung | Text | Beschreibungstext |
| ort_id | UUID | FK → geo_ort |
| legacy_id | Integer | Original-ID aus Legacy-DB |

## Indizes

Alle Tabellen haben Indizes auf:
- `code` (unique)
- `ags`
- Foreign Keys

Zusätzlich:
- `geo_ort.plz`
- `geo_ort.name`
- `geo_kreis.autokennzeichen`

## Beziehungen

```
geo_land (1) ─────< (n) geo_bundesland
geo_bundesland (1) ─────< (n) geo_regierungsbezirk
geo_bundesland (1) ─────< (n) geo_kreis
geo_regierungsbezirk (1) ─────< (n) geo_kreis (optional)
geo_kreis (1) ─────< (n) geo_ort
geo_ort (1) ─────< (n) geo_ortsteil
```

## Datenmenge (Stand Migration)

| Tabelle | Anzahl |
|---------|--------|
| geo_land | 238 |
| geo_bundesland | 101 |
| geo_regierungsbezirk | 0 |
| geo_kreis | 5.370 |
| geo_ort | 56.965 |
| geo_ortsteil | 148 |
