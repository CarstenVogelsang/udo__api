# Feldbeschreibung: UVP_Gueltig_ab

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`UVP_Gueltig_ab`

## Datentyp
Datum

## Pflichtfeld
Nein (empfohlen bei Preisänderungen)

## Beschreibung für Datenlieferant
Das Datum, ab dem die angegebene UVP gültig ist. Dieses Feld ist besonders wichtig bei Preisänderungen, um den Zeitpunkt der Gültigkeit zu dokumentieren.

Bei Neuheiten ist dies typischerweise das Erscheinungsdatum oder der Beginn der Auslieferung.

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein
- Kann in der Vergangenheit oder Zukunft liegen

## Validierungsregeln
- Format: `TT.MM.JJJJ` (z.B. 01.03.2025)
- Tag: 01-31 (abhängig vom Monat)
- Monat: 01-12
- Jahr: vierstellig
- Punkt als Trennzeichen

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `01.03.2025` | ✓ Korrekt | 1. März 2025 |
| `15.11.2024` | ✓ Korrekt | 15. November 2024 |
| `2025-03-01` | ✗ Falsch | Falsches Format (ISO) |
| `1.3.2025` | ✗ Falsch | Tag/Monat ohne führende Null |
| `01.03.25` | ✗ Falsch | Jahr nicht vierstellig |
| *(leer)* | ✓ Korrekt | Sofort gültig |

## Hinweise
- Bei leerem Feld gilt die UVP ab sofort / ohne zeitliche Einschränkung
- Bei zukünftigen Preisänderungen bitte rechtzeitig übermitteln
- Siehe auch `UVP_Gueltig_bis` für befristete Preise
