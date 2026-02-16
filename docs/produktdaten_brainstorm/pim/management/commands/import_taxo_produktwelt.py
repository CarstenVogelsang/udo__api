import os
import openpyxl
from django.core.management.base import BaseCommand
from pim.models_taxonomie import TaxoProduktwelt, TaxoSortiment, TaxoProduktgruppe
from django.conf import settings
from django.db import transaction

# Beispielaufruf: python manage.py import_taxo_produktwelt --family_codes 50200000 50190000 50160000
class Command(BaseCommand):
    help = 'Importiert die TaxoProduktwelt Daten aus der Excel-Datei'

    def add_arguments(self, parser):
        parser.add_argument('--family_codes', nargs='+', type=str, help='Liste der FamilyCodes, die importiert werden sollen')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(self.help))
        self.stdout.write(self.style.NOTICE('Starte...'))

        family_codes = options['family_codes']
        if not family_codes:
            self.stdout.write(self.style.ERROR('Keine FamilyCodes angegeben'))
            return

        # Pfad zur Excel-Datei
        excel_file = os.path.join(settings.IMPORT_DIRECTORY, 'GPC_11_2024_DE.xlsx')
        sheet_name = 'Class_Produktwelt'

        self.stdout.write(self.style.NOTICE(f'Öffne Excel-Datei: {excel_file}'))
        
        try:
            # Excel-Datei lesen
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook[sheet_name]

            headers = [cell.value.strip().lower() if cell.value else '' for cell in sheet[1]]
            self.stdout.write(self.style.SUCCESS(f'Gefundene Spalten: {headers}'))

            with transaction.atomic():
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    row_data = dict(zip(headers, row))
                    
                    family_code = str(row_data.get('familycode', '')).strip()
                    class_prio = str(row_data.get('classprio', '')).strip()
                    class_code = str(row_data.get('classcode', '')).strip()
                    class_title = str(row_data.get('classtitle', '')).strip()

                    if family_code not in family_codes or class_prio != 'A':
                        continue

                    sortiments_code = str(row_data.get('segmentcode', ''))[:2].strip()
                    sortiment = TaxoSortiment.objects.get(code=sortiments_code)

                    produktwelt_code = class_code[4:6]
                    produktwelt = TaxoProduktwelt.objects.get(gpc_classcode=class_code)

                    self.stdout.write(self.style.NOTICE(f'Verarbeite ClassCode: {class_code}, ClassTitle: {class_title}'))

                    obj, created = TaxoProduktgruppe.objects.update_or_create(
                        code=produktwelt_code,
                        produktwelt=produktwelt,
                        defaults={
                            'gpc_classcode': class_code,
                            'gpc_classprio': class_prio,
                            'gpc_classtitel': class_title,
                            'name_de': class_title
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Importiert: {class_code}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Vorhanden und aktualisiert: {class_code}'))

            self.stdout.write(self.style.NOTICE('Abgeschlossen.'))
           
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Fehler beim Import: {e}'))
