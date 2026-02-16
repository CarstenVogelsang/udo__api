# Feldbeschreibung: UVP_Brutto_EUR

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`UVP_Brutto_EUR`

## Datentyp
Dezimalzahl (2 Nachkommastellen)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Die unverbindliche Preisempfehlung (UVP) des Herstellers für den deutschen Markt, inklusive Mehrwertsteuer (Bruttopreis). Dieser Preis dient als Orientierung für Händler und wird oft in Katalogen und Online-Shops angezeigt.

Bitte geben Sie den Preis in Euro mit zwei Nachkommastellen an.

## Erlaubte Werte
- Positive Dezimalzahl
- Format: `0.00` (Punkt als Dezimaltrennzeichen)
- Mindestens: 0.01
- Maximal: 99999.99

## Validierungsregeln
- Nur numerische Werte
- Punkt als Dezimaltrennzeichen (nicht Komma)
- Genau 2 Nachkommastellen
- Keine Währungssymbole (nicht "€" oder "EUR")
- Keine Tausendertrennzeichen

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `389.99` | ✓ Korrekt | 389,99 € |
| `389,99` | ✗ Falsch | Komma statt Punkt |
| `389.9` | ✗ Falsch | Nur 1 Nachkommastelle |
| `€ 389.99` | ✗ Falsch | Währungssymbol |
| `1.299.99` | ✗ Falsch | Tausendertrennzeichen |
| `1299.99` | ✓ Korrekt | 1.299,99 € |

## Hinweise
- Die UVP ist unverbindlich – Händler können abweichende Preise verlangen
- Bei preisgebundenen Artikeln (z.B. Bücher) siehe Feld `Preisbindung_ab`
- Für Österreich und Schweiz siehe separate Felder `UVP_Brutto_AT` und `UVP_Brutto_CH`
