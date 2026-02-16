# Feldbeschreibung: Anzeige_ab

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Anzeige_ab`

## Datentyp
Datum

## Pflichtfeld
Nein (empfohlen bei Neuheiten mit Sperrfrist)

## Beschreibung für Datenlieferant
Das Datum, ab dem der Artikel in Online-Shops und Katalogen öffentlich angezeigt werden darf. Vor diesem Datum sollte der Artikel nicht sichtbar sein – auch nicht als "Coming Soon" oder "Vorbestellung".

Bei Neuheiten mit koordiniertem Marktstart steuert dieses Datum die Veröffentlichung.

## Erlaubte Werte
- Datum im Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein
- Sollte vor oder gleich `Verkauf_ab_B2C` sein

## Validierungsregeln
- Format: `TT.MM.JJJJ`
- Muss ein gültiges Datum sein

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `01.03.2025` | ✓ Korrekt | Anzeige ab 1. März 2025 |
| *(leer)* | ✓ Korrekt | Keine Sperrfrist, sofort anzeigbar |

## Typisches Szenario
```
Anzeige_ab:      01.03.2025  → Artikel erscheint im Shop
Verkauf_ab_B2C:  15.03.2025  → "Kaufen"-Button wird aktiv

Zwischen 01.03. und 15.03.:
- Artikel ist sichtbar
- Preis ist sichtbar
- "Vorbestellung möglich" oder "Bald verfügbar"
- Kein Kauf/Versand möglich
```

## Hinweise
- Ermöglicht Marketing-Vorlauf vor dem eigentlichen Verkaufsstart
- Bei leerem Feld gilt keine Anzeige-Sperrfrist
- Verstöße gegen Anzeige-Sperrfristen können zu Sanktionen führen
