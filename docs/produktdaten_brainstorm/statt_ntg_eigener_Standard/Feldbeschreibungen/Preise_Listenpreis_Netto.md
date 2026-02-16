# Feldbeschreibung: Listenpreis_Netto

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Listenpreis_Netto`

## Datentyp
Dezimalzahl (2 Nachkommastellen)

## Pflichtfeld
Nein (B2B-relevant)

## Beschreibung für Datenlieferant
Der Listenpreis (Händler-Einkaufspreis) ohne Mehrwertsteuer in Euro. Dies ist der Basispreis für B2B-Geschäfte, von dem ggf. Rabatte abgezogen werden.

Dieses Feld ist primär für die B2B-Kommunikation relevant und wird nicht an Endkunden kommuniziert.

## Erlaubte Werte
- Positive Dezimalzahl
- Format: `0.00` (Punkt als Dezimaltrennzeichen)
- Netto = ohne Mehrwertsteuer

## Validierungsregeln
- Nur numerische Werte
- Punkt als Dezimaltrennzeichen
- Genau 2 Nachkommastellen
- Keine Währungssymbole
- Muss niedriger sein als UVP_Brutto_EUR (nach Abzug MwSt)

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `220.00` | ✓ Korrekt | 220,00 € netto |
| `220,00` | ✗ Falsch | Komma statt Punkt |
| *(leer)* | ✓ Korrekt | Kein Listenpreis angegeben |

## Hinweise
- Dieser Preis ist vertraulich und nur für B2B-Partner bestimmt
- Von diesem Preis können Staffelrabatte oder Sonderkonditionen abgezogen werden
- Die Handelsspanne ergibt sich aus: UVP (netto) - Listenpreis (netto)
