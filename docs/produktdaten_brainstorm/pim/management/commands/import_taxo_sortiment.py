import os
import openpyxl
from django.core.management.base import BaseCommand
from pim.models_taxonomie import TaxoSortiment
from django.conf import settings
from django.db import transaction

# Beispielaufruf: python manage.py import_taxo_sortiment
class Command(BaseCommand):
    help = 'Importiert die TaxoSortiment Daten aus der Excel-Datei'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE(self.help))
        self.stdout.write(self.style.NOTICE('Starte...'))

        # Pfad zur Excel-Datei
        excel_file = os.path.join(settings.IMPORT_DIRECTORY, 'GPC_11_2024_DE.xlsx')
        sheet_name = 'Segment_Sortiment'

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
                    
                    sortiments_code = str(row_data.get('segmentcode', ''))[:2].strip()
                    segment_code = str(row_data.get('segmentcode', '')).strip()
                    segment_title = str(row_data.get('segmenttitle', '')).strip()

                    if not sortiments_code:
                        continue

                    self.stdout.write(self.style.NOTICE(f'Verarbeite SegmentCode: {segment_code}, SegmentTitle: {segment_title}'))

                    obj, created = TaxoSortiment.objects.update_or_create(
                        code=sortiments_code,
                        defaults={
                            'gpc_segmentcode': segment_code,
                            'gpc_segmenttitel': segment_title,
                            'name_de': segment_title
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Importiert: {segment_code}'))
                    else:
                        if not obj.name_de:
                            obj.name_de = segment_title
                            obj.save()
                        self.stdout.write(self.style.WARNING(f'Vorhanden und aktualisiert: {segment_code}'))

            self.stdout.write(self.style.NOTICE('Abgeschlossen.'))
           
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Fehler beim Import: {e}'))



