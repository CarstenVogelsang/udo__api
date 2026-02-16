# Feldbeschreibung: Ursprungsland

## Gruppierung
**Grunddaten**

## Feldname
`Ursprungsland`

## Datentyp
Text (aus Werteliste)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Das Herstellungsland des Produkts – also das Land, in dem der Artikel produziert wurde. Diese Angabe entspricht dem "Made in..." auf der Verpackung und ist für Zollzwecke sowie die Verbraucherinformation relevant.

Bitte geben Sie das Land an, in dem die wesentliche Herstellung/Montage stattgefunden hat. Bei Produkten mit Komponenten aus verschiedenen Ländern gilt das Land der Endmontage.

## Erlaubte Werte
**Nur Werte aus der Werteliste (deutsche Ländernamen)!**

## Werteliste
📎 **Siehe:** `Wertelisten/Werteliste_Grunddaten_Laender.xlsx`

Die Werteliste enthält:
- **Key**: ISO Alpha-2 Ländercode (Surrogate Key)
- **Land_DE**: Deutscher Ländername (diesen Wert verwenden!)
- **Land_EN**: Englischer Ländername
- **ISO_Alpha2**: ISO 3166-1 Alpha-2 Code
- **Region**: Geographische Region

## Validierungsregeln
- Wert muss exakt aus der Werteliste stammen (Spalte `Land_DE`)
- Deutsche Ländernamen verwenden (nicht "Germany" sondern "Deutschland")
- Keine ISO-Codes (nicht "DE" sondern "Deutschland")
- Keine Abkürzungen (nicht "D" statt "Deutschland")

## Temporär erlaubte Werte
- Bei unbekanntem Ursprungsland: Leer lassen und Rückmeldung an MHI
- Temporärer Wert "Unbekannt" nur in Ausnahmefällen und mit Begründung

## Beispiele
| Wert | Status | Bemerkung |
|------|--------|-----------|
| `Deutschland` | ✓ Korrekt | |
| `Ungarn` | ✓ Korrekt | |
| `China` | ✓ Korrekt | |
| `Germany` | ✗ Falsch | Englisch nicht erlaubt |
| `DE` | ✗ Falsch | ISO-Code nicht erlaubt |
| `D` | ✗ Falsch | Abkürzung nicht erlaubt |
| `Made in China` | ✗ Falsch | Nur Ländername |
| `Volksrepublik China` | ✗ Falsch | Kurzform "China" verwenden |

## Rechtlicher Hinweis
Die Angabe des Ursprungslandes ist gesetzlich vorgeschrieben für:
- Zollanmeldungen (Import/Export)
- Verbraucherinformation
- "Made in"-Kennzeichnung auf der Verpackung

Falsche Angaben können zu Zollproblemen und rechtlichen Konsequenzen führen.

## Besonderheiten
| Fall | Lösung |
|------|--------|
| Komponenten aus verschiedenen Ländern | Land der Endmontage angeben |
| Entwicklung in Land A, Produktion in Land B | Land B (Produktion) angeben |
| Umverpackung in anderem Land | Ursprüngliches Produktionsland angeben |
