# Feldbeschreibung: Preisbindung_bis

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Preisbindung_bis`

## Datentyp
Datum

## Pflichtfeld
Nein (nur bei preisgebundenen Artikeln)

## Beschreibung für Datenlieferant
Das Datum, bis zu dem eine Preisbindung für den Artikel gilt. Nach diesem Datum kann der Händler den Preis frei gestalten.

Bei Büchern endet die Preisbindung üblicherweise 18 Monate nach Erscheinen.

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Muss nach `Preisbindung_ab` liegen
- Oder leer (wenn keine Preisbindung)

## Validierungsregeln
- Format: `TT.MM.JJJJ`
- Muss nach Preisbindung_ab liegen

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `30.06.2026` | ✓ Korrekt | Preisbindung endet 30. Juni 2026 |
| *(leer)* | ✓ Korrekt | Keine Preisbindung oder unbefristet |

## Hinweise
- Nur relevant, wenn `Preisbindung_ab` gesetzt ist
- Nach Ablauf der Preisbindung wird der Artikel "modernes Antiquariat"
- Für Modellbahnartikel in der Regel nicht relevant
