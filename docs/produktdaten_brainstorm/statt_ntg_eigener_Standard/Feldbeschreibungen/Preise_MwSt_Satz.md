# Feldbeschreibung: MwSt_Satz

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`MwSt_Satz`

## Datentyp
Dezimalzahl (1 Nachkommastelle)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Der gültige Mehrwertsteuersatz für das Produkt in Deutschland in Prozent. Der Regelsteuersatz beträgt 19%, der ermäßigte Satz 7%.

Für Spielwaren und Modellbahnartikel gilt in der Regel der volle Steuersatz von 19%.

## Erlaubte Werte
| Wert | Beschreibung |
|------|--------------|
| `19.0` | Regelsteuersatz (Standard für Spielwaren) |
| `7.0` | Ermäßigter Steuersatz (z.B. Bücher, bestimmte Lebensmittel) |
| `0.0` | Steuerbefreit (z.B. Exporte, innergemeinschaftliche Lieferungen) |

## Validierungsregeln
- Nur die Werte 19.0, 7.0 oder 0.0 erlaubt
- Punkt als Dezimaltrennzeichen
- Keine Prozentzeichen (nicht "19%" sondern "19.0")

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `19.0` | ✓ Korrekt | 19% MwSt |
| `19` | ✓ Korrekt | Wird zu 19.0 |
| `7.0` | ✓ Korrekt | 7% MwSt |
| `19%` | ✗ Falsch | Kein Prozentzeichen |
| `19,0` | ✗ Falsch | Komma statt Punkt |
| `20.0` | ✗ Falsch | Kein gültiger DE-Steuersatz |

## Hinweise
- Für Modelleisenbahnen und Sammlermodelle gilt fast immer 19%
- Der ermäßigte Satz (7%) gilt nur für bestimmte Warengruppen (Bücher, Zeitschriften)
- Bei Exporten kann 0% gelten – bitte Steuerberater konsultieren
