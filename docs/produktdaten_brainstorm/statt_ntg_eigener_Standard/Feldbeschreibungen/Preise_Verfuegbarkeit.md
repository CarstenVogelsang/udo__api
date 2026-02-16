# Feldbeschreibung: Verfuegbarkeit

## Gruppierung
**Preise & Verfügbarkeit**

## Feldname
`Verfuegbarkeit`

## Datentyp
Text (aus Werteliste)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Der aktuelle Verfügbarkeitsstatus des Artikels. Diese Information wird Händlern und Endkunden angezeigt und steuert die Erwartungshaltung bezüglich Lieferzeiten.

Bitte aktualisieren Sie den Status zeitnah bei Änderungen der Verfügbarkeit.

## Erlaubte Werte
**Nur Werte aus der Werteliste!**

## Werteliste
📎 **Siehe:** `Wertelisten/Werteliste_Preise_Verfuegbarkeit.xlsx`

Die Werteliste enthält:
- **Key**: Eindeutiger Surrogate Key
- **Verfuegbarkeit**: Bezeichnung des Status
- **Beschreibung**: Erklärung
- **Sortierung**: Anzeigereihenfolge

## Kurzübersicht der Status
| Key | Verfügbarkeit | Beschreibung |
|-----|---------------|--------------|
| SOF | Sofort lieferbar | Auf Lager, Versand innerhalb 1-2 Werktage |
| KUR | Kurzfristig lieferbar | Lieferbar in 3-7 Werktagen |
| LIE | Lieferbar | Lieferbar in 1-2 Wochen |
| LI4 | Lieferbar in 2-4 Wochen | Längere Lieferzeit |
| VOR | Vorbestellung | Neuheit, Erscheinungstermin bekannt |
| TER | Termin folgt | Neuheit, Erscheinungstermin noch offen |
| AUS | Ausverkauft | Aktuell nicht verfügbar, Nachschub erwartet |
| NML | Nicht mehr lieferbar | Dauerhaft nicht mehr verfügbar |

## Validierungsregeln
- Wert muss aus der Werteliste stammen
- **Groß-/Kleinschreibung spielt keine Rolle** – beim Import wird automatisch normalisiert

## Beispiele
| Eingabe | Status | Ergebnis |
|---------|--------|----------|
| `Sofort lieferbar` | ✓ Korrekt | → Sofort lieferbar |
| `sofort lieferbar` | ✓ Korrekt | → Sofort lieferbar |
| `SOFORT LIEFERBAR` | ✓ Korrekt | → Sofort lieferbar |
| `Lieferbar` | ✓ Korrekt | → Lieferbar |
| `Auf Lager` | ✗ Falsch | Nicht in Werteliste |
| `Verfügbar` | ✗ Falsch | Nicht in Werteliste |

## Hinweis für Datenlieferanten
Bitte informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei bei:
- Änderungen der Verfügbarkeit
- Lieferengpässen
- Ausverkauf von Artikeln
- Reaktivierung nicht mehr lieferbarer Artikel
