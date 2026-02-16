# Mindestradius_mm

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Der minimale Gleisradius in Millimetern, den das Modell noch sicher befahren kann.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Mindestradius_mm |
| Datentyp | Ganzzahl |
| Pflichtfeld | Empfohlen |
| Einheit | Millimeter (mm) |
| Minimalwert | 100 |
| Maximalwert | 9999 |

## Hinweis für Datenlieferanten
Der Mindestradius ist entscheidend für die Anlagenplanung:

**Typische Radien (H0):**
- Märklin C-Gleis R1: 360 mm
- Märklin C-Gleis R2: 437,5 mm
- Märklin C-Gleis R3: 515 mm
- Roco Line R2: 358 mm
- Roco Line R3: 419 mm

**Faustregel:**
- Kurze Fahrzeuge: kleinerer Mindestradius
- Lange Fahrzeuge: größerer Mindestradius
- Drehgestell-Wagen: flexibler als Starrachswagen

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freie Eingabe als Ganzzahl.

## Beispiele (H0)
| Fahrzeugtyp | Mindestradius |
|-------------|---------------|
| Rangierlok (Köf) | 295 mm |
| Tenderlok (BR 64) | 360 mm |
| Schlepptenderlok (BR 01) | 360 mm |
| E-Lok (BR 103) | 360 mm |
| Personenwagen 26,4m | 360 mm |
| ICE-Triebkopf | 360 mm |
| ICE-Mittelwagen | 360 mm |
| Großraum-Güterwagen | 360 mm |

## Hinweis
Modelle können oft engere Radien befahren als angegeben, aber mit Einschränkungen (erhöhter Verschleiß, Entgleisungsgefahr, optisch unschön).
