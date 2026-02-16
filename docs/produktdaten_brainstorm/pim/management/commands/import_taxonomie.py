import openpyxl
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from pim.models_taxonomie import Taxonomie, TaxoSortiment, TaxoProduktwelt, TaxoProduktgruppe, TaxoProduktkategorie


# Beispielaufruf: python manage.py import_taxonomie FoodCat-1.xlsx FoodCat-1
class Command(BaseCommand):
    help = "Importiert Taxonomie-Daten aus einer Excel-Datei"

    def add_arguments(self, parser):
        parser.add_argument('file_name', type=str, help='Name der Excel-Datei im Import-Verzeichnis')
        parser.add_argument('taxonomie', type=str, help='Name der Taxonomie')

    def handle(self, *args, **kwargs):
        import_dir = getattr(settings, "IMPORT_DIRECTORY", "import")  # Import-Verzeichnis aus den Django-Settings
        file_path = os.path.join(import_dir, kwargs['file_name'])
        taxonomie_name = kwargs['taxonomie']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Datei nicht gefunden: {file_path}'))
            return
        
        self.stdout.write(self.style.NOTICE(f'Importiere Daten aus: {file_path} für Taxonomie: {taxonomie_name}'))
        
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        
        # Taxonomie holen oder erstellen
        taxonomie, _ = Taxonomie.objects.get_or_create(name=taxonomie_name)

        sortiment_cache = {}
        produktwelt_cache = {}
        produktgruppe_cache = {}
        
        headers = [cell.value for cell in sheet[1]]
        rows = sheet.iter_rows(min_row=2, values_only=True)

        for row in rows:
            row_data = dict(zip(headers, row))
            sortiment_code = str(row_data['Sortiment.Code'])
            produktwelt_code = str(row_data['Produktwelt.Code'])
            produktgruppe_code = str(row_data['Produktgruppe.Code'])
            produktkategorie_code = str(row_data['Produktkategorie.Code'])
            
            # Sortiment importieren (nur falls nicht bereits geladen)
            if sortiment_code not in sortiment_cache:
                sortiment, _ = TaxoSortiment.objects.update_or_create(
                    taxonomie=taxonomie,
                    code=sortiment_code,
                    defaults={'name_de': row_data['Sortiment.Name']}
                )
                sortiment_cache[sortiment_code] = sortiment
            else:
                sortiment = sortiment_cache[sortiment_code]
            
            # Produktwelt importieren (nur falls nicht bereits geladen)
            if produktwelt_code not in produktwelt_cache:
                produktwelt, _ = TaxoProduktwelt.objects.update_or_create(
                    sortiment=sortiment,
                    code=produktwelt_code,
                    defaults={'name_de': row_data['Produktwelt.Name']}
                )
                produktwelt_cache[produktwelt_code] = produktwelt
            else:
                produktwelt = produktwelt_cache[produktwelt_code]
            
            # Produktgruppe importieren (nur falls nicht bereits geladen)
            if produktgruppe_code not in produktgruppe_cache:
                produktgruppe, _ = TaxoProduktgruppe.objects.update_or_create(
                    produktwelt=produktwelt,
                    code=produktgruppe_code,
                    defaults={'name_de': row_data['Produktgruppe.Name']}
                )
                produktgruppe_cache[produktgruppe_code] = produktgruppe
            else:
                produktgruppe = produktgruppe_cache[produktgruppe_code]
            
            # Produktkategorie importieren (immer neu prüfen, da das Blatt im Baum)
            produktkategorie, _ = TaxoProduktkategorie.objects.update_or_create(
                produktgruppe=produktgruppe,
                code=produktkategorie_code,
                defaults={'name_de': row_data['Produktkategorie.Name']}
            )
            
        self.stdout.write(self.style.SUCCESS('Daten erfolgreich importiert!'))