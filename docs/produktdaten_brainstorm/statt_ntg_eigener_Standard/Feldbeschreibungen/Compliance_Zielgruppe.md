# Zielgruppe

## Feldgruppe
Compliance & Regulatorik

## Beschreibung
Die primäre Produktkategorie hinsichtlich der Zielgruppe – bestimmt, ob das Produkt als Spielzeug oder Sammlerartikel eingestuft wird.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Zielgruppe |
| Datentyp | Text (Code) |
| Pflichtfeld | Ja |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Die Zielgruppe hat direkte Auswirkungen auf:
- Anwendbare Richtlinien (Spielzeugrichtlinie vs. Produktsicherheit)
- CE-Kennzeichnung und Prüfanforderungen
- Warnhinweise und Altersfreigaben
- Shop-Kategorisierung

**Wichtig:** Die Einstufung muss konsistent mit der tatsächlichen Produktkennzeichnung sein. Ein Produkt mit "Kein Spielzeug"-Hinweis muss als SAM (Sammler) eingestuft werden.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Compliance_Zielgruppe.xlsx**

| Code | Zielgruppe | Beschreibung |
|------|------------|--------------|
| KIN | Kinder | Spielzeug für Kinder (Spielzeugrichtlinie) |
| JUG | Jugendliche | Produkte für Jugendliche 14+ |
| ERW | Erwachsene | Hobbyartikel für erwachsene Modellbahner |
| SAM | Sammler | Sammlermodelle (Kein Spielzeug) |
| PRO | Professionell | Gewerbliche Nutzung, Ausstellungen |
| ALL | Alle | Familienprodukte ohne Altersbeschränkung |

## Beispiele
| Produkt | Zielgruppe | Begründung |
|---------|------------|------------|
| H0-Lokomotive Standard | ERW | Hobby-Modellbahn |
| myWorld Kinderbahn | KIN | Explizit für Kinder konzipiert |
| Sammlermodell 1:18 | SAM | "Kein Spielzeug" deklariert |
| Startpackung | ALL | Für die ganze Familie |
| Profi-Digitalzentrale | PRO | Für erfahrene Anwender |

## Auswirkungen im MHI-System
| Zielgruppe | CE erforderlich | Spielzeugprüfung | Warnhinweise |
|------------|-----------------|------------------|--------------|
| KIN | Ja | Ja | Pflicht |
| ERW | Ja | Meist ja | Pflicht |
| SAM | Nein* | Nein | "Kein Spielzeug" |
| PRO | Bedingt | Nein | Nach Bedarf |

*Sammlermodelle unterliegen der allgemeinen Produktsicherheit, nicht der Spielzeugrichtlinie.
