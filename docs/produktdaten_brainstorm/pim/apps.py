from django.apps import AppConfig

class PimConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pim'
    verbose_name = 'e-vendo PIM'  # Admin-Anzeige

    def ready(self):
        import pim.signals  # Signal importieren