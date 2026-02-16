# CE_Kennzeichen

## Feldgruppe
Compliance & Regulatorik

## Beschreibung
Angabe, ob das Produkt die CE-Kennzeichnung trägt und damit die Konformität mit den geltenden EU-Richtlinien bestätigt wird.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | CE_Kennzeichen |
| Datentyp | Text (Code) |
| Pflichtfeld | Ja |
| Zeichenlänge | 1 |
| Erlaubte Werte | J, N |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Die CE-Kennzeichnung ist für Spielwaren in der EU verpflichtend (Spielzeugrichtlinie 2009/48/EG).

**CE = J (Ja) erforderlich bei:**
- Spielzeug gemäß Spielzeugrichtlinie
- Elektrische/elektronische Produkte (EMV-Richtlinie)
- Produkte mit Funkfunktion (RED-Richtlinie)

**CE = N (Nein) möglich bei:**
- Sammlermodelle mit Hinweis "Kein Spielzeug"
- Reine Dekorationsartikel
- Modelle für den professionellen Einsatz

Die CE-Kennzeichnung erfordert eine vollständige Konformitätsbewertung und technische Dokumentation durch den Hersteller.

Bei Änderungen des CE-Status informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
| Code | Bedeutung |
|------|-----------|
| J | CE-Kennzeichnung vorhanden |
| N | Keine CE-Kennzeichnung |

## Beispiele
| Produkttyp | CE_Kennzeichen | Begründung |
|------------|----------------|------------|
| H0-Lokomotive mit Decoder | J | Elektrisches Spielzeug |
| Startpackung | J | Spielzeug mit Trafo |
| Sammlermodell 1:18 "Kein Spielzeug" | N | Nicht als Spielzeug deklariert |
| Gebäudebausatz | J | Spielzeug für Kinder |
| Gleisschotter lose | N | Landschaftsmaterial |
