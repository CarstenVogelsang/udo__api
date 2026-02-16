# Rauchsatz_Vorbereitung

## Feldgruppe
Moba Rollmaterial

## Beschreibung
Angabe, ob das Modell für die Nachrüstung eines Rauchgenerators vorbereitet ist.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Rauchsatz_Vorbereitung |
| Datentyp | Text (Code) |
| Pflichtfeld | Nein |
| Zeichenlänge | 1 |
| Erlaubte Werte | J, N |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Dieses Feld ist relevant, wenn Rauchgenerator = N:

**Vorbereitet bedeutet:**
- Mechanische Aufnahme vorhanden
- Elektrischer Anschluss möglich
- Passender Rauchsatz erhältlich

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
| Code | Bedeutung |
|------|-----------|
| J | Für Rauchsatz vorbereitet |
| N | Nicht für Rauchsatz vorbereitet |

## Beispiele
| Produkt | Rauchgenerator | Vorbereitung | Hinweis |
|---------|----------------|--------------|---------|
| Märklin 39010 | J | - | Rauch eingebaut |
| Märklin 36010 | N | J | Nachrüstbar |
| Märklin 29000 | N | N | Nicht vorgesehen |

## Zusammenhang
Wenn Rauchsatz_Vorbereitung = J, sollte Rauchsatz_Artikelnr ausgefüllt werden.
