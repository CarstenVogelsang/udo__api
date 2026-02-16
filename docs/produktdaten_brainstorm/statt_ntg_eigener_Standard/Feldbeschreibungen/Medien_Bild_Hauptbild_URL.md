# Bild_Hauptbild_URL

## Feldgruppe
Medien

## Beschreibung
Die URL zum Hauptbild des Produkts – das primäre Produktfoto für Shop und Marktplätze.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Bild_Hauptbild_URL |
| Datentyp | URL |
| Pflichtfeld | Ja |
| Zeichenlänge | max. 500 |
| Format | https://... |

## Hinweis für Datenlieferanten
Das Hauptbild ist das wichtigste Produktbild und sollte höchsten Qualitätsansprüchen genügen:

**Bildanforderungen:**
- Mindestauflösung: 2000 x 2000 Pixel
- Format: JPG oder PNG
- Hintergrund: Weiß oder freigestellt
- Perspektive: Frontansicht / Hauptansicht
- Beleuchtung: Gleichmäßig, keine harten Schatten

**URL-Anforderungen:**
- HTTPS-Protokoll
- Direkter Link zur Bilddatei
- Permanente URL (keine Session-IDs)

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – URL vom Hersteller.

## Beispiele
```
https://www.maerklin.de/media/product/39212_main.jpg
https://cdn.hersteller.de/images/products/12345_hero.png
```

## Validierung
- URL muss mit https:// beginnen
- Dateiendung: .jpg, .jpeg, .png, .webp
- URL muss erreichbar sein (HTTP 200)
