from django.db import models

from django.db import models

class Kategorie(models.Model):
    """
    Selbstreferenzierende Tabelle zur Abbildung einer flexiblen hierarchischen Kategoriestruktur.
    Diese ersetzt die festen Ebenen (Sortiment, Produktwelt, Produktgruppe, Produktkategorie),
    erlaubt aber dennoch direkten Zugriff auf jede Ebene über Properties.
    
    Ebenenbeschreibung:
    - Ebene 1 (Sortiment): Höchste Kategorieebene, die das gesamte Sortiment beschreibt, z. B. "Hobby", "Spielwaren" etc.
    - Ebene 2 (Produktwelt): Unterteilung des Sortiments in thematische Welten, z. B. zur Kategorie "Hobby" die Produktwelten "Modelleisenbahn", "Modellbau" etc.
    - Ebene 3 (Produktgruppe): Weitere Differenzierung innerhalb der Produktwelt, z. B. zur Produktwelte "Modelleisenbahn" die Produktgruppen "Fahrzeuge", "Gleise", "Landschaft" etc.
    - Ebene 4 (Produktkategorie): Feinste Unterkategorie innerhalb einer Produktgruppe, z. B. in der Produktgruppe "Fahrzeuge" die Produktkategorien "Lokomotiven" oder "Wagen", "Packungen", "Gleismaterial", "Zubehör" etc.
    
    """
    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    ebene = models.IntegerField()  # Gibt an, auf welcher Hierarchieebene die Kategorie liegt (1=Sortiment, 2=Produktwelt etc.)

    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"

    def __str__(self):
        return self.breadcrumb  # Gibt den gesamten Pfad der Kategorie zurück

    @property
    def sortiment_E1(self):
        """Gibt das Sortiment zurück (Ebene 1)"""
        if self.ebene == 1:
            return self
        elif self.parent:
            return self.parent.sortiment_E1
        return None

    @property
    def produktwelt_E2(self):
        """Gibt die Produktwelt zurück (Ebene 2)"""
        if self.ebene == 2:
            return self
        elif self.parent:
            return self.parent.produktwelt_E2
        return None

    @property
    def produktgruppe_E3(self):
        """Gibt die Produktgruppe zurück (Ebene 3)"""
        if self.ebene == 3:
            return self
        elif self.parent:
            return self.parent.produktgruppe_E3
        return None

    @property
    def produktkategorie_E4(self):
        """Gibt die Produktkategorie zurück (Ebene 4)"""
        if self.ebene == 4:
            return self
        elif self.parent:
            return self.parent.produktkategorie_E4
        return None

    @property
    def breadcrumb(self):
        """
        Gibt die gesamte Hierarchie als String zurück,
        wobei jeder Eintrag mit seiner Ebene bezeichnet wird.
        Beispiel: "Sortiment: Modellbau > Produktwelt: Modelleisenbahn > Produktgruppe: Fahrzeuge & Technik > Produktkategorie: Lokomotiven"
        """
        ebene_mapping = {
            1: "Sortiment",
            2: "Produktwelt",
            3: "Produktgruppe",
            4: "Produktkategorie"
        }
        prefix = ebene_mapping.get(self.ebene, "Kategorie")
        if self.parent:
            return f"{self.parent.breadcrumb} > {prefix}: {self.name}"
        return f"{prefix}: {self.name}"


