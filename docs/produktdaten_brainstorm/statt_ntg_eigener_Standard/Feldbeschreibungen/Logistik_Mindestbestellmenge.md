# Mindestbestellmenge

## Feldgruppe
Logistik & Verpackung

## Beschreibung
Die Mindestanzahl an Verkaufseinheiten, die ein Händler bei einer Bestellung abnehmen muss.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Mindestbestellmenge |
| Datentyp | Ganzzahl |
| Pflichtfeld | Nein |
| Minimalwert | 1 |
| Maximalwert | 9999 |
| Standardwert | 1 |

## Hinweis für Datenlieferanten
Die Mindestbestellmenge (MOQ = Minimum Order Quantity) gibt an, ab welcher Stückzahl ein Händler einen Artikel bestellen kann.

**Typische Szenarien:**
- **MOQ = 1**: Jede Menge bestellbar (Standard bei Modellbahnen)
- **MOQ = Umkarton-Menge**: Nur ganze Umkartons bestellbar
- **MOQ > 1**: Bestellungen nur in Mindestmengen (z.B. bei Kleinteilen)

Die Mindestbestellmenge ist oft verknüpft mit:
- Preiskonditionen (Staffelpreise)
- Logistik (nur Umkartonweise)
- Erstbestellungen vs. Nachbestellungen

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freie Eingabe als Ganzzahl.

## Beispiele
| Produkttyp | Mindestbestellmenge | Begründung |
|------------|---------------------|------------|
| H0-Lokomotive | 1 | Hochpreisig, einzeln bestellbar |
| H0-Güterwagen | 1 | Standard |
| Ersatzteile | 1 | Service-Artikel |
| Gleismaterial | 6 | Umkarton-gebunden |
| Streumaterial | 3 | Mindestabnahme |
| Figuren-Beutel | 12 | Display-Einheit |

## Hinweis für MHI-System
Wenn das Feld leer ist, wird Mindestbestellmenge = 1 angenommen.
