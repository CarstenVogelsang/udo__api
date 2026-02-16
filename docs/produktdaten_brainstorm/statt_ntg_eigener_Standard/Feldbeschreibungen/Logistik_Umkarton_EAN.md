# Umkarton_EAN

## Feldgruppe
Logistik & Verpackung

## Beschreibung
Die EAN/GTIN des Umkartons (Masterpack, Versandkarton), in dem mehrere Verkaufseinheiten zusammengefasst werden.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Umkarton_EAN |
| Datentyp | Text (numerisch) |
| Pflichtfeld | Nein |
| Zeichenlänge | 13-14 |
| Format | GTIN-13 oder GTIN-14 |

## Hinweis für Datenlieferanten
Die Umkarton-EAN ist eine separate GTIN, die das Gebinde/Masterpack identifiziert – nicht zu verwechseln mit der Artikel-EAN der Verkaufseinheit.

**Typische Anwendung:**
- 6 Stück eines Artikels werden in einem Umkarton geliefert
- Der Umkarton hat eine eigene EAN für die Logistik
- Händler bestellen oft umkartonweise

Die Umkarton-EAN ist besonders relevant für:
- Wareneingang beim Handel
- Lagerlogistik und Kommissionierung
- EDI-Bestellungen (Bestellung auf Gebindeebene)

Wenn kein separater Umkarton existiert oder keine eigene EAN vergeben wurde, bleibt das Feld leer.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – GTIN vom Hersteller vergeben.

## Beispiele
| Artikel-EAN | Umkarton-EAN | Menge |
|-------------|--------------|-------|
| 4001883123456 | 4001883123463 | 6 |
| 4007246012345 | 14007246012342 | 12 |

## Validierung
- Muss gültige GTIN-13 oder GTIN-14 sein
- Prüfziffer muss korrekt sein
- Darf nicht identisch mit Artikel-EAN sein
