# Feldbeschreibung: Hersteller

## Gruppierung
**Grunddaten**

## Feldname
`Hersteller`

## Datentyp
Text (aus Werteliste)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Der Markenname bzw. Herstellername des Produkts. Bitte verwenden Sie ausschließlich Werte aus der vorgegebenen Werteliste. Der Hersteller wird für die Zuordnung im System, für Filter in Online-Shops und für die Markensuche verwendet.

Falls Ihr Herstellername nicht in der Werteliste enthalten ist, melden Sie diesen bitte an MHI zur Aufnahme in die Liste.

## Erlaubte Werte
**Nur Werte aus der Werteliste!**

## Werteliste
📎 **Siehe:** `Wertelisten/Werteliste_Grunddaten_Hersteller.xlsx`

Die Werteliste enthält:
- **Key**: Eindeutiger 3-stelliger Surrogate Key (z.B. MAR, TRX, ROC)
- **Hersteller**: Offizieller Markenname
- **Moba_Rollmaterial**: J/N - Herstellt Modelleisenbahn-Fahrzeuge
- **Moba_Zubehoer**: J/N - Herstellt Modelleisenbahn-Zubehör
- **Sammlermodelle**: J/N - Herstellt Sammlermodelle
- **Land**: ISO-2 Ländercode des Firmensitzes
- **Website**: Offizielle Website
- **Bemerkung**: Zusätzliche Informationen

## Validierungsregeln
- Wert muss exakt aus der Werteliste stammen
- Groß-/Kleinschreibung beachten
- Keine Abkürzungen (nicht "MM" statt "Märklin")
- Keine Zusätze (nicht "Märklin GmbH" statt "Märklin")

## Temporär erlaubte Werte
- Bei neuen Herstellern, die noch nicht in der Liste sind:
  - Temporär den Namen eintragen
  - **Pflicht-Meldung an MHI** zur Aufnahme in die Werteliste
  - Format der Meldung: Hersteller-Name, Land, Website, Produktkategorie

## Beispiele
| Wert | Status | Bemerkung |
|------|--------|-----------|
| `Märklin` | ✓ Korrekt | Exakt aus Werteliste |
| `märklin` | ✗ Falsch | Kleinschreibung |
| `MÄRKLIN` | ✗ Falsch | Großschreibung |
| `Märklin GmbH` | ✗ Falsch | Zusatz nicht erlaubt |
| `MM` | ✗ Falsch | Abkürzung |
| `Maerklin` | ✗ Falsch | Falsche Schreibweise |

## Prozess für neue Hersteller
1. Datenlieferant stellt fest, dass Hersteller nicht in Liste
2. Meldung an MHI mit: Name, Land, Website, Kategorie
3. MHI prüft und nimmt in Werteliste auf (vergibt Key)
4. Datenlieferant wird informiert und kann Wert verwenden

## Hinweis
Die Kombination aus `Hersteller` + `Artikelnummer_Hersteller` muss systemweit eindeutig sein. Duplikate werden abgelehnt.
