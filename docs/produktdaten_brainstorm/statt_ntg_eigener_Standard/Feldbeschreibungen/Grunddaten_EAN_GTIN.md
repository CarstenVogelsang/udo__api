# Feldbeschreibung: EAN_GTIN

## Gruppierung
**Grunddaten**

## Feldname
`EAN_GTIN`

## Datentyp
Text (nicht Zahl, wegen führender Nullen!)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Die European Article Number (EAN) bzw. Global Trade Item Number (GTIN) ist die weltweit eindeutige Produktidentifikation. Bitte tragen Sie die vollständige 13-stellige EAN-13 oder 14-stellige GTIN-14 ein. Bei 8-stelligen EAN-8 Codes bitte mit führenden Nullen auf 13 Stellen auffüllen.

Die EAN/GTIN muss beim Hersteller registriert sein (GS1). Jeder Artikel mit unterschiedlicher Ausstattung, Farbe oder Verpackung benötigt eine eigene EAN.

## Erlaubte Werte
| Format | Stellen | Verwendung |
|--------|---------|------------|
| EAN-13 | 13 Ziffern | Standardfall für Einzelartikel |
| GTIN-14 | 14 Ziffern | Für Umverpackungen/Gebinde |
| EAN-8 | 8 Ziffern | Nur bei Kleinstartikeln (selten) |

## Validierungsregeln
- Nur Ziffern 0-9 erlaubt
- Keine Leerzeichen
- Keine Bindestriche oder Trennzeichen
- Prüfziffer (letzte Stelle) muss mathematisch korrekt sein
- Länge: exakt 8, 13 oder 14 Stellen

## Prüfziffernberechnung
Die letzte Ziffer ist eine Prüfziffer. Sie wird berechnet aus den vorherigen Ziffern nach dem GS1-Algorithmus. Falsche Prüfziffern führen zur Ablehnung des Datensatzes.

## Temporär erlaubte Werte
- Leeres Feld nur bei Neuheiten, deren EAN noch nicht vergeben wurde
- In diesem Fall: Pflicht-Rückmeldung an MHI mit voraussichtlichem Datum der EAN-Vergabe
- Platzhalter wie "folgt", "TBD" oder "000000000000" sind NICHT erlaubt

## Beispiele
| Wert | Status | Bemerkung |
|------|--------|-----------|
| `4001883391234` | ✓ Korrekt | Standard EAN-13 |
| `4001883391235` | ✗ Falsch | Prüfziffer ungültig |
| `4 001883 391234` | ✗ Falsch | Leerzeichen nicht erlaubt |
| `4001883-391234` | ✗ Falsch | Bindestriche nicht erlaubt |
| `00040018833912` | ✓ Korrekt | GTIN-14 mit führenden Nullen |

## Werteliste
Keine – freies Feld mit Validierung
