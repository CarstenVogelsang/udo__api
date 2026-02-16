# Stromsystem

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Das elektrische System des Modells – Wechselstrom (AC) oder Gleichstrom (DC). Entscheidend für die Gleissystem-Kompatibilität.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Stromsystem |
| Datentyp | Text (Code) |
| Pflichtfeld | Ja (bei elektrischen Fahrzeugen) |
| Zeichenlänge | 2 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Das Stromsystem bestimmt die grundsätzliche Kompatibilität mit Gleissystemen:

**AC (Wechselstrom / 3-Leiter):**
- Märklin H0 (C-Gleis, K-Gleis, M-Gleis)
- Mittelleiter-System
- Polaritätsunabhängig

**DC (Gleichstrom / 2-Leiter):**
- Roco, Fleischmann, Piko, Tillig, etc.
- Schienenprofilgleise
- Polaritätsabhängig für Fahrtrichtung

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
| Code | Stromsystem | Beschreibung |
|------|-------------|--------------|
| AC | Wechselstrom | 3-Leiter-System (Märklin) |
| DC | Gleichstrom | 2-Leiter-System (Roco, Fleischmann, etc.) |

## Beispiele
| Produkt | Stromsystem | Hinweis |
|---------|-------------|---------|
| Märklin 39212 | AC | Märklin H0 |
| Trix 22912 | DC | Trix = DC-Version von Märklin |
| Roco 73120 | DC | Roco H0 |
| Fleischmann 731401 | DC | N-Spur ist immer DC |
| Märklin 88012 | - | Z-Spur ist immer DC |

## Wagen ohne Motor
Bei Wagen ohne eigenen Antrieb wird das Stromsystem oft leer gelassen oder entsprechend der Kupplungsaufnahme/Radsätze angegeben:
- AC-Wagen haben oft Mittelleiter-Schleifer
- DC-Wagen haben profilierte Radsätze

## Hinweis auf Wechselradsätze
Viele Hersteller bieten Wechselradsätze an, um Wagen systemkompatibel zu machen (siehe Felder AC_Radsatz_Artikelnr, DC_Radsatz_Artikelnr).
