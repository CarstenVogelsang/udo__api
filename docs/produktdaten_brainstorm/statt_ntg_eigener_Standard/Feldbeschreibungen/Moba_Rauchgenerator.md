# Rauchgenerator

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Angabe, ob das Modell einen eingebauten Rauchgenerator hat (typisch bei Dampfloks).

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Rauchgenerator |
| Datentyp | Text (Code) |
| Pflichtfeld | Nein |
| Zeichenlänge | 1 |
| Erlaubte Werte | J, N |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Der Rauchgenerator erzeugt mithilfe von Verdampferflüssigkeit Rauch aus dem Schornstein – ein beliebtes Effekt-Feature bei Dampfloks.

**Funktionsweise:**
- Heizelement verdampft Spezialflüssigkeit
- Rauch steigt aus dem Schornstein
- Bei Digital-Betrieb schaltbar

**Hinweis:** Regelmäßiges Nachfüllen der Rauchflüssigkeit erforderlich.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
| Code | Bedeutung |
|------|-----------|
| J | Rauchgenerator eingebaut |
| N | Kein Rauchgenerator |

## Beispiele
| Produkt | Rauchgenerator | Hinweis |
|---------|----------------|---------|
| Märklin 39010 (BR 01) | J | Mit Rauchsatz |
| Märklin 36010 (BR 01 Start up) | N | Ohne Rauch |
| Märklin 37889 (BR 44) | J | Mit Rauchsatz |

## Zusammenhang mit anderen Feldern
- Wenn Rauchgenerator = N, prüfen Rauchsatz_Vorbereitung
- Wenn nachrüstbar, Rauchsatz_Artikelnr angeben
