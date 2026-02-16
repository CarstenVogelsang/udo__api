# Originalmodell

## Feldgruppe
Sammlermodelle

## Beschreibung
Die genaue Modellbezeichnung des Vorbildfahrzeugs.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Originalmodell |
| Datentyp | Text |
| Pflichtfeld | Empfohlen |
| Zeichenlänge | max. 100 |

## Hinweis für Datenlieferanten
Das Originalmodell spezifiziert die exakte Variante des Vorbildfahrzeugs:

**Enthalten sollte:**
- Modellreihe (z.B. "911", "E-Klasse", "Golf")
- Baureihe/Generation (z.B. "W124", "Typ 1")
- Motorisierung (z.B. "Turbo", "V8", "TDI")
- Karosserieform (z.B. "Coupé", "Cabrio", "Kombi")

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freier Text.

## Beispiele
| Originalmarke | Originalmodell |
|---------------|----------------|
| Mercedes-Benz | 300 SL Flügeltürer (W198) |
| Porsche | 911 Turbo (930) |
| Volkswagen | Käfer 1303 Cabriolet |
| BMW | M3 E30 Sport Evolution |
| Ferrari | F40 |
| MAN | TGX 18.640 XXL |
| Airbus | A380-800 |

## Formatierung
Empfohlene Struktur:
```
[Modellname] [Variante/Zusatz] ([Baureihencode])
```
Beispiel: "911 Turbo S (991.2)"
