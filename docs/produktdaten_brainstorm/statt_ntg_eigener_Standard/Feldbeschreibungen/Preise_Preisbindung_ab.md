# Feldbeschreibung: Preisbindung_ab

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Preisbindung_ab`

## Datentyp
Datum

## Pflichtfeld
Nein (nur bei preisgebundenen Artikeln)

## Beschreibung für Datenlieferant
Das Datum, ab dem eine Preisbindung für den Artikel gilt. Preisbindung bedeutet, dass der Händler den Artikel nicht unter dem UVP verkaufen darf.

Preisbindung ist in Deutschland nur für Bücher und Zeitschriften (Buchpreisbindung) sowie für bestimmte Sondervereinbarungen zulässig.

**Hinweis:** Für die meisten Modellbahnartikel gibt es KEINE Preisbindung!

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Oder leer (keine Preisbindung)

## Validierungsregeln
- Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `01.01.2025` | ✓ Korrekt | Preisbindung ab 1. Januar 2025 |
| *(leer)* | ✓ Korrekt | Keine Preisbindung (Normalfall) |

## Hinweise
- Preisbindung ist in Deutschland stark reguliert (GWB §§ 1-3)
- Für Spielwaren/Modellbahnen ist Preisbindung grundsätzlich NICHT zulässig
- UVP ist immer nur eine unverbindliche EMPFEHLUNG
- Dieses Feld ist primär für Verlagsprodukte (Bücher, Kataloge) relevant
