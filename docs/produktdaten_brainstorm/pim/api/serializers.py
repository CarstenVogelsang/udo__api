# pim/api/serializers.py

from rest_framework import serializers
from pim.models_produkt import Produkt

class ProduktSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produkt
        fields = ["id", "bezeichnung", "hersteller", "hauptkategorie"]