# AC_Radsatz_Artikelnr

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Die Artikelnummer des Wechselradsatzes für den Betrieb auf Wechselstrom-Anlagen (3-Leiter/Märklin).

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | AC_Radsatz_Artikelnr |
| Datentyp | Text |
| Pflichtfeld | Nein |
| Zeichenlänge | max. 20 |

## Hinweis für Datenlieferanten
Dieses Feld ist relevant für DC-Modelle, die auf AC-Anlagen (Märklin) betrieben werden sollen:

**Typische Anwendung:**
- Roco/Fleischmann-Wagen auf Märklin-Anlage
- Wechselradsatz mit Mittelleiter-Schleifer

**Voraussetzung:**
- Modell ist DC (Gleichstrom)
- Passender AC-Radsatz verfügbar

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – Artikelnummer des Herstellers.

## Beispiele
| DC-Modell | AC_Radsatz_Artikelnr | Hersteller |
|-----------|----------------------|------------|
| Roco H0-Wagen | 40196 | Roco |
| Fleischmann H0-Wagen | 6560 | Fleischmann |
| Piko H0-Wagen | 56062 | Piko |

## Hinweis
Bei reinen AC-Modellen (Märklin) bleibt dieses Feld leer, da kein Wechsel nötig ist.

## Zusammenhang
Für die Gegenrichtung (AC → DC) siehe Feld DC_Radsatz_Artikelnr.
