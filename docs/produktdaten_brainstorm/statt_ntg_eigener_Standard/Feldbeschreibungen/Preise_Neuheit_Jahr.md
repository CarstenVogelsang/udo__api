# Feldbeschreibung: Neuheit_Jahr

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Neuheit_Jahr`

## Datentyp
Zahl (4-stellig)

## Pflichtfeld
Nein (empfohlen bei Neuheiten)

## Beschreibung für Datenlieferant
Das Jahr, in dem der Artikel als Neuheit erscheint oder erschienen ist. Diese Information wird für Kataloge, Neuheiten-Listen und Marketing verwendet.

Ein Artikel gilt als "Neuheit", wenn dieses Feld ausgefüllt ist und das Jahr dem aktuellen oder kommenden Jahr entspricht.

## Erlaubte Werte
- Vierstellige Jahreszahl
- Format: `JJJJ` (z.B. 2025)

## Validierungsregeln
- Genau 4 Ziffern
- Gültiger Jahresbereich: 2000-2099
- Keine Zusätze oder Formatierungen

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `2025` | ✓ Korrekt | Neuheit 2025 |
| `2024` | ✓ Korrekt | Neuheit 2024 |
| `25` | ✗ Falsch | Nicht vierstellig |
| `2025/2026` | ✗ Falsch | Keine Bereiche |
| *(leer)* | ✓ Korrekt | Keine Neuheit / Bestandsartikel |

## Hinweise
- Ein ausgefülltes Neuheit_Jahr ersetzt das frühere J/N-Feld "Ist Neuheit"
- Die Kombination mit Artikelstatus "Neuheit" ist empfohlen
- Nach Ablauf des Neuheiten-Zeitraums: Feld kann bestehen bleiben (historische Info)

## Zusammenspiel mit anderen Feldern
| Wenn | Dann |
|------|------|
| Neuheit_Jahr = aktuelles Jahr | Artikel erscheint in "Neuheiten"-Kategorie |
| Neuheit_Jahr = leer | Artikel ist kein Neuheiten-Artikel |
| Neuheit_Jahr + Anzeige_ab | Koordinierter Neuheiten-Launch |
