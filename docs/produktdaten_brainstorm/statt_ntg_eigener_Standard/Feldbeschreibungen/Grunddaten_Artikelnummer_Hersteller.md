# Feldbeschreibung: Artikelnummer_Hersteller

## Gruppierung
**Grunddaten**

## Feldname
`Artikelnummer_Hersteller`

## Datentyp
Text

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Die herstellereigene Artikelnummer zur eindeutigen Identifikation des Produkts im Sortiment des Herstellers. Diese Nummer wird vom Hersteller selbst vergeben und erscheint üblicherweise auf Verpackung, Katalog und in Bestellsystemen.

Bitte tragen Sie die Artikelnummer exakt so ein, wie sie offiziell vom Hersteller verwendet wird – inklusive eventueller Buchstaben, Bindestriche oder Punkte.

## Erlaubte Werte
- Alphanumerische Zeichen (A-Z, a-z, 0-9)
- Bindestriche (-)
- Punkte (.)
- Schrägstriche (/)
- Maximale Länge: 30 Zeichen

## Validierungsregeln
- Mindestens 1 Zeichen
- Maximal 30 Zeichen
- Keine Leerzeichen am Anfang oder Ende
- Keine Sonderzeichen außer: - . /
- Muss innerhalb eines Herstellers eindeutig sein

## Temporär erlaubte Werte
- Bei Neuheiten ohne finale Artikelnummer: vorläufige Nummer mit Suffix "_VORL" verwenden
- Beispiel: `39123_VORL`
- Pflicht-Rückmeldung an MHI, sobald finale Nummer feststeht

## Beispiele
| Wert | Status | Bemerkung |
|------|--------|-----------|
| `39123` | ✓ Korrekt | Rein numerisch (Märklin-Stil) |
| `BR193-001` | ✓ Korrekt | Alphanumerisch mit Bindestrich |
| `450043200` | ✓ Korrekt | Schuco-Stil |
| `LC-2025/A` | ✓ Korrekt | Mit Schrägstrich |
| `39 123` | ✗ Falsch | Leerzeichen nicht erlaubt |
| ` 39123` | ✗ Falsch | Führendes Leerzeichen |
| `Art.-Nr.: 39123` | ✗ Falsch | Keine Beschriftung, nur die Nummer |

## Werteliste
Keine – freies Feld mit Validierung

## Hinweis
Die Kombination aus `Hersteller` + `Artikelnummer_Hersteller` muss systemweit eindeutig sein. Duplikate werden abgelehnt.
