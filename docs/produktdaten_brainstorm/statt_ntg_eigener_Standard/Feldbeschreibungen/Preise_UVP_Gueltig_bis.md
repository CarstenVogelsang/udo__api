# Feldbeschreibung: UVP_Gueltig_bis

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`UVP_Gueltig_bis`

## Datentyp
Datum

## Pflichtfeld
Nein

## Beschreibung für Datenlieferant
Das Datum, bis zu dem die angegebene UVP gültig ist. Dieses Feld wird verwendet, wenn eine Preisänderung zu einem bestimmten Datum geplant ist.

Nach diesem Datum muss eine aktualisierte Stammdatei mit der neuen UVP übermittelt werden.

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein
- Muss nach `UVP_Gueltig_ab` liegen (falls angegeben)

## Validierungsregeln
- Format: `TT.MM.JJJJ` (z.B. 31.12.2025)
- Muss nach UVP_Gueltig_ab liegen
- Punkt als Trennzeichen

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `31.12.2025` | ✓ Korrekt | Gültig bis 31. Dezember 2025 |
| *(leer)* | ✓ Korrekt | Unbefristet gültig |
| `01.01.2024` | ✗ Prüfen | Liegt in der Vergangenheit |

## Hinweise
- Bei leerem Feld gilt die UVP unbefristet
- Bei geplanten Preiserhöhungen bitte rechtzeitig neue Stammdaten übermitteln
- Befristete UVP sind selten – meist bei Aktionspreisen oder Einführungsangeboten
