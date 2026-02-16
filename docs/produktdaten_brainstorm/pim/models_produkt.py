# pim/models_produkt.py
from django.db import models
from com.models_unternehmen import Unternehmen
from base.models import DatensatzStatus
from base.models_auswahl import AuswahlSchluesselliste
from base.konstanten import AG_ARTIKELIDENTIFIKATION
from .models_wg import WG_BambergerCode
from .models_mwst import Mehrwertsteuer
from .models_taxonomie import TaxoSortiment, TaxoProduktwelt, TaxoProduktgruppe, TaxoProduktkategorie
from .fields import (
    PimCharField,
    PimIntegerField,
    PimPositiveIntegerField,
    PimDecimalField,
    PimTextField,
    PimBooleanField,
    PimDateField,
    PimURLField,
    PimForeignKey,
    PimManyToManyField,
)
# from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# def default_hersteller():
#     """Stellt sicher, dass es einen Standardhersteller gibt"""
#     hersteller, created = Unternehmen.objects.get_or_create(
#         name="Unbekannter Hersteller"
#     )
#     return hersteller.id  # Rückgabe der ID für das ForeignKey-Feld


class Produkt(DatensatzStatus):
    """
    Repräsentiert Produkte/Artikel im PIM-System.
    Enthält Informationen wie Hersteller, Kategorien und weitere Attribute.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Produktbezeichnung (ersetzt 'name') !!
    #: Truly gourmet cuisine for madam; Lobster Thermidor
    bezeichnung = PimCharField(
        max_length=255,
        help_text="Bezeichnung des Artikels ohne Markenname oder Herstellerartikelnummer",
        ntg_ref="NTG-P-015",
    )

    # hersteller_ist_lieferant benötigt?

    # Verweis auf den Hersteller (jedes Unternehmen kann ein Hersteller sein)
    hersteller = PimForeignKey(
        Unternehmen,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Verknüpfung zum Hersteller des Artikels",
        ntg_ref="NTG-P-003",
    )
    
    # Hauptkategorie eines Produkts
    hauptkategorie = models.ForeignKey(
        TaxoProduktkategorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hauptprodukte",
        verbose_name="Hauptkategorie"
    )
    # Weitere Kategorien eines Produkts
    weitere_kategorien = models.ManyToManyField(
        TaxoProduktkategorie,
        related_name="produkte",
        blank=True,
        verbose_name="Weitere Kategorien"
    )
    # Bamberger Code (aus der Codeliste)
    bamberger_code = PimForeignKey(
        "pim.WG_BambergerCode",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Warengruppe nach Bamberger Code",
        ntg_ref="NTG-P-008",
    )

    # Saisonkennzeichen (gemäß Aufbau NTG Codeliste Saisonkennzeichnungen)
    saison = PimForeignKey(
        AuswahlSchluesselliste,
        on_delete=models.SET_NULL,
        limit_choices_to={"auswahl_gruppe__gruppe": "Saisonkennzeichnung"},
        blank=True,
        null=True,
        verbose_name="Saisonkennzeichen",
        help_text="Saisonkennzeichnung des Artikels",
        ntg_ref="NTG-P-146",
    )

    # Rabattgruppe BuschData - evtl. anders lösen
    rabattgruppe_buschdata = PimCharField(
        max_length=1, 
        blank=True, null=True, 
        verbose_name="Rabattgruppe BuschData",
        help_text="Rabattgruppe für BuschData",
        ntg_ref="NTG-P-314",
    )

    def __str__(self):
        return self.bezeichnung

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkt"


class Produkt_Identifikation(models.Model):
    """
    Speichert Identifikationsschlüssel wie EAN, GTIN, etc.
    -> NTG-P-014: Artikelnummer des Herstellers
    """

    produkt = models.ForeignKey(
        Produkt, on_delete=models.CASCADE, related_name="identifikationen"
    )
    schluessel = models.ForeignKey(
        AuswahlSchluesselliste,
        on_delete=models.CASCADE,
        limit_choices_to={"auswahl_gruppe__gruppe": AG_ARTIKELIDENTIFIKATION},
        verbose_name="Identifikationsschlüssel",
    )
    wert = models.CharField(max_length=255, verbose_name="Schlüsselwert")

    def __str__(self):
        return f"{self.schluessel}: {self.wert}"

    class Meta:
        verbose_name = "Produkt-Identifikation"
        verbose_name_plural = "Produkt-Identifikationen"


class Produkt_Mehrwertsteuer(models.Model):
    """
    Verknüpft Produkte mit Mehrwertsteuersätzen pro Land.
    -> NTG-P-068: Mehrwertsteuersatz
    """

    produkt = models.ForeignKey(Produkt, on_delete=models.CASCADE)
    mehrwertsteuersatz = models.ForeignKey("Mehrwertsteuer", on_delete=models.CASCADE)
    land_hilfsweise = models.CharField(
        max_length=2, help_text="ISO-Code des Landes (z.B. DE für Deutschland)"
    )  # ToDo Verknüpfung zu Model Land, dass noch erstellt werden muss

    def __str__(self):
        return f"{self.produkt} - {self.land}: {self.mehrwertsteuersatz.steuersatz}%"

class Produkt_Lieferant(models.Model):
    """
    Verknüpft Produkte mit Lieferanten und deren Artikelnummern.
    -> NTG-P-001: GLN Lieferant
    -> NTG-P-013: Artikelnummer des Lieferanten
    """

    produkt = models.ForeignKey(
        Produkt, 
        on_delete=models.CASCADE, 
        related_name="lieferanten"
    )
    lieferant = models.ForeignKey(
        Unternehmen, 
        on_delete=models.CASCADE, 
        related_name="lieferungen"
    )
    lieferantartnr = models.CharField(
        max_length=35,
        help_text="Artikelnummer des Lieferanten",
    )

    def __str__(self):
        return f"{self.lieferant} liefert {self.produkt} mit Artikelnummer {self.produkt_lieferant}"
