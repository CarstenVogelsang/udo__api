# Feldbeschreibung: Artikelbeschreibung_B2C

## Gruppierung
**Grunddaten**

## Feldname
`Artikelbeschreibung_B2C`

## Datentyp
Text (Langtext)

## Pflichtfeld
Ja

## Beschreibung für Datenlieferant
Die Marketing-Produktbeschreibung für den B2C-Bereich (Endkunden, Online-Shops). Diese Beschreibung wird dem Endkunden angezeigt und sollte emotional, ansprechend und verkaufsfördernd formuliert sein.

Die B2C-Beschreibung erzählt eine Geschichte, weckt Emotionen und macht Lust auf das Produkt. Sie sollte:
- Den Kunden emotional ansprechen
- Die Besonderheiten hervorheben
- Einen Kaufanreiz schaffen
- Leicht verständlich sein (keine Fachbegriffe ohne Erklärung)

## Erlaubte Werte
- Freitext
- Minimale Länge: 100 Zeichen
- Maximale Länge: 2000 Zeichen
- Erlaubte Sonderzeichen: - / ( ) . , & : ; ! ?

## Validierungsregeln
- Mindestens 100 Zeichen
- Maximal 2000 Zeichen
- Keine HTML-Tags (werden separat in SEO-Feld gepflegt)
- Keine Emojis
- Keine Preisangaben oder "ab XX €"
- Keine Vergleiche mit Wettbewerbern
- Keine übertriebenen Werbeaussagen ("Bester", "Einzigartig", "Nr. 1")
- Zeilenumbrüche erlaubt

## Inhaltliche Anforderungen
Die Beschreibung sollte folgende Elemente enthalten:

1. **Einleitung** – Emotionaler Einstieg, der Interesse weckt
2. **Highlights** – Die wichtigsten Produktvorteile
3. **Details** – Technische Infos verständlich erklärt
4. **Abschluss** – Kaufanreiz oder Sammlerargument

## Temporär erlaubte Werte
- Vorläufige Beschreibung bei Neuheiten
- Muss spätestens 4 Wochen vor Markteinführung finalisiert sein

## Beispiele

### Korrekt (Modelleisenbahn):
```
Erleben Sie die kraftvolle BR 193 Vectron in beeindruckender Detailtreue!

Die moderne Mehrsystemlokomotive von Siemens ist das Arbeitspferd
im europäischen Güterverkehr – und jetzt hält sie Einzug auf Ihrer
Modellbahnanlage.

Mit dem hochwertigen mfx+ Decoder und authentischem Soundpaket
wird jede Fahrt zum Erlebnis. Hören Sie das Anlassen der Motoren,
das Surren der Lüfter und das charakteristische Fahrgeräusch.

Die LED-Beleuchtung mit vorbildgerechtem Lichtwechsel und die
fein gravierten Details machen dieses Modell zu einem echten
Blickfang auf jeder Anlage.
```

### Korrekt (Sammlermodell):
```
Der neue Elfer in bestechender Silber-Metallic Lackierung –
ein Muss für jeden Porsche-Enthusiasten!

Schuco präsentiert den Porsche 911 (992) Carrera 4S als
hochwertiges Sammlermodell im Maßstab 1:18. Die Liebe zum
Detail zeigt sich in jedem Winkel: Von den originalgetreuen
Felgen über den detaillierten Motorraum bis hin zum
authentischen Interieur.

Türen, Motorhaube und Kofferraum lassen sich öffnen und
geben den Blick auf liebevoll gestaltete Details frei.
Die lenkbaren Vorderräder runden das Gesamtbild ab.

Inklusive hochwertiger Vitrinenbox zur staubfreien Präsentation.
```

### Falsch:
```
Beste Lok auf dem Markt! Kaufen Sie jetzt! Nur noch wenige verfügbar!
Besser als Konkurrenzprodukte! Jetzt zuschlagen!
```
→ Keine Produktinformation, nur Werbefloskeln, Vergleich mit Wettbewerb

## Werteliste
Keine – freies Feld mit Validierung

## Hinweis zur Tonalität
| Richtig | Falsch |
|---------|--------|
| "beeindruckende Detailtreue" | "der beste jemals gebaute" |
| "hochwertig verarbeitet" | "konkurrenzlos gut" |
| "ein echter Blickfang" | "ein absolutes Muss" |
| "für anspruchsvolle Sammler" | "nur für echte Kenner" |
