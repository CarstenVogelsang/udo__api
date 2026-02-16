#portal/pim/admin.py
import pytz
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django import forms
from django.contrib.contenttypes.admin import GenericTabularInline
from .forms import RefMobaBahnverwaltungForm, AenderungsBeschreibungWidget
from base.models_freigabe import FreigabeAktion
from .models_produkt import Produkt, Produkt_Identifikation  
from .models_wg import WG_BambergerCode
from .models_mwst import Mehrwertsteuer
from .models_produkteigenschaft_ref import RefStandardWert, RefMobaBahnverwaltung, RefMobaNenngroesse
from base.models_bild import Bild
from .models_taxonomie import Taxonomie, TaxoSortiment, TaxoProduktwelt, TaxoProduktgruppe, TaxoProduktkategorie
#from users.models import UserProfile

class WG_BambergerCodeAdminForm(forms.ModelForm):
    warenbereich_bezeichnung = forms.CharField(
        widget=forms.TextInput(attrs={'size': '100'})
    )

    class Meta:
        model = WG_BambergerCode
        fields = '__all__'

# Inline-Klasse für Produkt-Identifikationen
class ProduktIdentifikationInline(TabularInline):
    model = Produkt_Identifikation
    extra = 1  # Eine leere Zeile für neue Einträge
    classes = ["collapse"]  # Unfold-Style für einklappbare Sektionen
    fields = ('schluessel', 'get_bezeichnung', 'get_beschreibung', 'wert')
    readonly_fields = ('get_bezeichnung', 'get_beschreibung')

    def get_bezeichnung(self, obj):
        return obj.schluessel.bezeichnung if obj.schluessel else "-"
    get_bezeichnung.short_description = "Bezeichnung"

    def get_beschreibung(self, obj):
        return obj.schluessel.beschreibung if obj.schluessel else "-"
    get_beschreibung.short_description = "Beschreibung"

# Admin-Konfiguration für Produkte
@admin.register(Produkt)
class ProduktAdmin(ModelAdmin):
    # Definiere die Gruppierung der Felder
    fieldsets = (
        # Allgemeine Informationen (Standard-Feldgruppe, kein Tab)
        (
            None,
            {
                "fields": [
                    "bezeichnung",
                    "hersteller",
                ],
            },
        ),
        # Tab: Hauptkategorie
        (
            _("Hauptkategorie"),
            {
                "classes": ["tab"],
                "fields": [
                    "hauptkategorie",
                ],
            },
        ),
        # Tab: Bamberger Code
        (
            _("Bamberger Code"),
            {
                "classes": ["tab"],
                "fields": [
                    "bamberger_code",
                ],
            },
        ),
        # Tab: Datensatz-Status
        (
            _("Datensatz-Status"),
            {
                "classes": ["tab"],
                "fields": [
                    "aktiv",
                    "erstellt_am",
                    "erstellt_von",
                    "geaendert_am",
                    "geaendert_von",
                    "softgeloescht_am",
                    "softgeloescht_von",
                    "softgeloescht",
                ],
            },
        ),
    )
    
    # Nicht editierbare Felder
    readonly_fields = ('erstellt_am', 'geaendert_am', 'softgeloescht_am', 'erstellt_von', 'geaendert_von', 'softgeloescht_von', 'softgeloescht', 'geaendert_am_usertime')

    inlines = [ProduktIdentifikationInline] 

    # Automatisches Setzen von `erstellt_am` und `erstellt_von`
    def save_model(self, request, obj, form, change):
         # Speichere die Zeit immer in UTC
        current_time = timezone.now()  # Aktuelle Zeit in UTC
        if not change:  # Nur bei der Erstellung eines neuen Datensatzes
            obj.erstellt_am = current_time
            obj.erstellt_von = request.user
            obj.geaendert_am = current_time
            obj.geaendert_von = request.user
        else:
            obj.geaendert_am = current_time
            obj.geaendert_von = request.user
        super().save_model(request, obj, form, change)
    
    list_display = ('bezeichnung', 'hersteller', 'bamberger_code')
    search_fields = ('bezeichnung', 'hersteller__firmierung')
    list_filter = ('bamberger_code',)

# Admin-Konfiguration für WG_BambergerCode
@admin.register(WG_BambergerCode)
class WG_BambergerCodeAdmin(ModelAdmin):
    
    readonly_fields = ()  # Zunächst leer

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Dies ist ein bestehendes Objekt, also machen wir 'code' schreibgeschützt
            return self.readonly_fields + ('code',)
        return self.readonly_fields  # Dies ist ein neues Objekt, also lassen wir 'code' editierbar

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if 'code' in fields:
            fields.remove('code')
        fields.insert(0, 'code')
        return fields
    
    form = WG_BambergerCodeAdminForm
    
    list_display = ('code', 'beschreibung', 'warenbereich')
    search_fields = ('code', 'beschreibung')
    
    admin_group = 'Warengruppen-Admin'

# Admin-Konfiguration für Mehrwertsteuer
@admin.register(Mehrwertsteuer)
class MehrwertsteuerAdmin(ModelAdmin):
    list_display = ('land', 'steuersatz')
    search_fields = ('land',)
    list_filter = ('land',)

# Admin-Konfiguration für RefStandardWert
@admin.register(RefStandardWert)
class RefStandardWertAdmin(ModelAdmin):
    group = 'Produkteigenschaften'
    list_display = ('typ', 'code', 'name_de')
    search_fields = ('typ', 'code', 'name_de')
    list_filter = ('typ',)

# Inline-Klasse für Bilder   
class BildInline(GenericTabularInline):
    model = Bild
    extra = 1
    verbose_name = "Bild"
    verbose_name_plural = "Bilder"
    fields = ["bild"]  # Only include fields that exist in the model
    readonly_fields = ["beschreibung"]  # Use readonly_fields for calculated properties

# class RefMobaBahnverwaltungForm(forms.ModelForm):
#     """
#     Custom Form für RefMobaBahnverwaltung, um `aenderungs_beschreibung` als Combo + Freitext zu ermöglichen
#     """
#     AENDERUNGS_TYPEN = [
#         "Einstellung",
#         "Umbenennung",
#         "Umfirmierung",
#     ]
    
#     aenderungs_beschreibung = forms.CharField(
#         widget=AenderungsBeschreibungWidget(attrs={'aenderungs_typen': AENDERUNGS_TYPEN}),
#         required=False,
#     )
    
#     class Meta:
#         model = RefMobaBahnverwaltung
#         fields = '__all__'

# Inline-Klasse für Freigabeaktionen
class FreigabeAktionInline(GenericTabularInline):
    model = FreigabeAktion
    extra = 0
    readonly_fields = ('freigabe_status', 'freigabe_durch', 'freigabe_am', 'kommentar', 'inhaltstyp', 'objekt_id')
    can_delete = False
    verbose_name_plural = "Freigabeaktionen"
    ct_field = 'inhaltstyp'
    ct_fk_field = 'objekt_id'

    def has_add_permission(self, request, obj=None):
        return False

# Admin-Konfiguration für RefMobaBahnverwaltung
@admin.register(RefMobaBahnverwaltung)
class RefMobaBahnverwaltungAdmin(ModelAdmin):
    group = 'Produkteigenschaften'
    form = RefMobaBahnverwaltungForm
    list_display = ('name_de', 'kuerzel', 'land')
    search_fields = ('name_de', 'kuerzel', 'land')
    list_filter = ('epoche_i', 'epoche_ii', 'epoche_iii', 'epoche_iv', 'epoche_v', 'epoche_vi')
    inlines = [BildInline, FreigabeAktionInline]
    
    fieldsets = (
        (None, {"fields": ["kuerzel", "land", "gruendungsjahr", "aenderungsjahr", "aenderungs_beschreibung"],
                "classes": ["form-group"],}),
        (_("Epochen"), {"fields": ["epoche_i", "epoche_ii", "epoche_iii", "epoche_iv", "epoche_v", "epoche_vi"]}),
        (_("Deutsch"), {"classes": ["tab"], "fields": ["name_de", "alias_de", "text_de", "zusatztext_de"]}),
        (_("Englisch"), {"classes": ["tab"], "fields": ["name_en", "alias_en", "text_en", "zusatztext_en"]}),
        (_("Französisch"), {"classes": ["tab"], "fields": ["name_fr", "alias_fr", "text_fr", "zusatztext_fr"]}),
        (_("Niederländisch"), {"classes": ["tab"], "fields": ["name_nl", "alias_nl", "text_nl", "zusatztext_nl"]}),
        (_("Italienisch"), {"classes": ["tab"], "fields": ["name_it", "alias_it", "text_it", "zusatztext_it"]}),
        (_("Spanisch"), {"classes": ["tab"], "fields": ["name_es", "alias_es", "text_es", "zusatztext_es"]}),
    )
    
    #class Media:
        #js = ('admin/js/aenderungs_beschreibung.js',)  # Falls zusätzliche Anpassungen nötig sind

# Admin-Konfiguration für RefMobaNenngroesse
@admin.register(RefMobaNenngroesse)
class RefMobaNenngroesseAdmin(ModelAdmin):
    group = 'Produkteigenschaften'
    list_display = ('name_de', 'spurweite_mm', 'maßstab')
    search_fields = ('name_de', 'spurweite_mm', 'maßstab')
    list_filter = ('spurweite_mm',)

# Admin-Konfiguration für Taxonomie
@admin.register(Taxonomie)
class TaxonomieAdmin(ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )
    list_filter = ('name',)

# Admin-Konfiguration für TaxoSortiment
@admin.register(TaxoSortiment)
class TaxoSortimentAdmin(ModelAdmin):
    list_display = ('code', 'gpc_segmentcode', 'name_de', 'prioritaet', 'taxonomie')
    list_editable = ('prioritaet', 'taxonomie')
    search_fields = ('code', 'gpc_segmentcode', 'name_de')
    list_filter = ('prioritaet', 'taxonomie')
    readonly_fields = ('id', 'bezeichnung', )

    fieldsets = (
        (None, {
            'fields': ('bezeichnung', 'taxonomie', 'id', 'code', 'prioritaet')
        }),
        (_("Deutsch"), {"classes": ["tab"], "fields": ["name_de", "alias_de", "text_de", "zusatztext_de"]}),
        (_("Englisch"), {"classes": ["tab"], "fields": ["name_en", "alias_en", "text_en", "zusatztext_en"]}),
        (_("Französisch"), {"classes": ["tab"], "fields": ["name_fr", "alias_fr", "text_fr", "zusatztext_fr"]}),
        (_("Niederländisch"), {"classes": ["tab"], "fields": ["name_nl", "alias_nl", "text_nl", "zusatztext_nl"]}),
        (_("Italienisch"), {"classes": ["tab"], "fields": ["name_it", "alias_it", "text_it", "zusatztext_it"]}),
        (_("Spanisch"), {"classes": ["tab"], "fields": ["name_es", "alias_es", "text_es", "zusatztext_es"]}),
        (_("GPC Klassifikation"), {"classes": ["collapsible"], "fields": ["gpc_segmentcode", "gpc_segmenttitel"]}),
    )

    def bezeichnung(self, obj):
        return obj.name_de
    bezeichnung.short_description = "Bezeichnung"

    # def changelist_view(self, request, extra_context=None):
    #     if "prioritaet__exact" not in request.GET:
    #         q = request.GET.copy()
    #         q["prioritaet__exact"] = "A"
    #         request.GET = q
    #         request.META["QUERY_STRING"] = q.urlencode()
    #     return super().changelist_view(request, extra_context=extra_context)

# Admin-Konfiguration für TaxoProduktwelt
@admin.register(TaxoProduktwelt)
class TaxoProduktweltAdmin(ModelAdmin):
    list_display = ('code', 'name_de', 'sortiment', 'breadcrumb')
    search_fields = ('code', 'name_de', 'sortiment__name_de')
    list_filter = ('sortiment',)
    readonly_fields = ('id', 'bezeichnung', 'breadcrumb',)

    def breadcrumb(self, obj):
        return obj.breadcrumb
    breadcrumb.short_description = "Breadcrumb"
    
    def bezeichnung(self, obj):
        return obj.name_de
    bezeichnung.short_description = "Bezeichnung"

    # Add breadcrumb to the top of the form
    fieldsets = (
        (None, {
            'fields': ('breadcrumb', 'bezeichnung', 'id', 'code', 'sortiment')
        }),
        (_("Deutsch"), {"classes": ["tab"], "fields": ["name_de", "alias_de", "text_de", "zusatztext_de"]}),
        (_("Englisch"), {"classes": ["tab"], "fields": ["name_en", "alias_en", "text_en", "zusatztext_en"]}),
        (_("Französisch"), {"classes": ["tab"], "fields": ["name_fr", "alias_fr", "text_fr", "zusatztext_fr"]}),
        (_("Niederländisch"), {"classes": ["tab"], "fields": ["name_nl", "alias_nl", "text_nl", "zusatztext_nl"]}),
        (_("Italienisch"), {"classes": ["tab"], "fields": ["name_it", "alias_it", "text_it", "zusatztext_it"]}),
        (_("Spanisch"), {"classes": ["tab"], "fields": ["name_es", "alias_es", "text_es", "zusatztext_es"]}),
        (_("GPC Klassifikation"), {"classes": ["collapsible"], "fields": ["gpc_classcode", "gpc_classprio", "gpc_classtitel"]}),
    )

# Admin-Konfiguration für TaxoProduktgruppe
@admin.register(TaxoProduktgruppe)
class TaxoProduktgruppeAdmin(ModelAdmin):
    list_display = ('code', 'name_de', 'produktwelt')
    search_fields = ('code', 'name_de', 'produktwelt__name_de')
    list_filter = ('produktwelt',)
    readonly_fields = ('id', 'bezeichnung', 'breadcrumb',)
    
    def breadcrumb(self, obj):
        return obj.breadcrumb
    breadcrumb.short_description = "Breadcrumb"
    
    def bezeichnung(self, obj):
        return obj.name_de
    bezeichnung.short_description = "Bezeichnung"

    fieldsets = (
        (None, {
            'fields': ('breadcrumb', 'bezeichnung', 'id',  'code', 'produktwelt')
        }),
        (_("Deutsch"), {"classes": ["tab"], "fields": ["name_de", "alias_de", "text_de", "zusatztext_de"]}),
        (_("Englisch"), {"classes": ["tab"], "fields": ["name_en", "alias_en", "text_en", "zusatztext_en"]}),
        (_("Französisch"), {"classes": ["tab"], "fields": ["name_fr", "alias_fr", "text_fr", "zusatztext_fr"]}),
        (_("Niederländisch"), {"classes": ["tab"], "fields": ["name_nl", "alias_nl", "text_nl", "zusatztext_nl"]}),
        (_("Italienisch"), {"classes": ["tab"], "fields": ["name_it", "alias_it", "text_it", "zusatztext_it"]}),
        (_("Spanisch"), {"classes": ["tab"], "fields": ["name_es", "alias_es", "text_es", "zusatztext_es"]}),
        (_("GPC Klassifikation"), {"classes": ["collapsible"], "fields": ["gpc_classcode", "gpc_classprio", "gpc_classtitel", "gpc_brickcode", "gpc_brickprio", "gpc_bricktitel"]}),
    )
    

# Admin-Konfiguration für TaxoProduktkategorie
@admin.register(TaxoProduktkategorie)
class TaxoProduktkategorieAdmin(ModelAdmin):
    list_display = ('code', 'name_de', 'produktgruppe')
    search_fields = ('code', 'name_de', 'produktgruppe__name_de')
    list_filter = ('produktgruppe',)
    readonly_fields = ('id', 'bezeichnung', 'breadcrumb',)
        
    def breadcrumb(self, obj):
        return obj.breadcrumb
    breadcrumb.short_description = "Breadcrumb"
    
    def bezeichnung(self, obj):
        return obj.name_de
    bezeichnung.short_description = "Bezeichnung"

    fieldsets = (
        (None, {
            'fields': ('breadcrumb', 'bezeichnung', 'id',  'code', 'produktgruppe')
        }),
        (_("Deutsch"), {"classes": ["tab"], "fields": ["name_de", "alias_de", "text_de", "zusatztext_de"]}),
        (_("Englisch"), {"classes": ["tab"], "fields": ["name_en", "alias_en", "text_en", "zusatztext_en"]}),
        (_("Französisch"), {"classes": ["tab"], "fields": ["name_fr", "alias_fr", "text_fr", "zusatztext_fr"]}),
        (_("Niederländisch"), {"classes": ["tab"], "fields": ["name_nl", "alias_nl", "text_nl", "zusatztext_nl"]}),
        (_("Italienisch"), {"classes": ["tab"], "fields": ["name_it", "alias_it", "text_it", "zusatztext_it"]}),
        (_("Spanisch"), {"classes": ["tab"], "fields": ["name_es", "alias_es", "text_es", "zusatztext_es"]}),
        (_("GPC Klassifikation"), {"classes": ["collapsible"], "fields": ["gpc_brickcode", "gpc_brickprio", "gpc_bricktitel"]}),
    )


