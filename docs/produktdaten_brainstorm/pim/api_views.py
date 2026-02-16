# /pim/api_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from pim.models_taxonomie import TaxoSortiment

class SortimentListeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        sortimente = TaxoSortiment.objects.all().order_by("code")
        daten = [
            {
                "id": str(s.id),  # UUID als String
                "code": s.code,
                "name_de": s.name_de,
                "beschreibung_de": s.langtext_de,
            }
            for s in sortimente
        ]
        return Response(daten)