# Serie

## Feldgruppe
Grunddaten

## Beschreibung
Die Produktserie oder Produktlinie innerhalb einer Marke. Eine Marke kann mehrere Serien haben, die sich an unterschiedliche Zielgruppen oder Preissegmente richten.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Serie |
| Datentyp | Text (Code) |
| Pflichtfeld | Nein |
| Zeichenlänge | 3-5 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Die Serie ist eine optionale Untergliederung innerhalb einer Marke. Sie bezeichnet Produktlinien, die sich durch Zielgruppe, Qualitätsstufe oder Preissegment unterscheiden.

**Hierarchie:**
```
Hersteller (Firma)
└── Marke (Produktmarke)
    └── Serie (Produktlinie) ← optional
```

**Beispiele:**
- Marke "Märklin" → Serien: my world, Start up
- Marke "Roco" → Serien: Roco Line, geoLINE
- Marke "Piko" → Serien: Expert, Hobby, Classics, myTrain

**Wann Serie verwenden?**
- Wenn der Hersteller offiziell Produktlinien unterscheidet
- Wenn unterschiedliche Qualitäts-/Preisstufen existieren
- Wenn spezielle Zielgruppen angesprochen werden (Kinder, Einsteiger, Profis)

**Wann Serie leer lassen?**
- Wenn das Produkt keiner speziellen Serie zugeordnet ist
- Wenn der Hersteller keine Serien-Unterscheidung macht

Bitte verwenden Sie ausschließlich die Codes aus der zugehörigen Werteliste.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Grunddaten_Serie.xlsx**

Die Werteliste enthält:
- Key (Surrogate Key der Serie)
- Serie (Serienname)
- Marke_Key (Referenz auf Werteliste_Grunddaten_Marke)
- Beschreibung
- Zielgruppe
- URL (offizielle Produktseite, falls vorhanden)
- Sortierung

## Beispiele
| Marke | Serie (Key) | Serienname | Zielgruppe | URL |
|-------|-------------|------------|------------|-----|
| MAE | MYW | my world | Kinder ab 3 | maerklin.de/de/produkte/my-world |
| MAE | MSU | Start up | Kinder ab 6, Einsteiger | maerklin.de/de/produkte/start-up |
| ROC | RLN | Roco Line | Standard | roco.cc/de/products/h0-roco-line |
| ROC | GEO | geoLINE | Einsteiger | roco.cc/de/products/h0-geoline |
| PIK | EXP | Expert | Sammler, Experten | piko.de/de/piko-expert |
| PIK | PHB | Hobby | Einsteiger, Standard | piko.de/de/piko-hobby |

## Zusammenhang mit Marke
Das Feld "Serie" ergänzt das Feld "Marke":
- **Marke**: Die Produktmarke (z.B. Märklin)
- **Serie**: Die Produktlinie innerhalb der Marke (z.B. my world)

Ein Artikel hat immer genau eine Marke, aber nicht zwingend eine Serie.
