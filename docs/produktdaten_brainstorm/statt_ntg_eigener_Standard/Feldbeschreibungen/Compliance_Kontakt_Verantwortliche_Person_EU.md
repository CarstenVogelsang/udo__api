# Kontakt_Verantwortliche_Person_EU

## Feldgruppe
Compliance & Regulatorik

## Beschreibung
Die Kontaktdaten der "Verantwortlichen Person" in der EU gemäß Marktüberwachungsverordnung (EU) 2019/1020 – erforderlich für Produkte von Nicht-EU-Herstellern.

## Technische Spezifikation
| Eigenschaft | Wert |
|-------------|------|
| Feldname | Kontakt_Verantwortliche_Person_EU |
| Datentyp | Text (mehrzeilig) |
| Pflichtfeld | Bedingt (bei Nicht-EU-Herstellern) |
| Zeichenlänge | max. 500 |
| Format | Name, Straße, PLZ Ort, Land, E-Mail |

## Hinweis für Datenlieferanten
Seit Juli 2021 müssen alle Produkte, die in der EU in Verkehr gebracht werden und von einem Nicht-EU-Hersteller stammen, eine "verantwortliche Person" in der EU angeben.

**Die Verantwortliche Person kann sein:**
- Der Importeur mit Sitz in der EU
- Ein bevollmächtigter Vertreter des Herstellers
- Ein Fulfillment-Dienstleister mit Sitz in der EU

**Aufgaben der Verantwortlichen Person:**
- Bereithaltung der EU-Konformitätserklärung
- Bereitstellung technischer Dokumentation für Behörden
- Kooperation mit Marktüberwachungsbehörden
- Information über Produktsicherheitsprobleme

Bei EU-Herstellern ist dieses Feld nicht erforderlich (Kontakt_Hersteller reicht aus).

Bei Änderungen informieren Sie MHI proaktiv durch Einsendung einer aktualisierten Gesamt- oder Änderungsdatei.

## Werteliste
Keine – freier Text.

## Beispiele
**Für chinesischen Hersteller:**
```
EU-Bevollmächtigter:
Import Service GmbH
Hauptstraße 123
12345 Berlin
Deutschland
E-Mail: compliance@importservice.de
```

**Für US-Hersteller:**
```
Verantwortliche Person EU:
Transatlantic Toys Ltd.
Business Park 45
1234 AB Amsterdam
Niederlande
responsible-person@transatlantic.eu
```

## Kennzeichnung auf Produkt
Die Verantwortliche Person muss auf dem Produkt, der Verpackung oder einem Begleitdokument angegeben werden. Die Angabe erfolgt oft mit dem Symbol einer Fabrik und "EU".

## Hinweis für EU-Hersteller
Wenn Kontakt_Hersteller eine EU-Adresse enthält, kann dieses Feld leer bleiben oder die gleiche Adresse enthalten.
