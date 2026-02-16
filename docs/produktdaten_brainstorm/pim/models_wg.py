# pim/models_wg.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class WG_BambergerCode(models.Model):
    """
    Verwaltung des Bamberger Codes zur Zuordnung von Artikeln
    zu Warengruppen. Enthält auch Warenklassifikationen der GS1.
    """
    code = models.CharField(
        max_length=5, 
        primary_key=True, 
        help_text="Der Bamberger Code ist ein veraltetes, aber verbreitetes Warenklassifikationssystem",
        verbose_name="Bamberger Code"
    )
    bezeichnung = models.CharField(
        max_length=255, 
        help_text="Bezeichnung der Warengruppe",
        verbose_name="Warengruppe Bezeichnung"
    )
    beschreibung = models.TextField(
        help_text="Beschreibung der Warengruppe",
        verbose_name="Beschreibung"
    )
    warenbereich = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)],
        help_text="Warenbereich (Werte von 1 bis 9)",
        verbose_name="Warenbereich"
    )
    warenbereich_bezeichnung = models.CharField(
        max_length=255, 
        help_text="Bezeichnung des Warenbereichs",
        verbose_name="Warenbereich Bezeichnung"
    )
    gs1_klassifikation = models.CharField(
        blank=True, 
        null=True,
        max_length=255, 
        help_text="Warenklassifikation der GS1 (hilfsweise)",
        verbose_name="GS1 Klassifikation"
    )

    def __str__(self):
        kurze_beschreibung = self.beschreibung[:100]
        if len(self.beschreibung) > 100:
            kurze_beschreibung += "..."
        return f"{self.code}: {kurze_beschreibung}"

    class Meta:
        verbose_name = 'WG Bamberger Vz.'
        verbose_name_plural = 'WG Bamberger Vz.'

