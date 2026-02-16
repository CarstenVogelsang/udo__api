# Feldbeschreibung: Artikelstatus

## Gruppierung
**Grunddaten**

## Feldname
`Artikelstatus`

## Datentyp
Text (aus Werteliste)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Der Artikelstatus beschreibt den aktuellen Lebenszyklus-Status des Produkts im Sortiment. Er steuert, wie der Artikel in Systemen behandelt wird (z.B. Anzeige im Shop, Bestellbarkeit, Lagerhaltung).

Bitte aktualisieren Sie den Status zeitnah bei Änderungen, damit Händler und Systeme korrekt reagieren können.

## Erlaubte Werte
**Nur Werte aus der Werteliste!**

## Werteliste
📎 **Siehe:** `Wertelisten/Werteliste_Grunddaten_Artikelstatus.xlsx`

Die Werteliste enthält:
- **Key**: Eindeutiger 3-stelliger Surrogate Key (z.B. AKT, NEU, AUS)
- **Status**: Bezeichnung des Status
- **Beschreibung**: Erklärung des Status
- **Sortierung**: Reihenfolge im Lebenszyklus

## Kurzübersicht der Status
| Key | Status | Beschreibung |
|-----|--------|--------------|
| ANK | Ankündigung | Angekündigt, noch keine Details/Preise |
| NEU | Neuheit | Neuer Artikel, kann vorbestellt werden |
| AKT | Aktiv | Regulärer Verkaufsartikel |
| LIM | Limitiert | Limitierte Auflage, keine Nachproduktion |
| SAI | Saisonartikel | Nur zu bestimmten Zeiten verfügbar |
| AUS | Auslauf | Wird nicht mehr produziert, Restbestände |
| STR | Streichung | Aus dem Sortiment genommen |
| REA | Reaktivierung | Ehemals gestrichen, wird wieder produziert |

## Validierungsregeln
- Wert muss aus der Werteliste stammen
- **Groß-/Kleinschreibung spielt keine Rolle** – beim Import wird automatisch normalisiert
- Keine Kombinationen (nicht "Auslauf/Streichung")
- Keine Zusätze (nicht "Aktiv - wenig Bestand")

## Hinweis zur Schreibweise
Die Schreibweise ist flexibel. Folgende Eingaben werden alle als **"Aktiv"** erkannt:
- `Aktiv`
- `aktiv`
- `AKTIV`
- `AkTiV`

Der Import-Prozess normalisiert automatisch auf die korrekte Schreibweise.

## Status-Übergänge (Lebenszyklus)
```
Ankündigung → Neuheit → Aktiv → Auslauf → Streichung
                                    ↑
                            Reaktivierung
```

| Von | Nach | Wann |
|-----|------|------|
| Ankündigung | Neuheit | Wenn Details und Preise feststehen |
| Neuheit | Aktiv | Nach Erstauslieferung / Neuheitenzeitraum vorbei |
| Aktiv | Auslauf | Wenn Produktionsende beschlossen |
| Auslauf | Streichung | Wenn letzte Bestände verkauft |
| Streichung | Reaktivierung | Wenn Wiederauflage beschlossen |
| Reaktivierung | Aktiv | Nach Wiederaufnahme der Produktion |

## Temporär erlaubte Werte
Keine – Status muss immer aus Werteliste gewählt werden.

Bei Unsicherheit: Status "Aktiv" verwenden und Rücksprache mit MHI.

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `Aktiv` | ✓ Korrekt | → Aktiv |
| `aktiv` | ✓ Korrekt | → Aktiv |
| `AKTIV` | ✓ Korrekt | → Aktiv |
| `Neuheit` | ✓ Korrekt | → Neuheit |
| `neuheit` | ✓ Korrekt | → Neuheit |
| `Neu` | ✗ Falsch | Nicht in Werteliste |
| `Verfügbar` | ✗ Falsch | Nicht in Werteliste |
| `Auslauf/Streichung` | ✗ Falsch | Keine Kombinationen |

## Hinweis für Datenlieferanten
Bitte informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei bei:
- Neuen Artikeln (Ankündigung → Neuheit)
- Produktionsende (Aktiv → Auslauf)
- Sortimentsbereinigung (Auslauf → Streichung)
- Wiederauflagen (Streichung → Reaktivierung)
