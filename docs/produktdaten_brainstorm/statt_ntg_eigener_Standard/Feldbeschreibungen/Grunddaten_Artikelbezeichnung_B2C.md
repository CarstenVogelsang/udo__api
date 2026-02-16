# Feldbeschreibung: Artikelbezeichnung_B2C

## Gruppierung
**Grunddaten**

## Feldname
`Artikelbezeichnung_B2C`

## Datentyp
Text

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Die Marketing-Artikelbezeichnung für den B2C-Bereich (Endkunden, Online-Shops, Marktplätze). Diese Bezeichnung wird dem Endkunden angezeigt und sollte ansprechend, emotional und verkaufsfördernd formuliert sein.

Die B2C-Bezeichnung erscheint als Produkttitel in Online-Shops, auf Amazon, eBay und anderen Marktplätzen. Sie sollte:
- Den Markennamen enthalten
- Das Produkt klar benennen
- Emotional ansprechen
- SEO-relevant sein (wichtige Suchbegriffe)

## Erlaubte Werte
- Freitext
- Minimale Länge: 20 Zeichen
- Maximale Länge: 80 Zeichen (wichtig für Amazon-Darstellung!)
- Erlaubte Sonderzeichen: - / ( ) . , & –

## Validierungsregeln
- Mindestens 20 Zeichen
- Maximal 80 Zeichen (Amazon-Limit beachten!)
- Keine reinen Großbuchstaben
- Keine HTML-Tags
- Keine Emojis
- Keine Preisangaben oder "Angebot", "Sale", etc.
- Keine übertriebenen Werbeaussagen ("Bester", "Nr. 1")

## Aufbau-Empfehlung
**Modelleisenbahn:**
`[Marke] [Produktart] [Baureihe] – [Emotionaler Zusatz]`

**Sammlermodelle:**
`[Marke] [Originalmarke] [Modell] – [Emotionaler Zusatz]`

## Temporär erlaubte Werte
- Vorläufige Bezeichnungen bei Neuheiten
- Muss spätestens 4 Wochen vor Markteinführung finalisiert sein

## Beispiele
| Wert | Status | Bemerkung |
|------|--------|-----------|
| `Märklin Elektrolok BR 193 Vectron – Die Kraft der neuen Generation` | ✓ Korrekt | Emotional, mit Marke |
| `Schuco Porsche 911 Carrera 4S – Ikone in Silber` | ✓ Korrekt | Sammlermodell, ansprechend |
| `Roco Dampflok BR 01 – Legende auf Schienen` | ✓ Korrekt | Kurz und prägnant |
| `Elektrolok BR 193` | ✗ Falsch | Zu kurz, keine Marke, nicht emotional |
| `MÄRKLIN ELEKTROLOK BR 193 VECTRON` | ✗ Falsch | Keine Großbuchstaben |
| `Beste Lok aller Zeiten! Jetzt kaufen!` | ✗ Falsch | Keine Werbefloskeln |
| `Märklin H0 39193 Elektrolok BR 193 Vectron DB Cargo AC Digital Sound mfx+ Epoche VI Neuheit 2025` | ✗ Falsch | Zu lang (>80 Zeichen) |

## Werteliste
Keine – freies Feld mit Validierung

## SEO-Hinweis
Die B2C-Bezeichnung ist entscheidend für die Auffindbarkeit in Suchmaschinen und auf Marktplätzen. Wichtige Suchbegriffe sollten enthalten sein:
- Markenname (Märklin, Roco, Schuco, etc.)
- Produkttyp (Elektrolok, Dampflok, Modellauto)
- Modellbezeichnung (BR 193, 911, etc.)
