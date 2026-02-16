# Sortiment

## Feldgruppe
SEO & Marketing

## Beschreibung
Die übergeordnete Produktkategorie/Sortimentsgruppe für die Shop-Navigation und Katalogstruktur.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Sortiment |
| Datentyp | Text (Code) |
| Pflichtfeld | Ja |
| Zeichenlänge | 3 |
| Groß-/Kleinschreibung | Egal (wird normalisiert) |

## Hinweis für Datenlieferanten
Das Sortiment bestimmt die Hauptkategorie im Shop und die grundsätzliche Produktzuordnung.

**Sortiment-Hierarchie:**
Das Sortiment ist die oberste Ebene der Kategorisierung:
- Sortiment → Modellkategorie → Modelltyp → Detailtyp

Beispiel:
- Sortiment: Modelleisenbahn H0
- Modellkategorie: Lokomotiven
- Modelltyp: Diesellokomotiven
- Detailtyp: Streckendiesellok

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Siehe **Werteliste_SEO_Sortiment.xlsx**

| Code | Sortiment | Beschreibung |
|------|-----------|--------------|
| MH0 | Modelleisenbahn H0 | Spurweite H0 (1:87) |
| MN0 | Modelleisenbahn N | Spurweite N (1:160) |
| MTT | Modelleisenbahn TT | Spurweite TT (1:120) |
| MZ0 | Modelleisenbahn Z | Spurweite Z (1:220) |
| MS1 | Modelleisenbahn Spur 1 | Spurweite 1 (1:32) |
| MLG | Modelleisenbahn LGB | Gartenbahn (1:22,5) |
| MZU | Modellbahn-Zubehör | Gleise, Decoder, Elektronik |
| MLA | Modellbahn-Landschaft | Gebäude, Figuren, Vegetation |
| SAM | Sammlermodelle | Automodelle, Flugzeuge, Schiffe |
| KIN | Kinderbahnen | Spielbahnen, my world |
| ERS | Ersatzteile | Service und Reparatur |

## Beispiele
| Produkt | Sortiment |
|---------|-----------|
| Märklin H0 Lokomotive | MH0 |
| Fleischmann N Güterwagen | MN0 |
| NOCH H0 Bahnhof | MLA |
| Viessmann Signaldecoder | MZU |
| Wiking 1:87 LKW | SAM |
| Märklin my world | KIN |
| LGB Dampflok | MLG |

## Shop-Verwendung
Das Sortiment bestimmt:
- Hauptnavigation im Shop
- Filteroptionen
- Kategorie-Landing-Pages
- SEO-URLs (z.B. /modelleisenbahn-h0/lokomotiven/)
