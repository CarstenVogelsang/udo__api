# Feldbeschreibung: Zolltarifnummer

## Gruppierung
**Grunddaten**

## Feldname
`Zolltarifnummer`

## Datentyp
Text (8-11 Ziffern)

## Pflichtfeld
Ja (für Importe aus Nicht-EU-Ländern)

## Beschreibung für Datenlieferant
Die Zolltarifnummer (auch: HS-Code, Warennummer, TARIC-Code) ist eine international standardisierte Klassifikation für Waren im internationalen Handel. Sie wird für Zollanmeldungen, Importstatistiken und die Berechnung von Zöllen benötigt.

Bitte geben Sie mindestens die 8-stellige kombinierte Nomenklatur (KN) an. Für EU-Importe ist die 10-stellige TARIC-Nummer empfohlen.

## Erlaubte Werte
| Format | Stellen | Verwendung |
|--------|---------|------------|
| HS-Code | 6 Ziffern | International (Basis) |
| KN-Code | 8 Ziffern | EU-Standard (empfohlen) |
| TARIC | 10 Ziffern | EU-Import (vollständig) |
| National | 11 Ziffern | Nationale Erweiterungen |

## Relevante Zolltarifnummern für die Branche
| Code | Beschreibung |
|------|--------------|
| `9503 00 10` | Elektrische Eisenbahnen, einschl. Gleise, Signale und anderes Zubehör |
| `9503 00 30` | Andere maßstabgetreue Modelle zum Zusammenbauen |
| `9503 00 35` | Andere Bausätze und Konstruktionsspielzeug aus Kunststoff |
| `9503 00 41` | Spielzeug, das Tiere oder andere Wesen darstellt, gefüllt |
| `9503 00 49` | Spielzeug, das Tiere oder andere Wesen darstellt, andere |
| `9503 00 55` | Modelle aus Metall, zum Spielen |
| `9503 00 70` | Anderes Spielzeug, in Aufmachungen |
| `9503 00 75` | Anderes Spielzeug aus Kunststoff |
| `9503 00 79` | Anderes Spielzeug aus anderen Stoffen |
| `9503 00 81` | Spielzeug mit Motor |
| `9504 90 80` | Andere Gesellschaftsspiele |

## Validierungsregeln
- Nur Ziffern 0-9
- Mindestens 6 Stellen, maximal 11 Stellen
- Keine Leerzeichen oder Trennzeichen (werden intern formatiert)
- Muss einer gültigen Warengruppe entsprechen

## Temporär erlaubte Werte
- Bei unbekannter Zolltarifnummer: Leer lassen
- Meldung an MHI zur Klärung
- Für Zollabwicklung ist die Nummer zwingend erforderlich

## Beispiele
| Wert | Status | Bemerkung |
|------|--------|-----------|
| `95030010` | ✓ Korrekt | 8-stellig, Elektrische Eisenbahn |
| `9503001000` | ✓ Korrekt | 10-stellig, TARIC |
| `9503 00 10` | ✗ Falsch | Leerzeichen nicht erlaubt |
| `9503.00.10` | ✗ Falsch | Punkte nicht erlaubt |
| `950300` | ✗ Falsch | Nur 6 Stellen (zu kurz für EU) |
| `123456789012` | ✗ Falsch | Zu viele Stellen |

## Zuordnungshilfe

### Modelleisenbahn
| Produkttyp | Empfohlener Code |
|------------|------------------|
| Lokomotiven (elektrisch) | 9503 00 10 |
| Waggons | 9503 00 10 |
| Gleise | 9503 00 10 |
| Zubehör (Signale, etc.) | 9503 00 10 |
| Gebäude (Kunststoff) | 9503 00 75 |
| Figuren | 9503 00 49 |

### Sammlermodelle
| Produkttyp | Empfohlener Code |
|------------|------------------|
| Modellautos (Metall/Diecast) | 9503 00 55 |
| Modellautos (Kunststoff) | 9503 00 75 |
| Modelle mit Motor | 9503 00 81 |
| Bausätze | 9503 00 30 |

## Wichtiger Hinweis
Die korrekte Zolltarifnummer ist entscheidend für:
- Berechnung der Einfuhrabgaben
- Statistische Erfassung
- Einhaltung von Import-/Exportvorschriften

Bei Unsicherheit: Verbindliche Zolltarifauskunft (vZTA) beim Zoll beantragen.
