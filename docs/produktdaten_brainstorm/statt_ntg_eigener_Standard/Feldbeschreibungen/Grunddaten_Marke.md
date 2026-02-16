# Marke

## Feldgruppe
Grunddaten

## Beschreibung
Die Marke, unter der das Produkt verkauft wird. Eine Marke gehört immer zu einem Hersteller – ein Hersteller kann mehrere Marken führen.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Marke |
| Datentyp | Text (Code) |
| Pflichtfeld | Ja |
| Zeichenlänge | 3-5 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Die Marke ist die Dachmarke oder Produktmarke, unter der das Produkt im Handel und beim Endkunden bekannt ist.

**Hierarchie:**
```
Hersteller (Firma)
└── Marke (Produktmarke)
    └── Serie (optional, Produktlinie)
```

**Beispiele:**
- Hersteller "Gebr. Märklin & Cie. GmbH" → Marken: Märklin, Trix, LGB
- Hersteller "Modelleisenbahn Holding GmbH" → Marken: Roco, Fleischmann
- Hersteller "NOCH GmbH & Co. KG" → Marken: NOCH, NOCH creative

Bitte verwenden Sie ausschließlich die Codes aus der zugehörigen Werteliste.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Grunddaten_Marke.xlsx**

Die Werteliste enthält:
- Key (Surrogate Key der Marke)
- Marke (Markenname)
- Hersteller_Key (Referenz auf Werteliste_Grunddaten_Hersteller)
- Beschreibung
- Website

## Beispiele
| Hersteller | Marke (Key) | Markenname |
|------------|-------------|------------|
| MAR | MAE | Märklin |
| MAR | TRX | Trix |
| MAR | LGB | LGB |
| MAR | MYW | Märklin my world |
| MAR | MSU | Märklin Start up |
| MEH | ROC | Roco |
| MEH | FLE | Fleischmann |
| NOC | NOC | NOCH |
| NOC | NCR | NOCH creative |
| BUS | BUS | Busch |
| BUS | BAU | Busch Automodelle |

## Zusammenhang mit Hersteller
Das Feld "Marke" ergänzt das Feld "Hersteller":
- **Hersteller**: Die produzierende/verantwortliche Firma (rechtliche Einheit)
- **Marke**: Die Produktmarke, unter der verkauft wird

Ein Artikel hat immer genau einen Hersteller und genau eine Marke.
