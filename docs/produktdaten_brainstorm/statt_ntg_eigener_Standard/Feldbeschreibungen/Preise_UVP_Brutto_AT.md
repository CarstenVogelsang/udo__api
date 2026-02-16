# Feldbeschreibung: UVP_Brutto_AT

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`UVP_Brutto_AT`

## Datentyp
Dezimalzahl (2 Nachkommastellen)

## Pflichtfeld
Nein (optional)

## Beschreibung für Datenlieferant
Die unverbindliche Preisempfehlung (UVP) des Herstellers für den österreichischen Markt, inklusive Mehrwertsteuer (Bruttopreis) in Euro.

Falls kein separater Österreich-Preis existiert, kann das Feld leer bleiben – es wird dann der deutsche UVP verwendet.

## Erlaubte Werte
- Positive Dezimalzahl
- Format: `0.00` (Punkt als Dezimaltrennzeichen)
- Leer = kein separater AT-Preis

## Validierungsregeln
- Nur numerische Werte
- Punkt als Dezimaltrennzeichen
- Genau 2 Nachkommastellen
- Keine Währungssymbole

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `389.99` | ✓ Korrekt | 389,99 € (AT) |
| *(leer)* | ✓ Korrekt | Verwendet UVP_Brutto_EUR |
| `389,99` | ✗ Falsch | Komma statt Punkt |

## Hinweise
- Der österreichische MwSt-Satz beträgt regulär 20% (statt 19% in DE)
- Der UVP kann daher vom deutschen Preis abweichen
