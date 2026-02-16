# Feldbeschreibung: Erstlieferdatum

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Erstlieferdatum`

## Datentyp
Datum

## Pflichtfeld
Nein (empfohlen bei Neuheiten)

## Beschreibung für Datenlieferant
Das Datum der ersten Auslieferung des Artikels vom Hersteller an die Händler. Dies ist der Tag, an dem die Ware erstmals das Lager verlässt.

Bei Neuheiten ist dies ein wichtiges Datum für die Logistikplanung der Händler.

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Kann in der Vergangenheit liegen (bei bereits gelieferten Artikeln)
- Kann in der Zukunft liegen (bei Neuheiten)

## Validierungsregeln
- Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein
- Sollte vor oder gleich `Verkauf_ab_B2C` sein

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `15.03.2025` | ✓ Korrekt | Erste Auslieferung 15. März 2025 |
| `01.2025` | ✗ Falsch | Nur Monat/Jahr, Tag fehlt |
| `Q1/2025` | ✗ Falsch | Quartal nicht erlaubt |
| *(leer)* | ✓ Korrekt | Kein Erstlieferdatum bekannt |

## Hinweise
- Bei Neuheiten kann das Datum zunächst geschätzt sein
- Bitte bei Verschiebungen zeitnah aktualisierte Daten übermitteln
- Das Erstlieferdatum ist NICHT das Street Date (siehe `Verkauf_ab_B2C`)

## Abgrenzung zu anderen Datumsfeldern
| Feld | Bedeutung |
|------|-----------|
| `Erstlieferdatum` | Wann liefert der Hersteller an Händler |
| `Verkauf_ab_B2B` | Ab wann dürfen Händler bestellen |
| `Verkauf_ab_B2C` | Ab wann darf an Endkunden verkauft werden (Street Date) |
| `Anzeige_ab` | Ab wann darf der Artikel im Shop gezeigt werden |
