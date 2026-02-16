# Angetriebene_Achsen

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Die Antriebsformel oder Achsfolge des Modells – gibt an, welche und wie viele Achsen angetrieben sind.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Angetriebene_Achsen |
| Datentyp | Text |
| Pflichtfeld | Nein |
| Zeichenlänge | max. 20 |

## Hinweis für Datenlieferanten
Die Antriebsformel beschreibt die Achsanordnung nach UIC-Notation:

**Notation:**
- Großbuchstaben = Anzahl angetriebener Achsen (A=1, B=2, C=3, D=4)
- Kleinbuchstaben = Anzahl Laufachsen (a=1, b=2, o=0)
- Hochgestellte Ziffer (') = Einzelachsantrieb
- Zahlen = Achszahl in Drehgestellen

**Beispiele der Notation:**
- B'B' = 2 Drehgestelle mit je 2 angetriebenen Achsen (E-Lok)
- 1'C1' = 1 Laufachse vorn, 3 Kuppelachsen, 1 Laufachse hinten
- Co'Co' = 2 Drehgestelle mit je 3 Achsen

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freie Textangabe nach UIC-Notation.

## Beispiele
| Lokomotive | Antriebsformel | Beschreibung |
|------------|----------------|--------------|
| BR 103 | Co'Co' | 6 Achsen in 2 Drehgestellen |
| BR 218 | B'B' | 4 Achsen in 2 Drehgestellen |
| BR 01 | 2'C1' | 2+3+1 Achsen |
| BR 64 | 1'C1' | 1+3+1 Achsen |
| BR 44 | 1'E | 1+5 Achsen |
| Köf II | B | 2 Achsen starr |
| Re 460 | Bo'Bo' | 4 Achsen einzeln angetrieben |

## Vereinfachte Angabe
Alternativ zur UIC-Notation kann auch eine vereinfachte Angabe erfolgen:
- "Allachsantrieb"
- "4 von 6 Achsen angetrieben"
- "2 Antriebsachsen"
