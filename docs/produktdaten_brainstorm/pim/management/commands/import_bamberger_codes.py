#portal/pim/management/commands/import_bamberger_codes.py
# ------------------------------------------------------------------------------
from django.core.management.base import BaseCommand
from pim.models_wg import WG_BambergerCode
from django.db import transaction
import openpyxl
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Importiert Bamberger Codes aus einer XLSX-Datei'

    def add_arguments(self, parser):
        parser.add_argument('xlsx_file', type=str, help='Name der XLSX-Datei')
        parser.add_argument('sheet_name', type=str, help='Name des Tabellenblatts')

    def handle(self, *args, **options):
        
        self.stdout.write(self.style.NOTICE(self.help))
                
        xlsx_file_name = options['xlsx_file']
        sheet_name = options['sheet_name']
        xlsx_file_path = os.path.join(settings.IMPORT_DIRECTORY, xlsx_file_name)

        self.stdout.write(self.style.NOTICE(f'Starte Import aus {xlsx_file_path}, Tabellenblatt: {sheet_name}...'))

        try:
            workbook = openpyxl.load_workbook(xlsx_file_path)
            sheet = workbook[sheet_name]

            headers = [cell.value.strip().lower() if cell.value else '' for cell in sheet[1]]
            self.stdout.write(self.style.SUCCESS(f'Gefundene Spalten: {headers}'))

            with transaction.atomic():
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    row_data = dict(zip(headers, row))
                    
                    code = str(row_data.get('code', '')).strip()
                    if not code:
                        continue

                    if not WG_BambergerCode.objects.filter(code=code).exists():
                        WG_BambergerCode.objects.create(
                            code=code,
                            bezeichnung=str(row_data.get('bezeichnung', '')).strip(),
                            beschreibung=str(row_data.get('beschreibung', '')).strip(),
                            warenbereich=int(str(row_data.get('warenbereich', '0')).strip()),
                            warenbereich_bezeichnung=str(row_data.get('warenbereich_bezeichnung', '')).strip(),
                            gs1_klassifikation=str(row_data.get('gs1_klassifikation', '')).strip() or None
                        )
                        self.stdout.write(self.style.SUCCESS(f'Code {code} erfolgreich importiert'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Code {code} existiert bereits'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Fehler beim Import: {e}'))
            
        self.stdout.write(self.style.NOTICE('Abgeschlossen.'))
