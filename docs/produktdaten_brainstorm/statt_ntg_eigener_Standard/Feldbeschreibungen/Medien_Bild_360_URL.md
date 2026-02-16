# Bild_360_URL

## Feldgruppe
Medien

## Beschreibung
Die URL zu einer 360°-Ansicht oder einem drehbaren Produktbild.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Bild_360_URL |
| Datentyp | URL |
| Pflichtfeld | Nein |
| Zeichenlänge | max. 500 |
| Format | https://... |

## Hinweis für Datenlieferanten
360°-Bilder ermöglichen eine Rundumansicht des Produkts:

**Mögliche Formate:**
- 360°-Viewer (JavaScript-basiert)
- Bildsequenz (36 oder 72 Einzelbilder)
- Interaktives HTML

**Technische Anforderungen:**
- Gleichmäßige Beleuchtung in allen Winkeln
- Präzise Drehung (10° oder 5° Schritte)
- Einheitlicher Hintergrund

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – URL vom Hersteller.

## Beispiele
```
https://www.maerklin.de/360/39212/index.html
https://cdn.hersteller.de/360/product_12345.json
```

## Hinweis
Falls keine echte 360°-Ansicht verfügbar ist, können alternativ mehrere Ansichten (Front, Seite, Rück) über Bild_Detail_URL bereitgestellt werden.
