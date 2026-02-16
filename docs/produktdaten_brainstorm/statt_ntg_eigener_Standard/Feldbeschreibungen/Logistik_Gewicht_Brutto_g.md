# Gewicht_Brutto_g

## Feldgruppe
Logistik & Verpackung

## Beschreibung
Das Bruttogewicht des Produkts in Gramm – inklusive Verkaufsverpackung, Anleitungen, Beilagen und sonstigem Zubehör.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Gewicht_Brutto_g |
| Datentyp | Ganzzahl |
| Pflichtfeld | Ja |
| Einheit | Gramm (g) |
| Minimalwert | 1 |
| Maximalwert | 999999 |

## Hinweis für Datenlieferanten
Das Bruttogewicht ist die maßgebliche Größe für:
- Berechnung der Versandkosten
- Lagerplanung und Handling
- Transportkostenermittlung

Dieses Gewicht sollte dem tatsächlichen Versandgewicht einer Verkaufseinheit (VKE) entsprechen.

Bei Sets oder Aktionspackungen das Gesamtgewicht der Packung angeben, nicht das Gewicht der Einzelteile summieren.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freie Eingabe als Ganzzahl.

## Beispiele
| Produkttyp | Typischer Wert |
|------------|----------------|
| H0-Lokomotive in OVP | 400-800 |
| H0-Wagenset (3-tlg.) | 300-500 |
| N-Startpackung | 1500-3000 |
| 1:87 Modellauto in Vitrinenbox | 50-120 |
| Großer Gebäudebausatz | 500-1500 |

## Validierung
Gewicht_Brutto_g sollte größer oder gleich Gewicht_Netto_g sein.
