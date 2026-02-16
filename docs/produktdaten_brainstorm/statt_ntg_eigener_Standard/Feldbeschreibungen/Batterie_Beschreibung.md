# Batterie_Beschreibung

## Feldgruppe
Batterie

## Beschreibung
Die Art und Spezifikation der benötigten Batterien.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Batterie_Beschreibung |
| Datentyp | Text |
| Pflichtfeld | Bedingt (wenn Batterie_erforderlich = J) |
| Zeichenlänge | max. 100 |

## Hinweis für Datenlieferanten
Die Batterie-Beschreibung sollte Typ und Größe eindeutig angeben:

**Gängige Batterietypen:**
- AA (Mignon, LR6)
- AAA (Micro, LR03)
- C (Baby, LR14)
- D (Mono, LR20)
- 9V Block (6LR61)
- CR2032 (Knopfzelle)
- CR2025 (Knopfzelle)
- LR44 (Knopfzelle)

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freier Text.

## Beispiele
| Produkt | Batterie_Beschreibung |
|---------|----------------------|
| Fernbedienung | 2x AA (Mignon) |
| Sound-Modul | 1x CR2032 |
| Kinderbahn | 4x AA (Mignon) |
| Beleuchtetes Modell | 3x LR44 |
| Große Fernsteuerung | 4x C (Baby) |

## Format
Empfohlenes Format:
```
[Anzahl]x [Typ] ([Alternativbezeichnung])
```
