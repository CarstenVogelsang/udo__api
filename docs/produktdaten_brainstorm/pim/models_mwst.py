from django.db import models

class Mehrwertsteuer(models.Model):
    """
    Verwaltung der Mehrwertsteuersätze, abhängig vom Verkaufsland.
    """
    land = models.CharField(
        max_length=2, 
        help_text="ISO-Code des Landes (z.B. DE für Deutschland)"
    )
    steuersatz = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="Mehrwertsteuersatz in Prozent"
    )

    def __str__(self):
        return f"{self.land}: {self.steuersatz}%"

    class Meta:
        verbose_name = 'MwSt'
        verbose_name_plural = 'MwSt'