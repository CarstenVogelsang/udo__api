# Digitaldecoder

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Der eingebaute Digitaldecoder – gibt an, welches Digitalformat das Modell ab Werk unterstützt.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Digitaldecoder |
| Datentyp | Text (Code) |
| Pflichtfeld | Nein |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Der Digitaldecoder bestimmt, mit welchen Digitalzentralen das Modell gesteuert werden kann.

**Wichtig:** Nur den werksseitig eingebauten Decoder angeben, nicht nachgerüstete Decoder.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Moba_Digitaldecoder.xlsx**

| Code | Decoder | Beschreibung |
|------|---------|--------------|
| MFX | mfx | Märklin mfx (automatische Anmeldung) |
| MFP | mfx+ | Märklin mfx+ mit erweitertem Sound |
| DCC | DCC | Digital Command Control (NMRA) |
| MMS | MM + Sound | Märklin Motorola mit Sound |
| MM2 | MM2 | Märklin Motorola 2 |
| MUL | Multiprotokoll | DCC + MM + mfx |
| SEL | Selectrix | Selectrix-Protokoll |
| ANA | Analog | Kein Decoder (rein analog) |
| VOR | Vorbereitet | Schnittstelle vorhanden |

## Beispiele
| Produkt | Digitaldecoder | Beschreibung |
|---------|----------------|--------------|
| Märklin 39212 | MFP | mfx+ mit Sound |
| Märklin 36183 | MFX | mfx ohne Sound |
| Märklin 29000 (Start up) | ANA | Analoger Einsteigerartikel |
| Roco 73120 | DCC | DCC-Decoder ab Werk |
| Fleischmann 731401 | MUL | Multiprotokoll (DCC+MM) |
| Trix 22912 | DCC | DCC mit Sound |

## Hinweis
Bei Modellen mit Schnittstelle (Vorbereitet) zusätzlich das Feld Digitalschnittstelle ausfüllen.
