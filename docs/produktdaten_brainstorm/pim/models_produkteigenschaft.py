import uuid
from django.db import models
from base.models_mehrsprachig import MehrsprachigeBezeichnung    
from .models_taxonomie import TaxoProduktkategorie
from .models_produkteigenschaft_ref import RefStandardWert, RefMobaBahnverwaltung, RefMobaNenngroesse
from .models_produkt import Produkt

class Produkteigenschaft(MehrsprachigeBezeichnung):
    """
    Meta-Definition eines Produktattributs.
    Erbt von MehrsprachigeBezeichnung.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID als PK
    code = models.CharField(max_length=50, unique=True, verbose_name="Eigenschaftscode")
    ist_pflicht = models.BooleanField(default=False, verbose_name="Pflichtfeld")
    mehrfach_erlaubt = models.BooleanField(default=False, verbose_name="Mehrfachwerte erlaubt")
    filterbar = models.BooleanField(default=False, verbose_name="Filterbar")
    anzeige_reihenfolge = models.PositiveIntegerField(default=0, verbose_name="Anzeige-Reihenfolge")

    DATENTYP_CHOICES = [
        ("TEXT", "Freitext"),
        ("INT", "Ganze Zahl"),
        ("DECIMAL", "Dezimalzahl"),
        ("BOOL", "Ja/Nein"),
        ("DATUM", "Datum"),
        ("STANDARD_REF", "Verweis (Standard)"),
        ("BAHNVERWALTUNG_REF", "Verweis (Bahnverwaltung)"),
        ("NENNGR_REF", "Verweis (Nenngröße)"),
    ]
    daten_typ = models.CharField(max_length=30, choices=DATENTYP_CHOICES, verbose_name="Datentyp")

    def __str__(self):
        return f"{self.code} - {self.name_de}"


class ProduktEigenschaftswert(models.Model):
    """
    Verknüpft ein Produkt mit einem konkreten Wert für eine Produkteigenschaft.
    Je nach Datentyp wird der Wert in das entsprechende Feld geschrieben.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID als PK
    produkt = models.ForeignKey(
        Produkt,
        on_delete=models.CASCADE,
        related_name="eigenschaftswerte",
        verbose_name="Produkt"
    )
    produkteigenschaft = models.ForeignKey(
        Produkteigenschaft,
        on_delete=models.CASCADE,
        related_name="produktwerte",
        verbose_name="Produkteigenschaft"
    )
    freitext_wert = models.CharField(max_length=255, null=True, blank=True, verbose_name="Freitextwert")
    ganzzahl_wert = models.IntegerField(null=True, blank=True, verbose_name="Ganzzahlwert")
    dezimal_wert = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=4, verbose_name="Dezimalwert")
    bool_wert = models.BooleanField(null=True, blank=True, verbose_name="Boolescher Wert")
    datum_wert = models.DateField(null=True, blank=True, verbose_name="Datumswert")
    # Verweis auf Referenztabelle
    standard_ref_wert = models.ForeignKey(
        RefStandardWert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Standard-Referenzwert"
    )
    # Verweis auf spezielle Referenztabelle MobaBahnverwaltung
    bahnverw_ref_wert = models.ForeignKey(
        RefMobaBahnverwaltung,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Bahnverwaltung-Referenzwert"
    )
    # Verweis auf spezielle Referenztabelle MobaNenngroesse
    nenngroesse_ref_wert = models.ForeignKey(
        RefMobaNenngroesse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Nenngröße-Referenzwert"
    )

    def __str__(self):
        return f"{self.produkt} - {self.produkteigenschaft}"

    def get_wert_als_string(self):
        dt = self.produkteigenschaft.daten_typ
        if dt == "TEXT":
            return self.freitext_wert
        elif dt == "INT":
            return str(self.ganzzahl_wert) if self.ganzzahl_wert is not None else ""
        elif dt == "DECIMAL":
            return str(self.dezimal_wert) if self.dezimal_wert is not None else ""
        elif dt == "BOOL":
            return "Ja" if self.bool_wert else "Nein"
        elif dt == "DATUM":
            return self.datum_wert.isoformat() if self.datum_wert else ""
        elif dt == "STANDARD_REF":
            return self.standard_ref_wert.name_de if self.standard_ref_wert else ""
        elif dt == "BAHNVERWALTUNG_REF":
            return self.bahnverw_ref_wert.name_de if self.bahnverw_ref_wert else ""
        elif dt == "NENNGR_REF":
            return self.nenngroesse_ref_wert.name_de if self.nenngroesse_ref_wert else ""
        return ""

class ProdukteigenschaftValidierungsregel(models.Model):
    """
    Speichert Validierungsregeln für Produkteigenschaften.
    Ein Sachbearbeiter kann hier über ein Interface Regeln (z.B. als Ausdruck oder JSON) hinterlegen.
    Validierungsregel: Regeln, die über eine Oberfläche definiert und zur Laufzeit ausgewertet werden.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID als PK
    produkteigenschaft = models.ForeignKey(
        Produkteigenschaft,
        on_delete=models.CASCADE,
        related_name="validierungsregeln",
        verbose_name="Produkteigenschaft"
    )
    regel = models.TextField(verbose_name="Regel (als Ausdruck oder JSON)")
    fehlermeldung = models.CharField(max_length=255, verbose_name="Fehlermeldung")
    aktiv = models.BooleanField(default=True, verbose_name="Regel aktiv")

    def __str__(self):
        return f"{self.produkteigenschaft.name_de} - Regel"

# ------------------------------------------------------------------------------
# Verknüpfung von Produkteigenschaften mit Produktkategorien
# (Ermöglicht das Überschreiben von Pflichtflag und Sortierreihenfolge auf Kategorieebene.)
# ------------------------------------------------------------------------------
class ProduktkategorieProdukteigenschaft(models.Model):
    """
    Verknüpft eine Produkteigenschaft mit einer Produktkategorie.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID als PK
    kategorie = models.ForeignKey(
        TaxoProduktkategorie,
        on_delete=models.CASCADE,
        related_name="produkteigenschaften",
        verbose_name="Produktkategorie"
    )
    produkteigenschaft = models.ForeignKey(
        Produkteigenschaft,
        on_delete=models.CASCADE,
        related_name="kategorien",
        verbose_name="Produkteigenschaft"
    )
    anzeige_reihenfolge = models.PositiveIntegerField(null=True, blank=True, verbose_name="Anzeige-Reihenfolge (Override)")
    ist_pflicht = models.BooleanField(null=True, blank=True, verbose_name="Pflicht (Override)")

    class Meta:
        unique_together = ("kategorie", "produkteigenschaft")

    def __str__(self):
        return f"{self.kategorie} - {self.produkteigenschaft}"
