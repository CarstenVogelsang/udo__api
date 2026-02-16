# Feldbeschreibung: Verkauf_ab_B2B

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Verkauf_ab_B2B`

## Datentyp
Datum

## Pflichtfeld
Nein

## Beschreibung für Datenlieferant
Das Datum, ab dem Händler den Artikel beim Hersteller/Großhandel bestellen können. Dies ist das Freigabedatum für B2B-Bestellungen.

Bei Neuheiten liegt dieses Datum oft vor dem Street Date, damit Händler rechtzeitig Ware bevorraten können.

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Kann vor `Verkauf_ab_B2C` liegen

## Validierungsregeln
- Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `01.02.2025` | ✓ Korrekt | B2B-Bestellung ab 1. Februar 2025 |
| *(leer)* | ✓ Korrekt | Sofort bestellbar / keine Einschränkung |

## Typischer Ablauf bei Neuheiten
```
1. Ankündigung           → Artikel wird angekündigt
2. Verkauf_ab_B2B        → Händler können vorbestellen
3. Erstlieferdatum       → Ware wird ausgeliefert
4. Anzeige_ab            → Artikel darf im Shop gezeigt werden
5. Verkauf_ab_B2C        → Verkauf an Endkunden (Street Date)
```

## Hinweise
- Ermöglicht Händlern, Ware vor dem offiziellen Verkaufsstart zu ordern
- Bei leerem Feld gilt keine B2B-Sperrfrist
