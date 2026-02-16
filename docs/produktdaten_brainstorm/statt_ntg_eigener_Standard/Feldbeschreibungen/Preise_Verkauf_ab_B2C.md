# Feldbeschreibung: Verkauf_ab_B2C

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Verkauf_ab_B2C`

## Datentyp
Datum

## Pflichtfeld
Nein (Pflicht bei Neuheiten mit Sperrfrist)

## Beschreibung für Datenlieferant
Das **Street Date** – also das Datum, ab dem der Artikel an Endkunden verkauft werden darf. Vor diesem Datum darf kein Händler den Artikel an Privatpersonen verkaufen, auch wenn die Ware bereits im Lager ist.

Bei Neuheiten mit koordiniertem Marktstart ist dieses Datum verbindlich einzuhalten.

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein

## Validierungsregeln
- Format: `TT.MM.JJJJ`
- Sollte nach oder gleich `Erstlieferdatum` sein
- Sollte nach oder gleich `Anzeige_ab` sein

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `15.03.2025` | ✓ Korrekt | Verkauf an Endkunden ab 15. März 2025 |
| *(leer)* | ✓ Korrekt | Keine Sperrfrist, sofort verkaufbar |

## Wichtig: Street Date einhalten!
Bei Neuheiten mit Street Date gilt:
- Kein Verkauf vor dem Datum
- Kein Versand, der vor dem Datum ankommt
- Keine Abholung vor dem Datum

Verstöße gegen Street Dates können zu Sanktionen durch den Hersteller führen.

## Abgrenzung zu Anzeige_ab
| Feld | Bedeutung |
|------|-----------|
| `Anzeige_ab` | Artikel darf im Shop **angezeigt** werden |
| `Verkauf_ab_B2C` | Artikel darf **verkauft** werden |

Oft gilt: Anzeige_ab liegt vor Verkauf_ab_B2C → Kunden sehen den Artikel, können aber noch nicht kaufen (Vorbestellung möglich).
