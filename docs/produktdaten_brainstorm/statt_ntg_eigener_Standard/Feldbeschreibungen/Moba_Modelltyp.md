# Modelltyp

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Die Unterkategorie des Schienenfahrzeugs – unterscheidet nach Antriebsart bei Lokomotiven oder Bauart bei Wagen.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Modelltyp |
| Datentyp | Text (Code) |
| Pflichtfeld | Ja (bei Rollmaterial) |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Der Modelltyp verfeinert die Modellkategorie und bestimmt die verfügbaren Detailtypen.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Moba_Modelltyp.xlsx**

### Lokomotiven (LOK)
| Code | Modelltyp | Beschreibung |
|------|-----------|--------------|
| DLO | Dampflokomotive | Dampfbetriebene Lokomotiven |
| ELO | Elektrolokomotive | Elektrisch betriebene Lokomotiven |
| DIL | Diesellokomotive | Dieselbetriebene Lokomotiven |
| KLO | Kleinlokomotive | Rangierloks, Köf, Kö |

### Triebwagen (TWG)
| Code | Modelltyp | Beschreibung |
|------|-----------|--------------|
| ETW | Elektrotriebwagen | E-Triebwagen, S-Bahn, U-Bahn |
| DTW | Dieseltriebwagen | Schienenbus, Triebwagen |
| DMU | Dieseltriebzug | Mehrteilige Diesel-Triebzüge |
| EMU | Elektrotriebzug | ICE, TGV, Mehrteilige E-Triebzüge |

### Personenwagen (PWG)
| Code | Modelltyp | Beschreibung |
|------|-----------|--------------|
| REI | Reisezugwagen | Sitzwagen, Großraumwagen |
| LIE | Liegewagen | Liegewagen, Schlafwagen |
| SPW | Speisewagen | Restaurant, Bistro |
| GEP | Gepäckwagen | Gepäck, Post, Bahnpost |
| STW | Steuerwagen | Wendezug-Steuerwagen |

### Güterwagen (GWG)
| Code | Modelltyp | Beschreibung |
|------|-----------|--------------|
| OFF | Offener Güterwagen | Hochbordwagen, Schüttgutwagen |
| GED | Gedeckter Güterwagen | Geschlossene Güterwagen |
| FLA | Flachwagen | Rungenwagen, Containerwagen |
| KES | Kesselwagen | Tank- und Kesselwagen |
| KUE | Kühlwagen | Kühl- und Isolierwagen |
| SIL | Silowagen | Schüttgut-Silowagen |
| SON | Sondergüterwagen | Spezialwagen |

## Beispiele
| Produkt | Kategorie | Modelltyp |
|---------|-----------|-----------|
| BR 01 | LOK | DLO |
| BR 103 | LOK | ELO |
| BR 218 | LOK | DIL |
| VT 98 Schienenbus | TWG | DTW |
| ICE 3 | TWG | EMU |
| IC-Wagen 2. Klasse | PWG | REI |
| Eanos Hochbordwagen | GWG | OFF |
