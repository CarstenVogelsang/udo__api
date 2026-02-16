# Digitalschnittstelle

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Die Decoder-Schnittstelle des Modells – ermöglicht die Nachrüstung oder den Austausch von Digitaldecodern.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Digitalschnittstelle |
| Datentyp | Text (Code) |
| Pflichtfeld | Nein |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Die Digitalschnittstelle ist relevant für:
- Modelle ohne Decoder (Nachrüstung)
- Modelle mit Decoder (Austausch, Upgrade)
- Zubehör-Decoder (Kompatibilität)

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Moba_Digitalschnittstelle.xlsx**

| Code | Schnittstelle | Pins | Beschreibung |
|------|---------------|------|--------------|
| NEM | NEM651 | 6 | Klein, für N/TT |
| N52 | NEM652 | 8 | Standard 8-polig |
| PLU | PluX | 8-22 | PluX8, PluX12, PluX16, PluX22 |
| P08 | PluX8 | 8 | PluX 8-polig |
| P12 | PluX12 | 12 | PluX 12-polig |
| P16 | PluX16 | 16 | PluX 16-polig |
| P22 | PluX22 | 22 | PluX 22-polig |
| MTX | mtc | 21 | Märklin/Trix 21-polig |
| NXT | Next18 | 18 | Next18 (modern) |
| N21 | 21MTC | 21 | 21-polig MTC |
| KEI | Keine | - | Keine Schnittstelle |

## Beispiele
| Produkt | Schnittstelle | Hinweis |
|---------|---------------|---------|
| Märklin 39212 | MTX | mtc 21-polig |
| Roco 73120 | P22 | PluX22 |
| Fleischmann 731401 (N) | NXT | Next18 |
| Älteres Modell | N52 | NEM652 8-polig |
| Analogmodell | NEM | NEM651 für Nachrüstung |

## Hinweis zur Kompatibilität
Die Schnittstelle bestimmt, welche Decoder passen:
- mtc: Märklin/Trix Decoder
- PluX: ESU, Zimo, Doehler & Haass
- Next18: Moderne kompakte Decoder
