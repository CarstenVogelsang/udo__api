# Modellkategorie

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Die übergeordnete Kategorie des Schienenfahrzeugs – unterscheidet zwischen Triebfahrzeugen, Wagen und Zugverbänden.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Modellkategorie |
| Datentyp | Text (Code) |
| Pflichtfeld | Ja (bei Rollmaterial) |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Die Modellkategorie ist die erste Klassifizierungsebene für Schienenfahrzeuge und bestimmt die nachfolgenden Auswahlmöglichkeiten bei Modelltyp und Detailtyp.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_Moba_Modellkategorie.xlsx**

| Code | Kategorie | Beschreibung |
|------|-----------|--------------|
| LOK | Lokomotiven | Alle Triebfahrzeuge (Dampf, Diesel, Elektro) |
| TWG | Triebwagen | Triebwagen, Triebzüge, Schienenbusse |
| PWG | Personenwagen | Reisezugwagen, Gepäckwagen |
| GWG | Güterwagen | Alle Arten von Güterwagen |
| ZUG | Zugset | Komplette Zuggarnituren |
| SON | Sonderfahrzeuge | Bauzüge, Arbeitswagen, Kranwagen |
| GLB | Gleisbaufahrzeuge | Stopfmaschinen, Schotterwagen |

## Beispiele
| Produkt | Modellkategorie |
|---------|-----------------|
| BR 103 E-Lok | LOK |
| VT 11.5 TEE | TWG |
| IC-Großraumwagen | PWG |
| Schiebeplanenwagen | GWG |
| ICE 4 Triebzug | ZUG |
| Gleiskraftwagen | SON |

## Kategorie-Hierarchie
```
Modellkategorie
└── Modelltyp
    └── Detailtyp_Moba
```
