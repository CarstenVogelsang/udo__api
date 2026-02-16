from django.db import models

class PimFieldMixin:
    """
    Ein Mixin, das das `ntg_ref`-Attribut zu jedem Feldtyp hinzufügt.
    """
    def __init__(self, *args, ntg_ref=None, **kwargs):
        self.ntg_ref = ntg_ref
        super().__init__(*args, **kwargs)
    
    def deconstruct(self):
        """
        Deconstruct sorgt dafür, dass das benutzerdefinierte Attribut `ntg_ref` bei der Migration berücksichtigt wird.
        """
        name, path, args, kwargs = super().deconstruct()
        if self.ntg_ref is not None:
            kwargs['ntg_ref'] = self.ntg_ref
        return name, path, args, kwargs

class PimCharField(PimFieldMixin, models.CharField):
    """
    Ein CharField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

class PimIntegerField(PimFieldMixin, models.IntegerField):
    """
    Ein NTGIntegerField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

class PimPositiveIntegerField(PimFieldMixin, models.PositiveIntegerField):
    """
    Ein NTGPositiveIntegerField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

# Du kannst ähnliche Klassen für andere Feldtypen erstellen, z.B.:
class PimDecimalField(PimFieldMixin, models.DecimalField):
    """
    Ein NTGDecimalField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

class PimTextField(PimFieldMixin, models.TextField):
    """
    Ein TextField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

class PimBooleanField(PimFieldMixin, models.BooleanField):
    """
    Ein BooleanField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

class PimDateField(PimFieldMixin, models.DateField):
    """
    Ein DateField mit einem benutzerdefinierten Attribut `ntg_code`.
    """
    pass

class PimURLField(PimFieldMixin, models.URLField):
    """
    Ein URLField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

class PimForeignKey(PimFieldMixin, models.ForeignKey):
    """
    Ein URLField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass

class PimManyToManyField(PimFieldMixin, models.ManyToManyField):
    """
    Ein URLField mit einem benutzerdefinierten Attribut `ntg_ref`.
    """
    pass