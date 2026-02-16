# Sound

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Angabe, ob das Modell über Soundfunktionen verfügt (Motorgeräusch, Pfeife, Ansagen etc.).

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Sound |
| Datentyp | Text (Code) |
| Pflichtfeld | Nein |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Sound ist eines der beliebtesten Features bei digitalen Modellbahnen. Typische Soundfunktionen umfassen:

**Dampfloks:**
- Dampfschlag (fahrstufenabhängig)
- Pfeife, Glocke
- Luftpumpe, Kohleschaufeln

**Dieselloks:**
- Motorgeräusch (drehzahlabhängig)
- Horn, Signalhorn
- Druckluft, Kompressor

**E-Loks:**
- Fahrgeräusch, Lüfter
- Signalhorn
- Pantograph-Geräusch

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Moba_Sound.xlsx**

| Code | Sound | Beschreibung |
|------|-------|--------------|
| MFP | mfx+ Sound | Märklin mfx+ mit Sound |
| DCS | DCC Sound | DCC-Decoder mit Sound |
| MMS | MM Sound | Märklin Motorola mit Sound |
| ESU | ESU LokSound | ESU LokSound-Decoder |
| ZIM | Zimo Sound | Zimo Sound-Decoder |
| KEI | Kein Sound | Ohne Soundfunktion |
| VOR | Vorbereitet | Soundschnittstelle vorhanden |

## Beispiele
| Produkt | Sound | Hinweis |
|---------|-------|---------|
| Märklin 39212 | MFP | mfx+ Sound eingebaut |
| Märklin 36183 | KEI | Ohne Sound |
| Roco 73120 | DCS | DCC mit Sound |
| ESU 31xxx | ESU | LokSound V5.0 |
| Fleischmann 731401 | DCS | DCC Sound |

## Hinweis
Bei Sound-Modellen ist oft ein Pufferkondensator eingebaut, um Soundaussetzer bei Stromunterbrechungen zu vermeiden.
