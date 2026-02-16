# Verpackung_Hoehe_mm

## Feldgruppe
Logistik & Verpackung

## Beschreibung
Die Höhe der Verkaufsverpackung in Millimetern – die kürzeste Seite der Verpackung.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Verpackung_Hoehe_mm |
| Datentyp | Ganzzahl |
| Pflichtfeld | Ja |
| Einheit | Millimeter (mm) |
| Minimalwert | 1 |
| Maximalwert | 9999 |

## Hinweis für Datenlieferanten
Die Verpackungshöhe komplettiert die Maßangaben für die Volumenberechnung.

**Messkonvention:**
Höhe = die kürzeste Kante der Verpackung.

Bitte messen Sie die Außenmaße der geschlossenen Verkaufsverpackung.

Bei Änderungen der Verpackung informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freie Eingabe als Ganzzahl.

## Beispiele
| Verpackungstyp | Typische Höhe |
|----------------|---------------|
| H0-Lok Standardkarton | 50-80 |
| H0-Wagen Einzelverpackung | 40-60 |
| N-Lok Verpackung | 30-50 |
| Startpackung | 80-150 |
| Blisterverpackung Autos | 30-50 |

## Volumenberechnung
Das Verpackungsvolumen ergibt sich aus:
**Volumen (cm³) = Länge × Breite × Höhe / 1000**

Für die Berechnung des Volumengewichts (relevant für Versand):
**Volumengewicht (kg) = Länge × Breite × Höhe / 5.000.000**
(Divisor variiert je nach Spediteur zwischen 4.000.000 und 6.000.000)
