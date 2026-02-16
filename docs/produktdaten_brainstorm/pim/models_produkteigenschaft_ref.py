#/pim/models_produkteigenschaft_ref.py
import uuid
from django.db import models
from base.models_mehrsprachig import MehrsprachigeBezeichnung, MehrsprachigerText
from countries_plus.models import Country
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MinValueValidator, MaxValueValidator
from base.models_bild import Bild
from base.models_freigabe import FreigabeAktion


class RefStandardWert(MehrsprachigeBezeichnung):
    """
    Standard-Referenztabelle für einfache Eigenschaften.
    Weitere komplexe Referenztabellen mit dem Präfix "Ref" (z.B. RefBahnverwaltung, RefNenngroesse).
    'typ' unterscheidet verschiedene Listen (z.B. "EPOCHE", etc.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID als PK
    typ = models.CharField(max_length=50, verbose_name="Referenztyp")
    code = models.CharField(max_length=50, verbose_name="Wert-Code")

    def __str__(self):
        return f"{self.typ} - {self.code} - {self.name_de}"
    
    class Meta:
        unique_together = ("typ", "code")
        verbose_name = "Eigenschaft Standard"
        verbose_name_plural = "Eigenschaften Standard"

class RefMobaBahnverwaltung(MehrsprachigeBezeichnung, MehrsprachigerText):
    """
    Spezielle Referenztabelle für Bahnverwaltungen.
    Enthält mehrsprachige Bezeichnungen, Langtexte, sowie Verknüpfungen zu Bildern.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kuerzel = models.CharField(max_length=20, null=True, blank=True, verbose_name="Kürzel")
    land = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Land")
    gruendungsjahr = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Gründungsjahr",
        validators=[MinValueValidator(1750), MaxValueValidator(2050)]
    )
            
    # Epochen als Boolean-Felder
    epoche_i = models.BooleanField(default=False, verbose_name="Epoche I")
    epoche_ii = models.BooleanField(default=False, verbose_name="Epoche II")
    epoche_iii = models.BooleanField(default=False, verbose_name="Epoche III")
    epoche_iv = models.BooleanField(default=False, verbose_name="Epoche IV")
    epoche_v = models.BooleanField(default=False, verbose_name="Epoche V")
    epoche_vi = models.BooleanField(default=False, verbose_name="Epoche VI")
    
    # Historische Änderungen (Einstellung, Umbenennung, Umfirmierung)
    aenderungsjahr = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Änderungsjahr",
        validators=[MinValueValidator(1750), MaxValueValidator(2050)]
    )
    AENDERUNGS_TYPEN = [
        ("Einstellung", "Einstellung"),
        ("Umbenennung", "Umbenennung"),
        ("Umfirmierung", "Umfirmierung"),
    ]
    aenderungs_beschreibung = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Änderungsbeschreibung",
        choices=AENDERUNGS_TYPEN
    )
    
    # Bilder (Logo + Weitere Bilder)
    bilder = GenericRelation(Bild, related_query_name="bahnverwaltungen")

    # Freigabeaktionen für Anlagen und Änderungen
    freigabesaktionen = GenericRelation(
        FreigabeAktion,
        content_type_field='inhaltstyp',
        object_id_field='objekt_id',
        related_query_name="bahnverwaltungen"
    )

    def __str__(self):
        return f"{self.name_de} ({self.kuerzel})"
    
    class Meta:
        verbose_name = "Eigenschaft Moba Bahnverwaltung"
        verbose_name_plural = "Eigenschaften Moba Bahnverwaltungen"
        

class RefMobaNenngroesse(MehrsprachigeBezeichnung):
    """
    Spezielle Referenztabelle für Nenngrößen mit Spurweite, Maßstab und Kommentaren.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID als PK
    spurweite_mm = models.FloatField(verbose_name="Spurweite (mm)")
    maßstab = models.CharField(max_length=20, verbose_name="Maßstab")
    kommentar = models.TextField(null=True, blank=True, verbose_name="Kommentar")

    def __str__(self):
        return f"{self.name_de} ({self.maßstab})"

    class Meta:
        verbose_name = "Eigenschaft Moba Nenngrößen"
        verbose_name_plural = "Eigenschaften Moba Nenngrößen"
