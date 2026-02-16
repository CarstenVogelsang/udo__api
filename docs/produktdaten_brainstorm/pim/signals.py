from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from .models import RefMobaBahnverwaltung
from base.models_freigabe import FreigabeAktion, FreigabeStatus

@receiver(post_save, sender=RefMobaBahnverwaltung)
def freigabesaktion_fuer_aenderung_bahnverwaltung(sender, instance, created, **kwargs):
    """
    Erstellt automatisch eine Freigabesaktion, wenn eine Bahnverwaltung geändert wird.
    """
    if not created:  # Nur bei Änderungen an bestehenden Datensätzen
        FreigabeAktion.objects.create(
            inhaltstyp=ContentType.objects.get_for_model(instance),
            objekt_id=str(instance.id),
            freigabe_status=FreigabeStatus.IN_BEARBEITUNG,
            freigabe_am=now(),
            kommentar="Änderung an Bahnverwaltung erkannt. Wartet auf Genehmigung."
        )
