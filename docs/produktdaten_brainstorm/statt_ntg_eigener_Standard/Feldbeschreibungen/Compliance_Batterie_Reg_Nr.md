# Batterie_Reg_Nr

## Feldgruppe
Compliance & Regulatorik

## Beschreibung
Die Registrierungsnummer beim Umweltbundesamt (UBA) gemäß Batteriegesetz (BattG) für Produkte, die Batterien enthalten oder mit Batterien betrieben werden.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Batterie_Reg_Nr |
| Datentyp | Text |
| Pflichtfeld | Bedingt (bei Batterieprodukten) |
| Format | Herstellernummer / Markennummer |
| Zeichenlänge | max. 50 |

## Hinweis für Datenlieferanten
Die Batterieregistrierung ist Pflicht für Hersteller/Importeure, die Batterien oder Produkte mit eingebauten Batterien in Deutschland in Verkehr bringen.

**Registrierungspflicht bei:**
- Produkte mit eingebauten Batterien (nicht entnehmbar)
- Produkte mit beiliegenden Batterien
- Ersatzbatterien/Akkus als Zubehör

**Nicht registrierungspflichtig:**
- Produkte, die nur batteriebetrieben werden können, aber ohne Batterien geliefert werden
- Produkte für industrielle Anwendung

Seit 2021 erfolgt die Registrierung ebenfalls über das LUCID-Portal der ZSVR.

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – Registrierungsnummer vom UBA/ZSVR vergeben.

## Beispiele
| Produkttyp | Batterie_Reg_Nr |
|------------|-----------------|
| Lok mit Sound (Batterie im Lieferumfang) | 12345_Märklin |
| Handregler mit Akku | 12345_Märklin |

## Validierung
Die Batterie-Registrierung kann unter lucid.verpackungsregister.org geprüft werden.

## Zusammenhang mit Batterie-Feldern
Wenn Batterie_Reg_Nr angegeben wird, sollten auch die Felder der Feldgruppe "Batterie" ausgefüllt werden:
- Batterie_erforderlich
- Batterie_im_Lieferumfang
- Batterie_Beschreibung
- Batterie_Anzahl_enthalten
