from django import forms
from unfold.widgets import UnfoldAdminTextInputWidget
from .models_produkteigenschaft_ref import RefMobaBahnverwaltung

class AenderungsBeschreibungWidget(forms.TextInput):
    template_name = 'widgets/aenderungs_beschreibung.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'class': 'border bg-white font-medium min-w-20 rounded-md shadow-sm text-font-default-light text-sm '
                     'focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none '
                     'group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 '
                     'dark:bg-gray-900 dark:border-gray-700 dark:text-font-default-dark dark:focus:border-primary-600 '
                     'dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 '
                     'dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-10 max-w-2xl appearance-none '
                     'relative bg-right bg-no-repeat',
            'list': 'aenderungs_beschreibung_list',
        })

class RefMobaBahnverwaltungForm(forms.ModelForm):
    AENDERUNGS_TYPEN = [
        "Einstellung",
        "Umbenennung",
        "Umfirmierung",
    ]
    
    aenderungs_beschreibung = forms.CharField(
        label="Änderungsbeschreibung",
        widget=AenderungsBeschreibungWidget(attrs={'aenderungs_typen': AENDERUNGS_TYPEN}),
        required=False,
    )
    
    class Meta:
        model = RefMobaBahnverwaltung
        fields = '__all__'


