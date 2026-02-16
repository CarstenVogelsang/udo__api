#portal/pim/models_taxonomie.py
# ------------------------------------------------------------------------------
from django.db import models
from base.models import DatensatzStatus 
from base.models_mehrsprachig import MehrsprachigeBezeichnung, MehrsprachigerSlogan, MehrsprachigeBezeichnungAlias, MehrsprachigerText, MehrsprachigerZusatztext
import uuid

class Taxonomie(DatensatzStatus):
    """
    Gruppierung für eine bestimmte Klassifikation von Produkten.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID als PK
    name = models.CharField(max_length=20, blank=True, null=True, verbose_name="Taxonomie-Bezeichnung")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Taxonomie"
        verbose_name_plural = "Taxonomien"

class TaxoSortiment(MehrsprachigeBezeichnung, MehrsprachigeBezeichnungAlias, MehrsprachigerText, MehrsprachigerZusatztext):
    """
    Repräsentiert ein Sortiment (z.B. Hobby, Spielwaren, Baby, Schule & Büro, Wein & Spirituosen).
    Mit dem Präfix "Taxo" für den klaren Taxonomiebezug.
    Erste Ebene der Taxonomie in einem 4-stufigen Taxonomiekonzept:
    1. Sortiment -> 2. Produktwelt -> 3. Produktgruppe -> 4. Produktkategorie
    """
    PRIORITAET_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(max_length=2, verbose_name="Sortiments-Code")

    taxonomie = models.ForeignKey(
        Taxonomie,
        on_delete=models.CASCADE,
        related_name="sortimente",
        verbose_name="Taxonomie",
        null=True,
        blank=True
    )

    prioritaet = models.CharField(max_length=1, choices=PRIORITAET_CHOICES, verbose_name="Priorität", default='A')
    gpc_segmentcode = models.CharField(max_length=8, blank=True, null=True, verbose_name="GPC Segment-Code", help_text="Ein GPC Segment-Code ist die oberste Ebene der Global Product Classification (GPC) von GS1 und bezeichnet einen spezifischen Industriebereich in Form eines 8-stelligen Codes.",)
    gpc_segmenttitel = models.CharField(max_length=255, blank=True, null=True, verbose_name="GPC Segment-Titel", help_text="Ein GPC Segment-Titel ist die oberste Ebene der Global Product Classification (GPC) von GS1 und bezeichnet einen spezifischen Industriebereich, wie z. B. Lebensmittel&Getränke.",)
    
    @property
    def taxonomie_code(self):
        return self.code

    @property
    def breadcrumb(self):
        return f"{self.name_de}"

    def __str__(self):
        return f"{self.code} - {self.name_de}"

    class Meta:
        verbose_name = "Taxonomie (1) Sortiment"
        verbose_name_plural = "Taxonomien (1) Sortimente"
        

class TaxoProduktwelt(MehrsprachigeBezeichnung, MehrsprachigeBezeichnungAlias, MehrsprachigerText, MehrsprachigerZusatztext):
    """
    Repräsentiert eine Produktwelt (z.B. Modellbahn, Brettspiele).
    Mit dem Präfix "Taxo" für den klaren Taxonomiebezug.
    Zweite Ebene der Taxonomie in einem 4-stufigen Taxonomiekonzept:
    1. Sortiment -> 2. Produktwelt -> 3. Produktgruppe -> 4. Produktkategorie
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        
    code = models.CharField(max_length=2, verbose_name="Produktwelt-Code")
    
    sortiment = models.ForeignKey(
        TaxoSortiment,
        on_delete=models.CASCADE,
        related_name="produktwelten",
        verbose_name="Sortiment"
    )
    gpc_classcode = models.CharField(max_length=8, blank=True, null=True, verbose_name="GPC Class-Code")
    gpc_classprio = models.CharField(max_length=1, blank=True, null=True, verbose_name="GPC Class-Prio")
    gpc_classtitel = models.CharField(max_length=255, blank=True, null=True, verbose_name="GPC Class-Titel")

    @property
    def taxonomie_code(self):
        return f"{self.sortiment.taxonomie_code}{self.code}"

    @property
    def breadcrumb(self):
        return f"{self.sortiment.name_de} > {self.name_de}"

    @property
    def fullcode(self):
        return f"{self.sortiment.code}-{self.code}"

    def __str__(self):
        return f"{self.code} - {self.name_de}"

    class Meta:
        verbose_name = "Taxonomie (2) Produktwelt"
        verbose_name_plural = "Taxonomien (2) Produktwelten"


class TaxoProduktgruppe(MehrsprachigeBezeichnung, MehrsprachigeBezeichnungAlias, MehrsprachigerText, MehrsprachigerZusatztext):
    """
    Repräsentiert eine Produktgruppe innerhalb einer Produktwelt.
    Mit dem Präfix "Taxo" für den klaren Taxonomiebezug.
    Dritte Ebene der Taxonomie in einem 4-stufigen Taxonomiekonzept:
    1. Sortiment -> 2. Produktwelt -> 3. Produktgruppe -> 4. Produktkategorie
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=2,verbose_name="Produktgruppen-Code")
    
    produktwelt = models.ForeignKey(
        TaxoProduktwelt,
        on_delete=models.CASCADE,
        related_name="produktgruppen",
        verbose_name="Produktwelt"
    )
    gpc_classcode = models.CharField(max_length=8, blank=True, null=True, verbose_name="GPC Class-Code")
    gpc_classprio = models.CharField(max_length=1, blank=True, null=True, verbose_name="GPC Class-Prio")
    gpc_classtitel = models.CharField(max_length=255, blank=True, null=True, verbose_name="GPC Class-Titel")
    gpc_brickcode = models.CharField(max_length=8, blank=True, null=True, verbose_name="GPC Brick-Code")
    gpc_brickprio = models.CharField(max_length=1, blank=True, null=True, verbose_name="GPC Brick-Prio")
    gpc_bricktitel = models.CharField(max_length=255, blank=True, null=True, verbose_name="GPC Brick-Titel")

    @property
    def taxonomie_code(self):
        return f"{self.produktwelt.taxonomie_code}{self.code}"

    @property
    def breadcrumb(self):
        return f"{self.produktwelt.breadcrumb} > {self.name_de}"
    
    @property
    def fullcode(self):
        return f"{self.produktwelt.fullcode}-{self.code}"
    
    def __str__(self):
        return f"{self.code} - {self.name_de}"

    class Meta:
        verbose_name = "Taxonomie (3) Produktgruppe"
        verbose_name_plural = "Taxonomien (3) Produktgruppen"

class TaxoProduktkategorie(MehrsprachigeBezeichnung, MehrsprachigeBezeichnungAlias, MehrsprachigerText, MehrsprachigerZusatztext):
    """
    Repräsentiert eine Produktkategorie innerhalb einer Produktgruppe.
    Mit dem Präfix "Taxo" für den klaren Taxonomiebezug.
    Vierte Ebene der Taxonomie in einem 4-stufigen Taxonomiekonzept:
    1. Sortiment -> 2. Produktwelt -> 3. Produktgruppe -> 4. Produktkategorie
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(max_length=2, verbose_name="Produktkategorie-Code")
    
    produktgruppe = models.ForeignKey(
        TaxoProduktgruppe,
        on_delete=models.CASCADE,
        related_name="produktkategorien",
        verbose_name="Produktgruppe"
    )
    gpc_brickcode = models.CharField(max_length=8, blank=True, null=True, verbose_name="GPC Brick-Code")
    gpc_brickprio = models.CharField(max_length=1, blank=True, null=True, verbose_name="GPC Brick-Prio")
    gpc_bricktitel = models.CharField(max_length=255, blank=True, null=True, verbose_name="GPC Brick-Titel")

    @property
    def taxonomie_code(self):
        return f"{self.produktgruppe.taxonomie_code}{self.code}"

    @property
    def breadcrumb(self):
        return f"{self.produktgruppe.breadcrumb} > {self.name_de}"
    
    @property
    def fullcode(self):
        return f"{self.produktgruppe.fullcode}-{self.code}"

    def __str__(self):
        return f"{self.code} - {self.name_de}"

    class Meta:
        verbose_name = "Taxonomie (4) Produktkategorie"
        verbose_name_plural = "Taxonomien (4) Produktkategorien"