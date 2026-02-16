# pim/management/commands/import_auswahlschluesselliste_artikelidentifikationen.py
from django.core.management.base import BaseCommand
from base.models_auswahl import AuswahlSchluesselliste, AuswahlGruppe
from base.konstanten import AG_ARTIKELIDENTIFIKATION

class Command(BaseCommand):
    help = 'Importiert die Identifikationen für Artikel in die Tabelle AuswahlSchluesselliste'

    def add_arguments(self, parser):
        # Optionales Flag für das Aktualisieren vorhandener Einträge
        parser.add_argument(
            '--update',
            action='store_true',
            help='Aktualisiert vorhandene Einträge, wenn dieses Flag gesetzt ist.'
        )

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE(self.help))
        self.stdout.write(self.style.NOTICE('Starte...'))

        # Prüfe, ob das Update-Flag gesetzt ist
        update_existing = kwargs['update']

        # Erstelle oder hole die AuswahlGruppe für Artikel-Identifikationen
        gruppe_name = AG_ARTIKELIDENTIFIKATION
        gruppe, created = AuswahlGruppe.objects.get_or_create(gruppe=gruppe_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'AuswahlGruppe hinzugefügt: {gruppe_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'AuswahlGruppe existiert bereits: {gruppe_name}'))

        # Definiere die Artikel-Identifikationen
        artikel_identifikationen = [
            ('ean', 'European Article Number (EAN)', '13-stellige Artikelnummer zur globalen Produktkennzeichnung, z. B. 4006381333931.'),
            ('gtin', 'Global Trade Item Number (GTIN)', 'Globale Produktidentifikationsnummer, umfasst EAN, UPC, ISBN.'),
            ('upc', 'Universal Product Code (UPC)', 'Amerikanisches Äquivalent zur EAN, meist 12-stellig.'),
            ('isbn', 'International Standard Book Number (ISBN)', 'Einzigartige Buchidentifikationsnummer, meist 13-stellig.'),
            ('mpn', 'Hersteller-Artikel-Nummer (MPN/HAN)', 'Die Artikelnummer eines Herstellers zur Identifikation eines Produkts.'),
            # Amazon spezifische Identifikationen
            ('asin', 'Amazon Standard Identification Number (ASIN)', 'Von Amazon vergebene Identifikationsnummer für Produkte.'),
            ('fnsku', 'Fulfillment Network Stock Keeping Unit (FNSKU)', 'Von Amazon vergebene SKU für FBA-Produkte.'),  
            # eBay spezifische Identifikationen
            ('epid', 'eBay Product Identifier (ePID)', 'Von eBay vergebene eindeutige Produktnummer für Katalogeinträge.'),
            #('ebay_item_id', 'eBay Item ID', 'Einzigartige Artikelnummer für jedes auf eBay gelistete Produkt.'),
            # Otto Marktplatz spezifische Identifikationen
            ('otto_mpn', 'OTTO MPN', 'Manufacturer Part Number (MPN) für Artikel bei Otto.'),
            # Idealo spezifische Identifikationen
            ('idealo_id', 'Idealo Produkt-ID', 'Von Idealo vergebene eindeutige Identifikationsnummer für Produkte.'),
            # Weitere Online-Marktplätze und Handelsplattformen
            ('google_shopping_id', 'Google Shopping ID', 'Von Google Shopping verwendete eindeutige Produktkennzeichnung.'),
            ('bol_id', 'Bol.com Product ID', 'Produkt-ID für den niederländischen Marktplatz Bol.com.'),
            # e-vendo spezifische Identifikationen
            ('evendo_uid', 'e-vendo Produkt-ID', 'Produkt-ID im ERP System e-vendo.')
       ]

        # Importiere die Identifikationen in die AuswahlSchluesselliste
        for code, bezeichnung, beschreibung in artikel_identifikationen:
            obj, created = AuswahlSchluesselliste.objects.get_or_create(
                auswahl_gruppe=gruppe,
                schlüssel=code,
                defaults={
                    'bezeichnung': bezeichnung,
                    'beschreibung': beschreibung
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Importiert: {code} - {bezeichnung}'))
            else:
                self.stdout.write(self.style.WARNING(f'Vorhanden: {code} - {bezeichnung}'))

                # Wenn das Update-Flag gesetzt ist, aktualisiere die Felder `bezeichnung` und `beschreibung`
                if update_existing:
                    obj.bezeichnung = bezeichnung
                    obj.beschreibung = beschreibung
                    obj.save()
                    self.stdout.write(self.style.SUCCESS(f'Aktualisiert: {code} - {bezeichnung}'))

        self.stdout.write(self.style.NOTICE('Abgeschlossen.'))
