# Feldbeschreibung: Artikelbeschreibung

## Gruppierung
**Grunddaten**

## Feldname
`Artikelbeschreibung`

## Datentyp
Text (Langtext)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Die technische Produktbeschreibung für den B2B-Bereich. Diese Beschreibung enthält alle relevanten technischen Daten und Produkteigenschaften in sachlicher Form. Sie dient Händlern und Einkäufern als Informationsgrundlage.

Die Artikelbeschreibung sollte enthalten:
- Technische Spezifikationen
- Ausstattungsmerkmale
- Maßangaben
- Materialangaben
- Lieferumfang

## Erlaubte Werte
- Freitext
- Minimale Länge: 50 Zeichen
- Maximale Länge: 1000 Zeichen
- Erlaubte Sonderzeichen: - / ( ) . , & : ; mm cm

## Validierungsregeln
- Mindestens 50 Zeichen (aussagekräftige Beschreibung)
- Maximal 1000 Zeichen
- Keine HTML-Tags (werden entfernt)
- Keine Emojis
- Keine Preisangaben
- Zeilenumbrüche erlaubt

## Inhaltliche Anforderungen

### Modelleisenbahn
Die Beschreibung sollte folgende Informationen enthalten:
- Spurweite und Maßstab
- Stromsystem (AC/DC)
- Decoder-Ausstattung
- Beleuchtung
- Sound (ja/nein)
- Länge über Puffer
- Epoche
- Bahngesellschaft
- Besondere Features

### Sammlermodelle
Die Beschreibung sollte folgende Informationen enthalten:
- Maßstab
- Material (Diecast, Kunststoff, Resine)
- Funktionen (öffenbare Türen, Lenkung, etc.)
- Farbe
- Originalfahrzeug (Marke, Modell, Baujahr)

## Temporär erlaubte Werte
- Vorläufige Kurzbeschreibung bei Neuheiten mit Vermerk "[Beschreibung folgt]"
- Muss vor Markteinführung vervollständigt werden

## Beispiele

### Korrekt (Modelleisenbahn):
```
H0 Elektrolokomotive BR 193 Vectron der DB Cargo, Epoche VI.
Ausführung mit mfx+ Decoder und umfangreichem Soundpaket.
LED-Beleuchtung mit Lichtwechsel. Länge über Puffer: 218 mm.
Mehrzweckschnittstelle 21MTC. Mindestradius: 360 mm.
4 angetriebene Achsen, Haftreifen.
```

### Korrekt (Sammlermodell):
```
Modellauto Porsche 911 (992) Carrera 4S im Maßstab 1:18.
Hochwertiger Druckguss (Die-Cast) mit Kunststoffteilen.
Türen, Motorhaube und Kofferraum zum Öffnen.
Lenkbare Vorderräder. Detaillierter Innenraum und Motorraum.
Farbe: Silbermetallic. Inklusive Vitrinenbox.
```

### Falsch:
```
Tolle Lok, ein Muss für jeden Sammler!
```
→ Keine technischen Informationen, nur Werbung

## Werteliste
Keine – freies Feld mit Validierung

## Abgrenzung zu Artikelbeschreibung_B2C
| Feld | Zweck | Stil |
|------|-------|------|
| `Artikelbeschreibung` | B2B, Warenwirtschaft | Sachlich, technisch, Fakten |
| `Artikelbeschreibung_B2C` | Endkunde, Online-Shop | Emotional, erzählend, Marketing |
