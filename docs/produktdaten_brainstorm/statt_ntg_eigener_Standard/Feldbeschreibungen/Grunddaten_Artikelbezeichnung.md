# Feldbeschreibung: Artikelbezeichnung

## Gruppierung
**Grunddaten**

## Feldname
`Artikelbezeichnung`

## Datentyp
Text

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Die technische Artikelbezeichnung für den B2B-Bereich (Händler, Großhandel, interne Systeme). Diese Bezeichnung sollte sachlich und präzise sein und alle wesentlichen Produktmerkmale enthalten.

Die Artikelbezeichnung dient der eindeutigen Identifikation im Warenwirtschaftssystem und sollte folgende Informationen enthalten:
- Produktart (z.B. Elektrolok, Dampflok, Modellauto)
- Modellbezeichnung (z.B. BR 193, BR 01)
- Ggf. Bahngesellschaft oder Marke
- Maßstab/Spurweite

## Erlaubte Werte
- Freitext
- Minimale Länge: 10 Zeichen
- Maximale Länge: 100 Zeichen
- Erlaubte Sonderzeichen: - / ( ) . , &

## Validierungsregeln
- Mindestens 10 Zeichen (aussagekräftige Bezeichnung)
- Maximal 100 Zeichen
- Keine reinen Großbuchstaben (NICHT: "ELEKTROLOK BR 193")
- Keine HTML-Tags
- Keine Emojis oder Sonderzeichen außer den erlaubten

## Aufbau-Empfehlung
**Modelleisenbahn:**
`[Produktart] [Baureihe] [Bahngesellschaft] [Zusatzinfo]`

**Sammlermodelle:**
`[Marke] [Modell] [Farbe] [Maßstab]`

## Temporär erlaubte Werte
- Vorläufige Bezeichnungen bei Neuheiten mit Vermerk "(Arbeitstitel)"
- Muss vor Markteinführung durch finale Bezeichnung ersetzt werden

## Beispiele
| Wert | Status | Bemerkung |
|------|--------|-----------|
| `Elektrolok BR 193 Vectron DB Cargo` | ✓ Korrekt | Präzise, alle Infos |
| `Dampflok BR 01 DRG Epoche II` | ✓ Korrekt | Mit Epoche |
| `Porsche 911 (992) Carrera 4S silber 1:18` | ✓ Korrekt | Sammlermodell |
| `Lok` | ✗ Falsch | Zu kurz, nicht aussagekräftig |
| `ELEKTROLOK BR 193 VECTRON` | ✗ Falsch | Nicht in Großbuchstaben |
| `Tolle neue Lok!!!` | ✗ Falsch | Keine Werbung, sachlich bleiben |

## Werteliste
Keine – freies Feld mit Validierung

## Abgrenzung zu Artikelbezeichnung_B2C
| Feld | Zweck | Stil |
|------|-------|------|
| `Artikelbezeichnung` | B2B, Warenwirtschaft | Sachlich, technisch |
| `Artikelbezeichnung_B2C` | Endkunde, Online-Shop | Emotional, Marketing |
