# LUCID_Nr

## Feldgruppe
Compliance & Regulatorik

## Beschreibung
Die Registrierungsnummer im LUCID-Verpackungsregister der Zentralen Stelle Verpackungsregister (ZSVR) gemäß Verpackungsgesetz (VerpackG).

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | LUCID_Nr |
| Datentyp | Text |
| Pflichtfeld | Ja (für Erstinverkehrbringer) |
| Format | DE + 15-stellige Nummer |
| Zeichenlänge | 17 |

## Hinweis für Datenlieferanten
Jeder Hersteller/Importeur, der Verpackungen erstmals in Deutschland in Verkehr bringt, muss sich im LUCID-Register registrieren und seine Verpackungen bei einem dualen System lizenzieren.

**LUCID-Pflicht gilt für:**
- Verkaufsverpackungen (Kartons, Blister, Folien)
- Umverpackungen (Displays, Umkartons)
- Versandverpackungen (wenn der Hersteller selbst versendet)

**Ausnahmen:**
- B2B-Verpackungen (verbleiben beim Handel)
- Mehrwegverpackungen
- Transportverpackungen

Die LUCID-Registrierung muss vor dem erstmaligen Inverkehrbringen erfolgen.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – Registrierungsnummer von ZSVR vergeben.

## Beispiele
| Hersteller | LUCID_Nr |
|------------|----------|
| Märklin | DE1234567890123 |
| Busch | DE9876543210987 |

## Validierung
- Muss mit "DE" beginnen
- Gefolgt von 15 Ziffern
- Kann unter lucid.verpackungsregister.org verifiziert werden

## Hinweis
Händler wie MHI nutzen die LUCID-Nr. des Herstellers für die Produktkennzeichnung und zur Erfüllung eigener Dokumentationspflichten.
