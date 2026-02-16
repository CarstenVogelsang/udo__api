# Kontakt_Hersteller

## Feldgruppe
Compliance & Regulatorik

## Beschreibung
Die vollständige Kontaktadresse des Herstellers gemäß den Anforderungen der Produktsicherheitsverordnung und der Spielzeugrichtlinie.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Kontakt_Hersteller |
| Datentyp | Text (mehrzeilig) |
| Pflichtfeld | Ja |
| Zeichenlänge | max. 500 |
| Format | Name, Straße, PLZ Ort, Land |

## Hinweis für Datenlieferanten
Die Herstellerangabe ist auf Produkten und Verpackungen gesetzlich vorgeschrieben. Sie muss den Verbraucher in die Lage versetzen, den Hersteller zu kontaktieren.

**Pflichtangaben:**
- Firmenname (vollständig)
- Straße und Hausnummer
- Postleitzahl und Ort
- Land

**Optional, aber empfohlen:**
- Telefonnummer
- E-Mail-Adresse
- Website

Bei Nicht-EU-Herstellern muss zusätzlich die "Verantwortliche Person in der EU" angegeben werden (siehe Feld Kontakt_Verantwortliche_Person_EU).

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freier Text nach Vorgabe des Herstellers.

## Beispiele
```
Gebr. Märklin & Cie. GmbH
Stuttgarter Str. 55-57
73033 Göppingen
Deutschland
Tel.: +49 7161 608-0
www.maerklin.de
```

```
NOCH GmbH & Co. KG
Lindauer Str. 49
88239 Wangen im Allgäu
Deutschland
www.noch.de
```

```
Wiking Modellbau GmbH & Co. KG
Schlittenbacher Str. 60
58511 Lüdenscheid
Deutschland
```

## Validierung
- Mindestens 4 Zeilen (Name, Straße, PLZ/Ort, Land)
- Keine Postfachadressen erlaubt
- Adresse muss postalisch erreichbar sein
