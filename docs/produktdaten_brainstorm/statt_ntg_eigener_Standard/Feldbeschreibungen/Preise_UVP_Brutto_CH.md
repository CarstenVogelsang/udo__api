# Feldbeschreibung: UVP_Brutto_CH

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`UVP_Brutto_CH`

## Datentyp
Dezimalzahl (2 Nachkommastellen)

## Pflichtfeld
Nein (optional)

## Beschreibung für Datenlieferant
Die unverbindliche Preisempfehlung (UVP) des Herstellers für den Schweizer Markt, inklusive Mehrwertsteuer in Schweizer Franken (CHF).

Falls kein separater Schweiz-Preis existiert, kann das Feld leer bleiben.

## Erlaubte Werte
- Positive Dezimalzahl
- Format: `0.00` (Punkt als Dezimaltrennzeichen)
- **Währung: CHF** (nicht EUR!)
- Leer = kein separater CH-Preis

## Validierungsregeln
- Nur numerische Werte
- Punkt als Dezimaltrennzeichen
- Genau 2 Nachkommastellen
- Keine Währungssymbole

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `429.00` | ✓ Korrekt | 429,00 CHF |
| *(leer)* | ✓ Korrekt | Kein CH-Preis hinterlegt |
| `429,00` | ✗ Falsch | Komma statt Punkt |
| `CHF 429.00` | ✗ Falsch | Währungssymbol |

## Hinweise
- **Achtung:** Währung ist CHF, nicht EUR!
- Der Schweizer MwSt-Satz beträgt regulär 8.1% (deutlich niedriger als DE/AT)
- Bei Preisumrechnungen bitte aktuellen Wechselkurs beachten
