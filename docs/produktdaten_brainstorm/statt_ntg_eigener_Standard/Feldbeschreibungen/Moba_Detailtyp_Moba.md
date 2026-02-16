# Detailtyp_Moba

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Die feinste Klassifizierungsebene für Schienenfahrzeuge – unterscheidet nach Einsatzzweck oder Bauart.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Detailtyp_Moba |
| Datentyp | Text (Code) |
| Pflichtfeld | Nein |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Der Detailtyp ermöglicht eine präzise Kategorisierung für spezifische Kundensuchen und Filterung im Shop.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Moba_Detailtyp.xlsx**

### Dampflokomotiven (DLO)
| Code | Detailtyp | Beschreibung |
|------|-----------|--------------|
| SCH | Schnellzuglok | Schnellzug-Dampfloks (BR 01, 03, 18) |
| PER | Personenzuglok | Personenzug-Dampfloks (BR 38, 78) |
| GUE | Güterzuglok | Güterzug-Dampfloks (BR 44, 50, 52) |
| TEN | Tenderlok | Tender-Dampfloks (BR 64, 86, 94) |
| SCM | Schmalspurlok | Schmalspur-Dampfloks |

### Elektrolokomotiven (ELO)
| Code | Detailtyp | Beschreibung |
|------|-----------|--------------|
| SCE | Schnellzug-Elok | Schnellzug-Eloks (BR 103, 120) |
| UNE | Universal-Elok | Mehrzweck-Eloks (BR 110, 111) |
| GUE | Güterzug-Elok | Güterzug-Eloks (BR 151, 185) |
| RAN | Rangierlok | E-Rangierloks (BR 163, 294) |

### Diesellokomotiven (DIL)
| Code | Detailtyp | Beschreibung |
|------|-----------|--------------|
| STR | Streckenlok | Strecken-Dieselloks (BR 218, 232) |
| RAN | Rangierlok | Diesel-Rangierloks (BR 260, 294) |
| KLE | Kleinlok | Klein-Dieselloks (Köf, Kö) |

### Güterwagen-Details
| Code | Detailtyp | Beschreibung |
|------|-----------|--------------|
| STA | Standard | Standard-Bauart |
| SPE | Speziell | Sonderbauart |
| PRI | Privatwagen | Firmenwagen mit Werbung |

## Beispiele
| Produkt | Kategorie | Modelltyp | Detailtyp |
|---------|-----------|-----------|-----------|
| BR 01 | LOK | DLO | SCH |
| BR 64 | LOK | DLO | TEN |
| BR 103 | LOK | ELO | SCE |
| BR 218 | LOK | DIL | STR |
| BR 260 | LOK | DIL | RAN |
