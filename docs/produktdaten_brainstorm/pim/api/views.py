from rest_framework import viewsets
from pim.models_produkt import Produkt
from .serializers import ProduktSerializer

class ProduktViewSet(viewsets.ModelViewSet):
    queryset = Produkt.objects.all()
    serializer_class = ProduktSerializer
    # Optional: permission_classes = [AllowAny] für MVP ohne Auth
