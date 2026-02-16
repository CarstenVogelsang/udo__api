import sqlite3
from django.core.management.base import BaseCommand
from pim.models_taxonomie import TaxoSortiment, TaxoProduktgruppe, TaxoProduktwelt, TaxoProduktkategorie
from django.db import transaction

class Command(BaseCommand):
    help = "Kopiert Taxonomie-Daten aus einer Backup-Datenbank in die aktuelle Django-Datenbank"

    def handle(self, *args, **kwargs):
        backup_db = "backup_portal.db"  # Name der Backup-Datenbank
        self.stdout.write(self.style.NOTICE(f"Öffne Backup-Datenbank: {backup_db}"))

        try:
            conn = sqlite3.connect(backup_db)
            cursor = conn.cursor()

            with transaction.atomic():  # Alle Einfügungen in einer Transaktion
                # 1️⃣ TaxoSortiment kopieren
                
                self.copy_table(cursor, TaxoSortiment, "pim_taxosortiment", ["name_de", "name_en", "name_fr", "name_nl", "name_it", "name_es", "code", "gpc_segmentcode", "gpc_segmenttitel", "prioritaet", "langtext_de", "langtext_en", "langtext_es", "langtext_fr","langtext_it", "langtext_nl"])

                # 2️⃣ TaxoProduktwelt kopieren
                self.copy_table(cursor, TaxoProduktwelt, "pim_taxoproduktwelt", ["name_de", "name_en", "name_fr", "name_nl", "name_it", "name_es", "code", "sortiment_id", "gpc_classcode", "gpc_classprio", "gpc_classtitel", "langtext_de", "langtext_en", "langtext_es", "langtext_fr", "langtext_it", "langtext_nl"]) 

                # 3️⃣ TaxoProduktgruppe kopieren
                self.copy_table(cursor, TaxoProduktgruppe, "pim_taxoproduktgruppe", ["name_de", "name_en", "name_fr", "name_nl", "name_it", "name_es", "code", "produktwelt_id", "gpc_brickcode", "gpc_brickprio", "gpc_bricktitel", "gpc_classcode", "gpc_classprio", "gpc_classtitel", "langtext_de", "langtext_en", "langtext_es", "langtext_fr", "langtext_it", "langtext_nl"])

                # 4️⃣ TaxoProduktkategorie kopieren
                self.copy_table(cursor, TaxoProduktkategorie, "pim_taxoproduktkategorie", ["name_de", "name_en", "name_fr", "name_nl", "name_it", "name_es", "code", "produktgruppe_id", "gpc_brickcode", "gpc_brickprio", "gpc_bricktitel", "langtext_de", "langtext_en", "langtext_es", "langtext_fr", "langtext_it", "langtext_nl"])

            conn.close()
            self.stdout.write(self.style.SUCCESS("✅ Taxonomie erfolgreich kopiert!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Fehler beim Kopieren der Taxonomie: {e}"))

    def copy_table(self, cursor, model, table_name, columns):
        """Kopiert Daten aus einer Tabelle in das Django-Modell."""
        self.stdout.write(self.style.NOTICE(f"Kopiere {table_name}..."))

        # SQL-Abfrage vorbereiten
        existing_columns = [col for col in columns if col != "id"]  # Entferne "id"
        sql = f"SELECT {', '.join(existing_columns)} FROM {table_name}"
        cursor.execute(sql)

        # Daten holen und in Django-Model speichern
        rows = cursor.fetchall()
        instances = [model(**dict(zip(columns, row))) for row in rows]

        if instances:
            model.objects.bulk_create(instances, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f"✅ {len(instances)} Einträge in {table_name} kopiert."))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ Keine Daten in {table_name} gefunden."))
